"""Live-session durability: translator hydration, the write path, boot recovery.

All hermetic — the autouse guard blanks the DSN, so durable's write helpers no-op
unless a test monkeypatches its seams (recorders for writes; a FakeDurableGraph for
the checkpoint's aget_state/astream). The real-Postgres path is exercised by the
manual restart smoke, not here.
"""
from __future__ import annotations

import asyncio
from types import SimpleNamespace

from langgraph.types import Command

from server.game.live_game_registry import LiveGameRegistry
from server.housekeeping import recovery
from server.database_models.game import DROPPED, RUNNING, WAITING, GameRow
from server.storage.game_repository import derive_completion_metadata
from server.game.translate import Translator
from tests.factories.builders import human_turn_request
from tests.fixtures.server import FakeGraph

# ---- translator hydration ------------------------------------------------------------------


def test_hydrate_rebuilds_the_shadow_from_the_log(fixture_parts):
    """Round-trip: state rebuilt from EVENTS must match state built from PARTS —
    same roles, same continued seq, and (the load-bearing one) the same ship-once
    guards, or a post-restart resume would re-ship every delivered message."""
    lived = Translator()
    log = [e for p in fixture_parts for e in lived.translate(p)]

    revived = Translator()
    revived.hydrate(log)

    assert revived.roles == lived.roles
    assert revived.wolves == lived.wolves
    assert revived.seq == lived.seq  # next event continues, never collides
    assert revived._seen_day_entries == lived._seen_day_entries
    assert revived._seen_wolf_msgs == lived._seen_wolf_msgs
    assert revived._strategies == lived._strategies
    # Provisional buffers deliberately stay empty: the resume re-run repopulates them.
    assert revived._day_ballots == {} and revived._wolf_votes == {}


# ---- the write path (runtime -> durable) -----------------------------------------------------


async def test_run_persists_events_and_finalizes_one_game_row(quiet_session, fixture_parts):
    repository = RecordingGameRepository()

    session = quiet_session(FakeGraph(fixture_parts), repository=repository)
    session.start()
    await asyncio.wait_for(session.wait_finished(), timeout=30)

    assert [e.seq for e in repository.events] == [e.seq for e in session.log]
    assert repository.completions == [(session.game_id, len(session.log), 0)]
    # The fixture game is all-LLM: human_players never changes, so no seat upsert.
    assert all("human_players" not in fields for fields in repository.upserts)


async def test_death_marks_the_row_dead_and_cancellation_does_not(quiet_session):
    repository = RecordingGameRepository()

    class ExplodingGraph:
        async def astream(self, payload, **_):
            raise RuntimeError("provider died")
            yield  # pragma: no cover

    session = quiet_session(ExplodingGraph(), repository=repository)
    session.start()
    await asyncio.wait_for(session.wait_finished(), timeout=10)
    assert repository.upserts[-1]["status"] == DROPPED
    assert "provider died" in repository.upserts[-1]["error"]
    assert repository.completions == []

    # Shutdown cancellation must leave the durable status untouched ('running'), so
    # the next boot recovers the game instead of burying it.
    from tests.fixtures.server import HangingGraph

    repository.upserts.clear()
    parked = quiet_session(HangingGraph(), repository=repository)
    parked.start()
    await asyncio.sleep(0.05)
    await parked.shutdown()
    assert all("status" not in fields for fields in repository.upserts)


# ---- boot recovery ---------------------------------------------------------------------------


class FakeDurableGraph:
    """aget_state serves a canned checkpoint view; astream records the resume."""

    def __init__(self, state):
        self._state = state
        self.calls = []

    async def aget_state(self, config):
        return self._state

    async def astream(self, payload, *, config, context, stream_mode, subgraphs, version):
        self.calls.append(payload)
        return
        yield  # pragma: no cover


class RecordingGameRepository:
    """The runtime's narrow persistence contract, with no database or globals."""

    def __init__(self, rows=()) -> None:
        self.rows = list(rows)
        self.events = []
        self.completions = []
        self.upserts = []
        self.upsert_calls = []

    async def record_events(self, game_id, events):
        self.events.extend(events)

    async def upsert_game(self, game_id, **fields):
        self.upserts.append(fields)
        self.upsert_calls.append((game_id, fields))

    async def complete_game(self, game_id, log, n_humans):
        self.completions.append((game_id, len(log), n_humans))

    async def load_recoverable_games(self):
        return self.rows

    async def load_events(self, game_id):
        return []


