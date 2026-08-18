"""server/runtime.py + server/app.py — session loop, entitlement, pacing, SSE framing.

The end-to-end test drives a real GameSession over the captured fixture through a fake
graph (zero LLM), asserting the task → translator → log → fan-out pipeline. The interrupt
test proves the full park/validate/resume round-trip with the CLI's HITL contract. No HTTP
server is spun up — the SSE generator is driven directly (it's just an async generator);
the HTTP layer has its own suite (test_http_api.py). Async tests run on pytest-asyncio
(asyncio_mode=auto); shared machinery comes from tests/fixtures + tests/factories.
"""
from __future__ import annotations

import asyncio

import pytest

from Agents.turn.human_turn import HumanTurnContractError
from server.app import _sse, event_stream
from server.runtime import PacingTracker, entitled
from server.schemas import events as ev
from server.translate import Translator
from tests.factories.builders import human_turn_request
from tests.fixtures.server import FakeGraph, HangingGraph

ROLES = {"w0": "wolf", "w1": "wolf", "v1": "villager", "inv": "investigator"}


# ---- entitled(): the tier gate ----------------------------------------------------------


def _ev(cls, **kw):
    return cls(seq=1, day=1, **kw)


def test_public_reaches_everyone_including_spectators():
    e = _ev(ev.GmMessage, channel_seq=0, text="dawn")
    assert entitled(e, "", ROLES, False)
    assert entitled(e, "v1", ROLES, False)


def test_faction_reaches_wolves_only():
    e = _ev(ev.WolfMessage, round=1, wolf="w0", message="target?")
    assert entitled(e, "w0", ROLES, False)
    assert not entitled(e, "v1", ROLES, False)
    assert not entitled(e, "", ROLES, False)


def test_seat_reaches_the_named_recipient_only():
    e = _ev(ev.InvestigationResult, player="inv", target="w0", role="wolf")
    assert entitled(e, "inv", ROLES, False)
    assert not entitled(e, "w0", ROLES, False)


def test_observer_reaches_nobody_live_and_everybody_after_game_over():
    e = _ev(ev.NightAction, actor="inv", role="investigator", target="w0")
    assert not entitled(e, "inv", ROLES, False)
    assert all(entitled(e, seat, ROLES, True) for seat in ("", "v1", "w0"))


# ---- the session over the real captured game --------------------------------------------

async def test_session_replays_the_fixture_end_to_end(quiet_session, fixture_parts):
    session = quiet_session(FakeGraph(fixture_parts))
    session.start()
    await asyncio.wait_for(session.wait_finished(), timeout=30)

    assert session.error is None
    assert session.game_over is True

    expected = Translator()
    n_expected = sum(len(expected.translate(p)) for p in fixture_parts)
    assert len(session.log) == n_expected
    assert session.public_alive_counts(), "census must be derivable from the log"


async def test_sse_replays_the_whole_log_after_game_over(quiet_session, fixture_parts):
    session = quiet_session(FakeGraph(fixture_parts))
    session.start()
    await session.wait_finished()

    frames = []
    gen = _sse(session, seat="", last_seq=0)
    async for frame in gen:
        frames.append(frame)
        if len(frames) == len(session.log):
            break
    await gen.aclose()

    # Post-game connection: observer unlock means every event replays, in seq order.
    ids = [int(f.split("\n", 1)[0].removeprefix("id: ")) for f in frames]
    assert ids == [e.seq for e in session.log]
    assert all("event: game" in f for f in frames)


async def test_pre_start_subscriber_still_gets_faction_events(quiet_session, fixture_parts):
    """Regression: a viewer connecting BEFORE the first part is processed must not freeze
    an empty roles map — the translator REBINDS roles at INITIALIZE_GAME, so _sse must
    read them fresh per entitlement check, not capture the reference at connect time."""
    expected = Translator()
    for p in fixture_parts:
        expected.translate(p)
    wolf_seat = next(s for s, r in expected.roles.items() if r == "wolf")

    session = quiet_session(FakeGraph(fixture_parts))
    gen = _sse(session, seat=wolf_seat, last_seq=0)

    async def collect():
        async for frame in gen:
            if '"wolf_message"' in frame:
                return True

    collector = asyncio.ensure_future(collect())
    await asyncio.sleep(0)  # let the generator subscribe while the log is still empty
    session.start()
    try:
        assert await asyncio.wait_for(collector, timeout=30) is True
    finally:
        await gen.aclose()


