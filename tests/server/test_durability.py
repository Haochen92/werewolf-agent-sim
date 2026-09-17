"""Live-session durability: translator hydration, the write path, boot recovery.

All hermetic — the autouse guard blanks the DSN, so durable's write helpers no-op
unless a test monkeypatches its seams (recorders for writes; a FakeDurableGraph for
the checkpoint's aget_state/astream). The real-Postgres path is exercised by the
manual restart smoke, not here.
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from langgraph.types import Command

from server.game.live_game_registry import LiveGameRegistry
from server.housekeeping import recovery
from server.database_models.game import DROPPED, RUNNING, WAITING, GameRow
from server.storage.game_repository import derive_completion_metadata, event_log_shortfall
from server.game.translate import Translator
from server.schemas import events as ev
from tests.factories.builders import human_turn_request
from tests.fixtures.server import FakeGraph
from tests.fixtures.translator_golden import _updates

# ---- translator hydration ------------------------------------------------------------------


def test_hydrate_rebuilds_the_shadow_from_the_log(fixture_chunks):
    """Round-trip: state rebuilt from EVENTS must match state built from PARTS —
    same roles, same continued seq, and (the load-bearing one) the same ship-once
    guards, or a post-restart resume would re-ship every delivered message."""
    lived = Translator()
    log = [e for p in fixture_chunks for e in lived.translate(p)]

    revived = Translator()
    revived.hydrate(log)

    assert revived.roles == lived.roles
    assert revived.wolves == lived.wolves
    assert revived.seq == lived.seq  # next event continues, never collides
    assert revived._seen_day_entries == lived._seen_day_entries
    assert revived._seen_wolf_msgs == lived._seen_wolf_msgs
    assert revived._strategies == lived._strategies
    assert revived._targets == lived._targets
    assert revived._last_day_ballots == lived._last_day_ballots
    # Uncollected ballots come back from the resumed step, including cached chunks.
    assert revived._day_ballots == {} and revived._wolf_votes == {}


@pytest.mark.parametrize("resolution", ["DAY_RESOLUTION", "NIGHT_RESOLUTION"])
def test_restart_before_every_resolution_matches_uninterrupted_play(fixture_chunks, resolution):
    """The producing phase is committed; only its consumer runs after this restart."""
    lived = Translator()
    log = []
    checked = 0
    for chunk in fixture_chunks:
        restored = None
        if resolution in chunk.get("data", {}):
            restored = Translator()
            restored.hydrate(log)
        expected = lived.translate(chunk)
        if restored is not None:
            assert restored.translate(chunk) == expected
            checked += 1
        log.extend(expected)
    assert checked == 5  # Includes empty nights, saves, lynches and multi-day resets.


@pytest.mark.parametrize("wolf", [False, True], ids=["day-vote", "wolf-vote"])
async def test_recovered_cached_votes_wait_for_collection_and_include_every_voter(
        quiet_session, fixture_chunks, wolf):
    scope = "WOLF_NIGHT_PHASE" if wolf else "DAY_PHASE"
    node = "WOLF_NIGHT_VOTE" if wolf else "vote"
    human_node = "WOLF_NIGHT_VOTE_HUMAN" if wolf else "vote_human"
    collector = "COLLECT_WOLF_VOTES" if wolf else "COLLECT_VOTES"
    event_type = "wolf_vote" if wolf else "vote_cast"

    def ballot(player, target):
        return ({"wolf_channel": [{"wolf": player, "vote": target}]}
                if wolf else {"day_votes": [{"voter": player, "votee": target}]})

    before = quiet_session(FakeGraph([]))
    before._on_chunk(fixture_chunks[0])
    before._on_chunk(_updates("NIGHT_START" if wolf else "START_VOTING", {}))
    ai_vote = ballot("player_4", "player_6")
    before._on_chunk(_updates(node, ai_vote, scope))

    restored = quiet_session(FakeGraph([]))
    restored.reload_history(before.log, [])
    original = list(restored.log)
    # A cached AI sibling has no new event or pacing tick; it still has a ballot.
    restored._on_chunk(_updates(node, ai_vote, scope, cached=True))
    restored._on_chunk(_updates(node, ai_vote, scope, cached=True))  # duplicate is harmless
    assert restored.log == original
    restored._on_chunk(_updates(human_node, ballot("player_9", "player_6"), scope))
    assert not any(e.type == event_type for e in restored.log)
    restored._on_chunk(_updates(collector, {"wolves_kill_target": "player_6"}
                               if wolf else {}, scope))
    votes = [e for e in restored.log if e.type == event_type]
    assert len(votes) == 2
    assert {e.wolf if wolf else e.voter for e in votes} == {"player_4", "player_9"}
    assert {e.votee for e in votes} == {"player_6"}
    await before.suspend()
    await restored.suspend()


# ---- the write path (runtime -> durable) -----------------------------------------------------


async def test_run_persists_events_and_finalizes_one_game_row(quiet_session, fixture_chunks):
    repository = RecordingGameRepository()

    session = quiet_session(FakeGraph(fixture_chunks), repository=repository)
    session.start()
    await asyncio.wait_for(session.wait_finished(), timeout=30)

    assert [e.seq for e in repository.events] == [e.seq for e in session.log]
    assert repository.completions == [(session.game_id, len(session.log), 0)]
    # The fixture game is all-LLM: human_players never changes, so no seat upsert.
    assert all("human_players" not in fields for fields in repository.updates)


async def test_death_marks_the_row_dead_and_cancellation_does_not(quiet_session):
    repository = RecordingGameRepository()

    class ExplodingGraph:
        async def astream(self, payload, **_):
            raise RuntimeError("provider died")
            yield  # pragma: no cover

    session = quiet_session(ExplodingGraph(), repository=repository)
    session.start()
    await asyncio.wait_for(session.wait_finished(), timeout=10)
    assert repository.updates[-1]["status"] == DROPPED
    assert "provider died" in repository.updates[-1]["error"]
    assert repository.completions == []

    # Shutdown cancellation must leave the durable status untouched ('running'), so
    # the next boot recovers the game instead of burying it.
    from tests.fixtures.server import HangingGraph

    repository.updates.clear()
    parked = quiet_session(HangingGraph(), repository=repository)
    parked.start()
    await asyncio.sleep(0.05)
    await parked.suspend()
    assert all("status" not in fields for fields in repository.updates)


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
        self.updates = []
        self.update_calls = []

    async def record_events(self, game_id, events):
        self.events.extend(events)
        return True

    async def update_game(self, game_id, **fields):
        self.updates.append(fields)
        self.update_calls.append((game_id, fields))
        return True

    async def complete_game(self, game_id, log, n_humans):
        self.completions.append((game_id, len(log), n_humans))

    async def load_recoverable_games(self):
        return self.rows

    async def load_events(self, game_id):
        return []


async def test_failed_saves_retry_the_whole_unsaved_tail_and_human_assignment(quiet_session):
    class FlakyRepository(RecordingGameRepository):
        fail = True

        async def record_events(self, game_id, events):
            return False if self.fail else await super().record_events(game_id, events)

        async def update_game(self, game_id, **fields):
            return False if self.fail else await super().update_game(game_id, **fields)

    repository = FlakyRepository()
    session = quiet_session(FakeGraph([]), repository=repository, human_players=["player_3"])
    session.log = [ev.PhaseChange(seq=1, day=1, phase="day")]
    await session._persist_tail()
    assert session._saved_event_count == 0 and session._saved_humans == []
    repository.fail = False
    session.log.append(ev.PhaseChange(seq=2, day=1, phase="voting"))
    await session._persist_tail()
    await session._persist_tail()  # a successful save is not sent again
    assert repository.events == session.log
    assert repository.updates == [{"human_players": ["player_3"]}]
    assert session._saved_event_count == 2 and session._saved_humans == ["player_3"]


@pytest.mark.parametrize("persistent_failure", [False, True])
async def test_final_chunk_gets_one_bounded_retry_before_completion(
        quiet_session, fixture_chunks, persistent_failure):
    class FinalSaveFails(RecordingGameRepository):
        attempts = 0

        async def record_events(self, game_id, events):
            if any(e.type == "game_over" for e in events):
                self.attempts += 1
                if self.attempts == 1 or persistent_failure:
                    return False
            return await super().record_events(game_id, events)

        async def complete_game(self, game_id, log, n_humans):
            assert self.attempts == 2
            assert (self.events == log) is not persistent_failure
            await super().complete_game(game_id, log, n_humans)

    repository = FinalSaveFails()
    # Stop at game over so there is truly no subsequent chunk to retry the failed save.
    end = next(i for i, chunk in enumerate(fixture_chunks) if "END_GAME" in chunk["data"])
    session = quiet_session(FakeGraph(fixture_chunks[:end + 1]), repository=repository)
    session.start()
    await asyncio.wait_for(session.wait_finished(), timeout=10)
    assert session.error is None and session.game_over
    assert len(repository.completions) == 1


def _row(**over):
    base = dict(game_id="g-1", status=RUNNING, host_key="", model="", byok=False,
                seats=[{"name": "hao", "token": "tok-1"}], human_players=["player_3"])
    base.update(over)
    return GameRow(**base)


async def _recover(monkeypatch, rows, graph, check_key=None):
    monkeypatch.setattr("server.game.game_session.seed_memory_from_config", lambda *a, **k: None)
    repository = RecordingGameRepository(rows=rows)
    extra = {"check_key": check_key} if check_key is not None else {}
    games = LiveGameRegistry(repository, SimpleNamespace(graph=graph), **extra)
    await recovery.recover_registry(games, repository)
    return games, repository


async def test_a_waiting_row_is_never_rebuilt(monkeypatch):
    # Rooms live in memory only (ruled 2026-09-12): a restart closes them. A waiting row
    # can only predate that ruling; it is left alone, neither revived nor rewritten.
    row = _row(status=WAITING, host_key="hk-9", room_name="wolves den")
    games, repository = await _recover(monkeypatch, [row], FakeDurableGraph(None))
    assert games.get("g-1") is None and len(games) == 0
    assert repository.update_calls == []


@pytest.mark.parametrize("partial_park", [False, True], ids=["checkpoint-read", "second-prompt"])
async def test_failed_recovery_removes_the_session_and_cancels_partial_clocks(
        monkeypatch, partial_park):
    from server.game.seat_clocks import SeatClocks

    armed = []
    original_arm = SeatClocks.arm

    def arm(self, request):
        original_arm(self, request)
        armed.extend(self._tasks.values())

    monkeypatch.setattr(SeatClocks, "arm", arm)
    request = human_turn_request(player_id="player_3")
    state = SimpleNamespace(next=("DAY_PHASE",), tasks=[SimpleNamespace(interrupts=[
        SimpleNamespace(value=request.model_dump(), id="good"),
        SimpleNamespace(value={"not": "a prompt"}, id="bad"),
    ])])

    class BrokenGraph(FakeDurableGraph):
        async def aget_state(self, config):
            if not partial_park:
                raise RuntimeError("checkpoint read failed")
            return self._state

    row = _row(seats=[{"token": "t1"}, {"token": "t2"}])
    games, repository = await _recover(monkeypatch, [row], BrokenGraph(state))
    await asyncio.sleep(0)  # settle cancellation of any clock armed before the failure
    assert games.get(row.game_id) is None
    assert repository.updates[-1] == {"status": DROPPED, "error": "recovery failed on restart"}
    assert bool(armed) is partial_park
    assert all(task.cancelled() for task in armed)


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


async def test_byok_game_waits_for_its_key_and_resumes_when_a_seat_holder_funds_it(monkeypatch):
    request = human_turn_request(player_id="player_3", phase="day_channel",
                                 can_pass=True, valid_targets=[])
    state = SimpleNamespace(next=("DAY_PHASE",), tasks=[SimpleNamespace(
        interrupts=[SimpleNamespace(value=request.model_dump(), id="int-9")])])
    graph = FakeDurableGraph(state)
    probed = []

    async def check_key(model, api_key):
        probed.append((model, api_key))
        if api_key == "sk-bad":
            raise ValueError("the provider rejected this key: 401")

    stamp = datetime(2026, 9, 11, 9, 0, tzinfo=timezone.utc)
    games, repository = await _recover(
        monkeypatch, [_row(byok=True, model="gemini-2.5-pro", updated_at=stamp)], graph,
        check_key=check_key)

    # Rebuilt, live, idle: no task, no question re-parked yet, the row left as it was.
    session = games.get("g-1")
    assert session.awaiting_key and session._task is None and not session.pending_requests
    assert session.parked_since == stamp  # the sweeper's clock runs from the last write
    assert repository.update_calls == []

    # A bad key is refused by the provider probe and the game keeps waiting.
    with pytest.raises(ValueError, match="rejected"):
        await games.resume_with_key("g-1", "sk-bad")
    assert session.awaiting_key and session._task is None

    # A good key: the model is the row's, the question is re-parked, the task runs.
    await games.resume_with_key("g-1", "sk-good")
    assert probed == [("gemini-2.5-pro", "sk-bad"), ("gemini-2.5-pro", "sk-good")]
    assert not session.awaiting_key
    assert session._llm_selection.api_key == "sk-good"
    assert session._llm_selection.model == "gemini-2.5-pro"
    assert "player_3" in session.pending_requests and session._task is not None
    with pytest.raises(LookupError):  # not waiting any more
        await games.resume_with_key("g-1", "sk-again")
    await session.suspend()


async def test_house_selected_model_survives_restart(monkeypatch):
    model = "gemini-3.6-flash"
    state = SimpleNamespace(next=("resume",), tasks=[])
    games, _ = await _recover(
        monkeypatch, [_row(model=model, byok=False)], FakeDurableGraph(state))

    assert games.get("g-1")._llm_selection.model == model


async def test_memory_switch_survives_restart(monkeypatch):
    # A game is rebuilt with the switch it was started with — a memory-on game must not
    # quietly continue memory-off, and a memory-off game must not pick memory up.
    state = SimpleNamespace(next=("resume",), tasks=[])
    games, _ = await _recover(
        monkeypatch, [_row(memory=True), _row(game_id="g-2")], FakeDurableGraph(state))

    assert all(games.get("g-1").config["configurable"]["memory_config"].values())
    assert not any(games.get("g-2").config["configurable"]["memory_config"].values())


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


def test_event_log_shortfall_names_a_short_or_holed_log():
    assert event_log_shortfall(expected=3, stored=3, last_seq=3) is None
    # A batch failed to write during play: fewer rows than the game produced.
    assert event_log_shortfall(3, 2, 3) == "event log incomplete: 2 of 3 events stored, last seq 3"
    # The hole a restart hides: the revived game's log was rebuilt from the rows, so the
    # counts agree, but the seq numbers skip.
    assert event_log_shortfall(2, 2, 3) == "event log incomplete: 2 of 2 events stored, last seq 3"
    # Nothing stored at all (storage was off while the game ran, then turned on).
    assert event_log_shortfall(3, 0, 0) == "event log incomplete: 0 of 3 events stored, last seq 0"