def _row(**over):
    base = dict(game_id="g-1", status=RUNNING, host_key="", model="", byok=False,
                seats=[{"name": "hao", "token": "tok-1"}], human_players=["player_3"])
    base.update(over)
    return GameRow(**base)


async def _recover(monkeypatch, rows, graph):
    monkeypatch.setattr("server.game.game_session.seed_memory_from_config", lambda *a, **k: None)
    repository = RecordingGameRepository(rows=rows)
    games = LiveGameRegistry(repository, SimpleNamespace(graph=graph))
    await recovery.recover_registry(games, repository)
    return games, repository


async def test_a_waiting_row_is_never_rebuilt(monkeypatch):
    # Rooms live in memory only (ruled 2026-09-12): a restart closes them. A waiting row
    # can only predate that ruling; it is left alone, neither revived nor rewritten.
    row = _row(status=WAITING, host_key="hk-9", room_name="wolves den")
    games, repository = await _recover(monkeypatch, [row], FakeDurableGraph(None))
    assert games.get("g-1") is None and len(games) == 0
    assert repository.upsert_calls == []


async def test_parked_game_revives_reparked_and_resumes_on_the_answer(monkeypatch):
    request = human_turn_request(player_id="player_3", phase="day_channel",
                                 can_pass=True, valid_targets=[])
    state = SimpleNamespace(next=("DAY_PHASE",), tasks=[SimpleNamespace(
        interrupts=[SimpleNamespace(value=request.model_dump(), id="int-9")])])
    graph = FakeDurableGraph(state)

    from datetime import datetime, timezone
    stamp = datetime(2026, 8, 24, 3, 32, tzinfo=timezone.utc)
    games, _ = await _recover(monkeypatch, [_row(updated_at=stamp)], graph)
    session = games.get("g-1")
    assert sorted(session.pending_requests) == ["player_3"]  # the returning-player view
    assert session.parked_since == stamp  # the retention clock survives the restart
    assert session.seat_for_token("tok-1") == "player_3"

    session.submit_turn({"message": "back from the dead"}, seat="player_3")
    await asyncio.wait_for(session.wait_finished(), timeout=10)
    resume = graph.calls[0]
    assert isinstance(resume, Command) and resume.resume["message"] == "back from the dead"


async def test_byok_game_is_dropped_with_a_clear_epitaph_and_not_kept(monkeypatch):
    from server.game.live_game_registry import _BYOK_EPITAPH

    games, repository = await _recover(monkeypatch, [_row(byok=True)],
                                       FakeDurableGraph(None))
    # Nothing can play it (the key was never stored), so it is not a live game: the row,
    # marked dropped with the reason, is what answers for it from now on.
    assert games.get("g-1") is None
    assert ("g-1", {"status": DROPPED, "error": _BYOK_EPITAPH}) in repository.upsert_calls


async def test_house_selected_model_survives_restart(monkeypatch):
    model = "gemini-3.6-flash"
    state = SimpleNamespace(next=("resume",), tasks=[])
    games, _ = await _recover(
        monkeypatch, [_row(model=model, byok=False)], FakeDurableGraph(state))

    assert games.get("g-1")._llm_override.model == model


async def test_stale_running_row_of_a_finished_game_is_closed_and_not_kept(monkeypatch):
    state = SimpleNamespace(next=(), tasks=[])
    games, repository = await _recover(monkeypatch, [_row()], FakeDurableGraph(state))
    assert games.get("g-1") is None  # completed games live in the archive, not the table
    assert repository.completions == [("g-1", 0, 1)]


def test_completion_metadata_is_lifted_from_the_event_log():
    from server.schemas import events as ev

    log = [
        ev.GameStarted(seq=1, day=1, seats=["p1", "p2"],
                       cast_role_counts={"wolf": 1, "villager": 1}),
        ev.GmMessage(seq=2, day=2, channel_seq=0, text="dawn"),
        ev.GameOver(seq=3, day=3, winner="wolves"),
    ]
    assert derive_completion_metadata(log) == {
        "winner": "wolves",
        "days": 3,
        "n_events": 3,
        "cast_role_counts": {"wolf": 1, "villager": 1},
    }
    assert derive_completion_metadata(log[:-1]) is None