async def test_postgame_reconnect_cursor_does_not_skip_the_withheld_backlog(
        quiet_session, fixture_parts):
    """Ruled 2026-08-18 (variant 1): a spectator who watched live up to the end, then
    reconnects AFTER game over, sends a high last_seq — but that cursor only ever covered
    public events. The replay must still deliver the withheld tiers below the cursor,
    and must NOT resend the public events the cursor genuinely covers."""
    session = quiet_session(FakeGraph(fixture_parts))
    session.start()
    await asyncio.wait_for(session.wait_finished(), timeout=30)

    roles = session.translator.roles
    live_public = [e for e in session.log if entitled(e, "", roles, False)]
    cursor = max(e.seq for e in live_public)  # "I received everything public, live"
    withheld = {e.seq for e in session.log if not entitled(e, "", roles, False)}
    assert withheld, "fixture must contain withheld events for this test to mean anything"

    frames = []
    gen = _sse(session, seat="", last_seq=cursor)
    async for frame in gen:
        frames.append(frame)
        if len(frames) == len(withheld):
            break
    await gen.aclose()

    ids = {int(f.split("\n", 1)[0].removeprefix("id: ")) for f in frames}
    assert ids == withheld  # every withheld event arrives; no covered public event resent
    assert all(i <= cursor or i in withheld for i in ids)


async def test_reconnect_header_overrides_the_frozen_query_cursor(
        quiet_session, fixture_parts):
    """Ruled 2026-08-18 (①): the browser's auto-reconnect reuses the ORIGINAL url verbatim
    (query cursor = a fossil from construction time) and carries its real position in the
    Last-Event-ID header — the header must win when present."""
    session = quiet_session(FakeGraph(fixture_parts))
    session.start()
    await asyncio.wait_for(session.wait_finished(), timeout=30)

    roles = session.translator.roles
    cursor = max(e.seq for e in session.log if entitled(e, "", roles, False))
    withheld = {e.seq for e in session.log if not entitled(e, "", roles, False)}

    # Stale query cursor (0) + living header cursor: header must be used. (The Game
    # dependency is resolved by FastAPI in production; here the session is passed direct.)
    response = await event_stream(session, seat="", last_seq=0, last_event_id=str(cursor))
    frames = []
    gen = response.body_iterator
    async for frame in gen:
        frames.append(frame)
        if len(frames) == len(withheld):
            break
    await gen.aclose()

    ids = {int(f.split("\n", 1)[0].removeprefix("id: ")) for f in frames}
    assert ids == withheld  # header honored: only the withheld backlog replays, not all 0+


async def test_live_unlock_flushes_withheld_backlog_below_a_reconnect_cursor(
        quiet_session, fixture_parts):
    """Ruled 2026-08-18 (variant 2): a viewer reconnects MID-game with a cursor, then the
    game ends while they are connected. The R7 flush must not treat the cursor as covering
    the withheld events below it."""
    # Split the fixture at the first point where wolf chat sits BELOW the public
    # high-water mark (a later public event outranks it) — so the reconnect cursor,
    # built from public seqs, is above withheld traffic. Park phase 1 behind a
    # synthetic interrupt there.
    probe, seen, split_at = Translator(), [], None
    for i, p in enumerate(fixture_parts):
        seen.extend(probe.translate(p))
        wolf_seqs = [e.seq for e in seen if e.type == "wolf_message"]
        public_max = max((e.seq for e in seen
                          if entitled(e, "", probe.roles, False)), default=0)
        if wolf_seqs and min(wolf_seqs) < public_max:
            split_at = i + 1
            break
    assert split_at is not None
    session = quiet_session(FakeGraph(fixture_parts[:split_at] + [_interrupt_part()],
                                      fixture_parts[split_at:]))
    session.start()
    while session.pending_request is None:
        await asyncio.sleep(0.01)

    roles = session.translator.roles
    cursor = max(e.seq for e in session.log if entitled(e, "", roles, False))
    wolf_below_cursor = {e.seq for e in session.log
                         if e.type == "wolf_message" and e.seq <= cursor}
    assert wolf_below_cursor, "phase 1 must hold withheld wolf chat below the cursor"

    gen = _sse(session, seat="", last_seq=cursor)  # mid-game reconnector

    async def collect():
        got: set[int] = set()
        async for frame in gen:
            if frame.startswith("id: "):
                got.add(int(frame.split("\n", 1)[0].removeprefix("id: ")))
            if wolf_below_cursor <= got:
                return True

    collector = asyncio.ensure_future(collect())
    await asyncio.sleep(0)          # let the generator subscribe + replay
    session.submit_turn({"message": "hello table"})   # resume: phase 2 -> game over
    try:
        assert await asyncio.wait_for(collector, timeout=30) is True
    finally:
        await gen.aclose()


