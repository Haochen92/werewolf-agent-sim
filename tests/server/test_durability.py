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

from server import durable, recovery
from server.translate import Translator
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


async def test_run_persists_events_and_final_phase(quiet_session, monkeypatch,
                                                   fixture_parts):
    recorded, upserts = [], []

    async def rec_events(game_id, events):
        recorded.extend(events)

    async def rec_upsert(game_id, **fields):
        upserts.append(fields)

    monkeypatch.setattr(durable, "record_events", rec_events)
    monkeypatch.setattr(durable, "upsert_session", rec_upsert)

    session = quiet_session(FakeGraph(fixture_parts))
    session.start()
    await asyncio.wait_for(session.wait_finished(), timeout=30)

    assert [e.seq for e in recorded] == [e.seq for e in session.log]  # full log, in order
    assert upserts[-1] == {"phase": "finished"}
    # The fixture game is all-LLM: human_players never changes, so no seat upsert.
    assert all("human_players" not in u for u in upserts)


async def test_death_marks_the_row_dead_and_cancellation_does_not(quiet_session,
                                                                  monkeypatch):
    upserts = []

    async def rec_upsert(game_id, **fields):
        upserts.append(fields)

    monkeypatch.setattr(durable, "upsert_session", rec_upsert)

    class ExplodingGraph:
        async def astream(self, payload, **_):
            raise RuntimeError("provider died")
            yield  # pragma: no cover

    session = quiet_session(ExplodingGraph())
    session.start()
    await asyncio.wait_for(session.wait_finished(), timeout=10)
    assert upserts[-1]["phase"] == "dead" and "provider died" in upserts[-1]["error"]

    # Shutdown cancellation must leave the durable phase untouched ('running'), so
    # the next boot recovers the game instead of burying it.
    from tests.fixtures.server import HangingGraph

    upserts.clear()
    parked = quiet_session(HangingGraph())
    parked.start()
    await asyncio.sleep(0.05)
    await parked.shutdown()
    assert all("phase" not in u for u in upserts)


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


def _row(**over):
    base = dict(game_id="g-1", phase="running", host_key="", model="", byok=False,
                seats=[{"name": "hao", "token": "tok-1"}], human_players=["player_3"])
    base.update(over)
    return durable.SessionRow(**base)


async def _recover(monkeypatch, rows, graph):
    async def fake_rows():
        return rows

    async def fake_events(game_id):
        return []

    async def rec_upsert(game_id, **fields):
        rec_upsert.calls.append((game_id, fields))

    rec_upsert.calls = []
    monkeypatch.setattr(durable, "_graph", graph)
    monkeypatch.setattr(durable, "load_open_sessions", fake_rows)
    monkeypatch.setattr(durable, "load_events", fake_events)
    monkeypatch.setattr(durable, "upsert_session", rec_upsert)
    monkeypatch.setattr("server.runtime.seed_memory_from_config", lambda *a, **k: None)
    games: dict = {}
    await recovery.recover_registry(games)
    return games, rec_upsert.calls


async def test_waiting_room_revives_with_its_identity(monkeypatch):
    from datetime import datetime, timezone

    stamp = datetime(2026, 8, 20, 12, 0, tzinfo=timezone.utc)
    row = _row(phase="waiting", host_key="hk-9",
               room_name="wolves den", locked=True, created_at=stamp)
    games, _ = await _recover(monkeypatch, [row], FakeDurableGraph(None))

    lobby = games["g-1"]
    assert (lobby.game_id, lobby.host_key) == ("g-1", "hk-9")
    assert lobby.players == ["hao"] and lobby.tokens == ["tok-1"]
    # The browser/lock facts survive too: a restart must not silently unlock a
    # room or reset its listing-TTL clock to boot time.
    assert (lobby.name, lobby.locked, lobby.created_at) == ("wolves den", True, stamp)


async def test_parked_game_revives_reparked_and_resumes_on_the_answer(monkeypatch):
    request = human_turn_request(player_id="player_3", phase="day_channel",
                                 can_pass=True, valid_targets=[])
    state = SimpleNamespace(next=("DAY_PHASE",), tasks=[SimpleNamespace(
        interrupts=[SimpleNamespace(value=request.model_dump(), id="int-9")])])
    graph = FakeDurableGraph(state)

    games, _ = await _recover(monkeypatch, [_row()], graph)
    session = games["g-1"]
    assert sorted(session.pending_requests) == ["player_3"]  # the returning-player view
    assert session.seat_for_token("tok-1") == "player_3"

    session.submit_turn({"message": "back from the dead"}, seat="player_3")
    await asyncio.wait_for(session.wait_finished(), timeout=10)
    resume = graph.calls[0]
    assert isinstance(resume, Command) and resume.resume["message"] == "back from the dead"


async def test_byok_game_revives_dead_with_a_clear_epitaph(monkeypatch):
    games, upserts = await _recover(monkeypatch, [_row(byok=True)],
                                    FakeDurableGraph(None))
    session = games["g-1"]
    assert "API key" in session.error and session._task is None
    assert ("g-1", {"phase": "dead", "error": session.error}) in upserts


async def test_stale_running_row_of_a_finished_game_is_closed(monkeypatch):
    state = SimpleNamespace(next=(), tasks=[])
    games, upserts = await _recover(monkeypatch, [_row()], FakeDurableGraph(state))
    assert games["g-1"]._task is None
    assert ("g-1", {"phase": "finished"}) in upserts