# ---- the interrupt round-trip -----------------------------------------------------------

def _interrupt_part() -> dict:
    """A day-channel interrupt part, request built by the shared HITL builder."""
    value = human_turn_request(player_id="player_3", phase="day_channel",
                               valid_targets=[], surviving_players=["player_3"]).model_dump()
    return {"type": "updates", "ns": [], "data": {"__interrupt__": [{"value": value}]}}


async def test_interrupt_parks_validates_and_resumes(quiet_session):
    session = quiet_session(FakeGraph([_interrupt_part()], []))
    session.start()
    while session.pending_request is None:
        await asyncio.sleep(0.01)

    # A contract-violating action bounces AND the request stays pending for a retry.
    with pytest.raises(HumanTurnContractError):
        session.submit_turn({"message": "   "})
    assert session.pending_request is not None

    session.submit_turn({"message": "hello table"})
    await asyncio.wait_for(session.wait_finished(), timeout=10)

    assert session.error is None
    # The input_request event shipped to the log, seat-tiered to the human.
    (request_event,) = [e for e in session.log if e.type == "input_request"]
    assert request_event.player == "player_3"
    assert request_event.action_kind == "discuss"


async def test_shutdown_cancels_a_parked_game(quiet_session):
    """Lifespan teardown path: a game parked mid-stream is cancelled cleanly —
    _finished still fires (the finally), no pending-task noise on server exit."""
    session = quiet_session(HangingGraph())
    session.start()
    await asyncio.sleep(0)  # let the task enter astream
    await asyncio.wait_for(session.shutdown(), timeout=5)
    assert session._finished.is_set()


# ---- pacing: public denominator + padded completion -------------------------------------

async def test_pacing_night_denominator_is_the_public_census():
    snapshots = []
    tracker = PacingTracker(snapshots.append)
    tracker.on_event(_ev(ev.GameStarted, seats=[], cast_role_counts={
        "wolf": 2, "villager": 3, "healer": 1, "investigator": 1,
        "serial_killer": 1, "vigilante": 1,
    }))
    # The investigator was publicly lynched -> not a unit tonight.
    tracker.on_event(_ev(ev.LynchResult, outcome="lynched", player="p", role="investigator",
                         vote_counts={}, no_lynch_streak=0))
    tracker.on_event(_ev(ev.PhaseChange, phase="night"))
    assert snapshots[-1].total == 4  # wolves, healer, SK, vigilante
    assert snapshots[-1].done == 0

    tracker.on_branch_done("wolves")
    assert (snapshots[-1].done, snapshots[-1].stage) == (1, "night")
    tracker.on_branch_done("wolves")  # idempotent
    assert snapshots[-1].done == 1

    tracker.on_event(_ev(ev.NightResult, deaths=[], save=None))  # dawn: stage closes
    assert snapshots[-1].done == snapshots[-1].total


async def test_pacing_vote_stage_counts_ballots_against_survivors():
    snapshots = []
    tracker = PacingTracker(snapshots.append)
    tracker.on_event(_ev(ev.GameStarted, seats=[], cast_role_counts={
        "wolf": 1, "villager": 2,
    }))
    tracker.on_event(_ev(ev.PhaseChange, phase="voting"))
    assert snapshots[-1] == ev.PhaseProgress(
        day=1, stage="day_vote", done=0, total=3)
    tracker.on_ballot()
    tracker.on_ballot()
    assert snapshots[-1].done == 2
