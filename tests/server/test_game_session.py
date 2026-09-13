"""Runtime sessions plus the game router's entitlement, pacing, and SSE framing.

The end-to-end test drives a real GameSession over the captured fixture through a fake
graph (zero LLM), asserting the task → translator → log → fan-out pipeline. The interrupt
test proves the full park/validate/resume round-trip with the CLI's HITL contract. No HTTP
server is spun up — the SSE generator is driven directly (it's just an async generator);
the HTTP layer has its own suite (test_http_api.py). Async tests run on pytest-asyncio
(asyncio_mode=auto); shared machinery comes from tests/fixtures + tests/factories.
"""
from __future__ import annotations

import asyncio
from contextlib import contextmanager
from types import SimpleNamespace

import pytest

from Agents.turn.human_turn import HumanTurnContractError
from server.game import game_session as rt
from server.routes.games import _sse, event_stream
from server.game.pacing import PacingTracker
from server.game.entitlement import entitled
from server.schemas import events as ev
from server.game.translate import Translator
from tests.factories.builders import human_turn_request
from tests.fixtures.server import FakeGraph, HangingGraph

ROLES = {"w0": "wolf", "w1": "wolf", "v1": "villager", "inv": "investigator"}


class _TraceRoot:
    trace_id = "stable-game-trace"
    id = "game-root-span"

    def __init__(self):
        self.updates = []
        self.trace_updates = []

    def update(self, **kwargs):
        self.updates.append(kwargs)

    def update_trace(self, **kwargs):
        self.trace_updates.append(kwargs)


async def test_server_session_owns_one_stable_game_trace(quiet_session, monkeypatch):
    captured = {}
    root = _TraceRoot()

    @contextmanager
    def observation(**kwargs):
        captured["observation"] = kwargs
        yield root

    def create_trace_id(*, seed):
        captured["trace_seed"] = seed
        return "stable-game-trace"

    monkeypatch.setattr(rt, "langfuse", SimpleNamespace(
        create_trace_id=create_trace_id,
        start_as_current_observation=observation,
    ))

    def create_handler(*, trace_context):
        captured["handler_context"] = trace_context
        return "game-handler"

    monkeypatch.setattr(rt, "create_langfuse_handler", create_handler)
    monkeypatch.setattr(rt, "flush", lambda: captured.setdefault("flushed", True))

    session = quiet_session(FakeGraph([]))
    session.start()
    await asyncio.wait_for(session.wait_finished(), timeout=10)

    assert session.config["callbacks"] == ["game-handler"]
    assert captured["handler_context"] == {
        "trace_id": "stable-game-trace", "parent_span_id": "game-root-span"}
    assert captured["trace_seed"] == f"werewolf-game:{session.game_id}"
    assert captured["observation"]["trace_context"] == {
        "trace_id": "stable-game-trace"}
    assert root.trace_updates[0]["name"] == "werewolf_game"
    assert root.trace_updates[0]["metadata"]["game_id"] == session.game_id
    assert root.trace_updates[-1]["output"]["status"] == "success"
    assert captured["flushed"] is True


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


# ---- seat_for_token(): the proof-of-identity lookup -------------------------------------


def test_token_maps_to_the_dealt_seat_in_join_order(quiet_session):
    """Join order IS deal order: token i owns human_players[i] (the orchestrator
    builds the list deterministically — pre-shuffle candidate, then extras)."""
    session = quiet_session(FakeGraph([]), seat_tokens=["tok-a", "tok-b"])

    # Before INITIALIZE_GAME lands: valid tokens resolve to "" (seatless), not None.
    assert session.seat_for_token("tok-a") == ""
    assert session.seat_for_token("forged") is None
    assert session.seat_for_token("") is None  # no cookie is never a valid token

    session.human_players = ["player_4", "player_7"]  # what INITIALIZE_GAME sets
    assert session.seat_for_token("tok-a") == "player_4"
    assert session.seat_for_token("tok-b") == "player_7"
    assert session.seat_for_token("forged") is None


def test_owns_mirrors_the_lobby_contract(quiet_session):
    session = quiet_session(FakeGraph([]), seat_tokens=["tok-a", "tok-b"])
    assert session.owns("tok-b") is True
    assert session.owns("forged") is False


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
    assert session.public_alive_counts, "census must be derivable from the log"


async def test_sse_replays_the_whole_log_after_game_over(quiet_session, fixture_parts):
    session = quiet_session(FakeGraph(fixture_parts))
    session.start()
    await session.wait_finished()

    frames = []
    gen = _sse(session, "", last_seq=0)
    async for frame in gen:
        frames.append(frame)
        if len(frames) == len(session.log):
            break
    await gen.aclose()

    # Post-game connection: observer unlock means every event replays, in seq order.
    ids = [int(f.split("\n", 1)[0].removeprefix("id: ")) for f in frames]
    assert ids == [e.seq for e in session.log]
    assert all("event: game" in f for f in frames)


async def test_pre_start_subscriber_still_gets_faction_events(quiet_session, fixture_parts,
                                                              monkeypatch):
    """Regression: a viewer connecting BEFORE the first part is processed must not freeze
    an empty roles map — the translator REBINDS roles at INITIALIZE_GAME, so _sse must
    read them fresh per entitlement check, not capture the reference at connect time."""
    expected = Translator()
    for p in fixture_parts:
        expected.translate(p)
    wolf_seat = next(s for s, r in expected.roles.items() if r == "wolf")

    session = quiet_session(FakeGraph(fixture_parts))
    monkeypatch.setattr(session, "seat_of_viewer", lambda token: wolf_seat)  # view as the wolf
    gen = _sse(session, "wolf-token", last_seq=0)

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
    gen = _sse(session, "", last_seq=cursor)
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
    response = await event_stream(session, token="", last_seq=0, last_event_id=str(cursor))
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
    while not session.pending_requests:
        await asyncio.sleep(0.01)

    roles = session.translator.roles
    cursor = max(e.seq for e in session.log if entitled(e, "", roles, False))
    wolf_below_cursor = {e.seq for e in session.log
                         if e.type == "wolf_message" and e.seq <= cursor}
    assert wolf_below_cursor, "phase 1 must hold withheld wolf chat below the cursor"

    gen = _sse(session, "", last_seq=cursor)  # mid-game reconnector

    async def collect():
        got: set[int] = set()
        async for frame in gen:
            if frame.startswith("id: "):
                got.add(int(frame.split("\n", 1)[0].removeprefix("id: ")))
            if wolf_below_cursor <= got:
                return True

    collector = asyncio.ensure_future(collect())
    await asyncio.sleep(0)          # let the generator subscribe + replay
    session.submit_turn({"message": "hello table"}, seat="player_3")  # resume -> game over
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
    while not session.pending_requests:
        await asyncio.sleep(0.01)

    # A contract-violating action bounces AND the request stays pending for a retry.
    with pytest.raises(HumanTurnContractError):
        session.submit_turn({"message": "   "}, seat="player_3")
    assert session.pending_requests

    session.submit_turn({"message": "hello table"}, seat="player_3")
    await asyncio.wait_for(session.wait_finished(), timeout=10)

    assert session.error is None
    # The input_request event shipped to the log, seat-tiered to the human.
    (request_event,) = [e for e in session.log if e.type == "input_request"]
    assert request_event.player == "player_3"
    assert request_event.action_kind == "discuss"
    # A lone answer resumes as a bare value — the path proven in live HITL games.
    assert session._graph.calls[1].resume == {"message": "hello table", "pass_turn": False,
                                              "target": None, "delegate": False}


async def test_child_namespace_interrupt_mirrors_park_and_ship_once(quiet_session):
    """subgraphs=True streams each interrupt twice — child ns first, root mirror after
    (parallel-interrupt probe, 2026-08-19). Only the root copy parks the seat and ships
    an input_request; the child copy is dropped, or every request doubles on the wire."""
    root = _interrupt_part()
    child = {**root, "ns": ["DAY_PHASE:abc123"]}
    session = quiet_session(FakeGraph([child, root], []))
    session.start()
    while not session.pending_requests:
        await asyncio.sleep(0.01)

    assert len([e for e in session.log if e.type == "input_request"]) == 1
    assert sorted(session.pending_requests) == ["player_3"]
    session.submit_turn({"message": "hello table"}, seat="player_3")
    await asyncio.wait_for(session.wait_finished(), timeout=10)
    assert session.error is None


def _two_seat_interrupt_part() -> dict:
    """One parallel superstep interrupting for two human seats (multi-human room)."""
    def item(player, interrupt_id):
        value = human_turn_request(player_id=player, phase="day_votes",
                                   valid_targets=["p9"]).model_dump()
        return {"value": value, "id": interrupt_id}
    return {"type": "updates", "ns": [], "data": {
        "__interrupt__": [item("player_3", "int-a"), item("player_5", "int-b")]}}


async def test_parallel_interrupts_park_per_seat_and_resume_as_one_batch(quiet_session):
    session = quiet_session(FakeGraph([_two_seat_interrupt_part()], []))
    session.start()
    while len(session.pending_requests) < 2:
        await asyncio.sleep(0.01)

    # An unknown-seat submission bounces, state intact.
    with pytest.raises(LookupError, match="player_8"):
        session.submit_turn({"target": "p9"}, seat="player_8")

    # First answer: accepted, but the game stays parked on the second seat.
    session.submit_turn({"target": "p9"}, seat="player_3")
    await asyncio.sleep(0.05)
    assert sorted(session.pending_requests) == ["player_5"]
    assert not session.ended

    # Last answer completes the batch: one id-addressed mapping resumes the graph.
    session.submit_turn({"target": "p9"}, seat="player_5")
    await asyncio.wait_for(session.wait_finished(), timeout=10)
    assert session.error is None
    resume = session._graph.calls[1].resume
    assert set(resume) == {"int-a", "int-b"}
    assert all(answer["target"] == "p9" for answer in resume.values())


# ---- the AFK timer: multi-human games delegate a parked seat's turn ----------------------

async def test_afk_timeout_delegates_the_parked_turn(quiet_session, monkeypatch):
    """The seat is absent but ANOTHER human is watching: at expiry the table delegates
    this one turn to the seat's agent (seat_continuity.md §5, "someone connected")."""
    monkeypatch.setattr("server.game.seat_clocks.AFK_TIMEOUT_SECONDS", 10.0)
    monkeypatch.setattr("server.game.seat_clocks.ABSENCE_GRACE_SECONDS", 0.05)
    session = quiet_session(FakeGraph([_interrupt_part()], []), seat_tokens=["t1", "t2"],
                            human_players=["player_3", "player_5"])
    session.subscribe("t2")  # the other human's open stream
    session.start()
    while not session.pending_requests:
        await asyncio.sleep(0.01)
    assert list(session.turn_deadlines) == ["player_3"]  # the client's countdown source
    # The input_request translated from the SAME part carries the deadline (parking
    # runs before translation): the countdown rides the push channel, no poll needed.
    (request_event,) = [e for e in session.log if e.type == "input_request"]
    assert request_event.deadline == session.turn_deadlines["player_3"]

    # Nobody answers: the stopwatch rings, the delegate sentinel resumes the game.
    await asyncio.wait_for(session.wait_finished(), timeout=10)
    assert session.error is None
    assert session._graph.calls[1].resume["delegate"] is True
    assert session.turn_deadlines == {}


async def test_afk_timer_never_arms_in_solo(quiet_session, monkeypatch):
    """One human seat = nobody is held hostage; the lone human may think forever."""
    monkeypatch.setattr("server.game.seat_clocks.AFK_TIMEOUT_SECONDS", 0.02)
    session = quiet_session(FakeGraph([_interrupt_part()], []), seat_tokens=["t1"])
    session.start()
    while not session.pending_requests:
        await asyncio.sleep(0.01)
    assert session.turn_deadlines == {}
    (request_event,) = [e for e in session.log if e.type == "input_request"]
    assert request_event.deadline is None  # no timer, no countdown to render
    await asyncio.sleep(0.1)  # several windows pass; the seat still owes input
    assert sorted(session.pending_requests) == ["player_3"]

    session.submit_turn({"message": "took my time"}, seat="player_3")
    await asyncio.wait_for(session.wait_finished(), timeout=10)
    assert session.error is None


async def test_afk_stopwatch_dies_with_its_own_question(quiet_session, monkeypatch):
    """Identity, not membership: the stopwatch for an ANSWERED question must not fire
    into the seat's NEXT question (answered at 119s, next turn parks at 119.5s, the
    old stopwatch rings at 120s — the new question keeps its full window)."""
    monkeypatch.setattr("server.game.seat_clocks.AFK_TIMEOUT_SECONDS", 0.01)
    session = quiet_session(FakeGraph([]), seat_tokens=["t1", "t2"], human_players=["p1", "p2"])
    answered = human_turn_request(player_id="p1")
    next_question = human_turn_request(player_id="p1", day=2)
    session.pending_requests["p1"] = next_question  # the seat owes input — but not THIS
    await session.clocks._expire("p1", answered, _now())  # the stale stopwatch rings
    assert session.pending_requests == {"p1": next_question}  # untouched


# ---- presence: the table decides between delegating and parking (seat_continuity §3–§5)

def _now():
    from datetime import datetime, timezone
    return datetime.now(timezone.utc)


def _seconds_left(session, seat) -> float:
    from datetime import datetime
    return (datetime.fromisoformat(session.turn_deadlines[seat]) - _now()).total_seconds()


def _park(session, seat="p1", **over):
    """Hand-park one question on a seat, the way _on_part does, and arm its clock."""
    request = human_turn_request(player_id=seat, **over)
    session.pending_requests[seat] = request
    session._pending_ids[seat] = seat
    session._pending_answers[seat] = asyncio.get_running_loop().create_future()
    session.parked_since = _now()
    session.clocks.arm(request)
    return request


async def test_afk_expiry_parks_when_nobody_is_connected(quiet_session, monkeypatch):
    """No human stream at all: the delegate is NOT submitted. The question keeps
    waiting like a solo game, the graph idles, and the countdown is withdrawn."""
    monkeypatch.setattr("server.game.seat_clocks.AFK_TIMEOUT_SECONDS", 10.0)
    monkeypatch.setattr("server.game.seat_clocks.ABSENCE_GRACE_SECONDS", 0.05)
    session = quiet_session(FakeGraph([_interrupt_part()], []), seat_tokens=["t1", "t2"])
    session.start()
    while not session.pending_requests:
        await asyncio.sleep(0.01)
    await asyncio.sleep(0.2)  # several grace windows pass
    assert sorted(session.pending_requests) == ["player_3"]  # still parked
    assert session.turn_deadlines == {} and session.clocks._tasks == {}
    assert len(session._graph.calls) == 1  # never resumed
    assert not session.ended


async def test_connected_seat_keeps_the_full_thinking_window(quiet_session, monkeypatch):
    monkeypatch.setattr("server.game.seat_clocks.AFK_TIMEOUT_SECONDS", 10.0)
    monkeypatch.setattr("server.game.seat_clocks.ABSENCE_GRACE_SECONDS", 0.5)
    session = quiet_session(FakeGraph([]), seat_tokens=["t1", "t2"], human_players=["p1", "p2"])
    session.subscribe("t1")
    _park(session)
    assert _seconds_left(session, "p1") > 9


async def test_absent_seat_gets_the_grace_not_the_thinking_window(quiet_session, monkeypatch):
    monkeypatch.setattr("server.game.seat_clocks.AFK_TIMEOUT_SECONDS", 10.0)
    monkeypatch.setattr("server.game.seat_clocks.ABSENCE_GRACE_SECONDS", 0.5)
    session = quiet_session(FakeGraph([]), seat_tokens=["t1", "t2"], human_players=["p1", "p2"])
    _park(session)
    assert 0 < _seconds_left(session, "p1") <= 0.5


async def test_stream_drop_starts_the_grace_and_a_return_lifts_it(quiet_session, monkeypatch):
    """Mid-turn disconnect: the effective deadline drops to the grace. Reconnect: it
    goes back to the ORIGINAL thinking deadline — absence never extends the clock."""
    monkeypatch.setattr("server.game.seat_clocks.AFK_TIMEOUT_SECONDS", 10.0)
    monkeypatch.setattr("server.game.seat_clocks.ABSENCE_GRACE_SECONDS", 0.5)
    session = quiet_session(FakeGraph([]), seat_tokens=["t1", "t2"], human_players=["p1", "p2"])
    q = session.subscribe("t1")
    _park(session)
    thinking = session.turn_deadlines["p1"]

    session.unsubscribe(q)
    assert _seconds_left(session, "p1") <= 0.5
    assert sorted(session.pending_requests) == ["p1"]  # not delegated on the drop itself

    session.subscribe("t1")
    assert session.turn_deadlines["p1"] == thinking


async def test_returning_seat_unparks_and_the_others_get_the_grace(quiet_session, monkeypatch):
    """A parked table (two absent seats). One human comes back: their own question gets
    a fresh thinking window; the other absent seat gets the grace, and at ITS expiry
    the presence test now finds someone — so that turn is delegated."""
    monkeypatch.setattr("server.game.seat_clocks.AFK_TIMEOUT_SECONDS", 10.0)
    monkeypatch.setattr("server.game.seat_clocks.ABSENCE_GRACE_SECONDS", 0.05)
    session = quiet_session(FakeGraph([]), seat_tokens=["t1", "t2", "t3"],
                            human_players=["p1", "p2", "p3"])
    _park(session, "p1")
    _park(session, "p2")
    await asyncio.sleep(0.2)
    assert session.turn_deadlines == {} and session.clocks._tasks == {}  # parked

    session.subscribe("t1")
    assert _seconds_left(session, "p1") > 9        # fresh window for the returner
    assert 0 < _seconds_left(session, "p2") <= 0.05  # grace for the still-absent seat
    await asyncio.sleep(0.2)
    assert sorted(session.pending_requests) == ["p1"]  # p2 delegated, p1 still theirs
    assert session._pending_answers["p2"].result()["delegate"] is True


async def test_solo_games_ignore_presence(quiet_session, monkeypatch):
    monkeypatch.setattr("server.game.seat_clocks.ABSENCE_GRACE_SECONDS", 0.01)
    session = quiet_session(FakeGraph([]), seat_tokens=["t1"], human_players=["p1"])
    request = human_turn_request(player_id="p1")
    session.pending_requests["p1"] = request
    q = session.subscribe("t1")
    session.unsubscribe(q)
    session.subscribe("t1")
    await asyncio.sleep(0.05)
    assert session.turn_deadlines == {} and session.clocks._tasks == {}
    assert session.pending_requests == {"p1": request}


async def test_answer_cancels_the_stopwatch(quiet_session, monkeypatch):
    monkeypatch.setattr("server.game.seat_clocks.AFK_TIMEOUT_SECONDS", 10.0)
    session = quiet_session(FakeGraph([]), seat_tokens=["t1", "t2"], human_players=["p1", "p2"])
    session.subscribe("t1")
    _park(session, valid_targets=["p2"])
    session.submit_turn({"target": "p2"}, seat="p1")
    await asyncio.sleep(0)
    assert session.clocks._tasks == {} and session.clocks._thinking == {}


def test_spectators_never_count_as_presence(quiet_session):
    session = quiet_session(FakeGraph([]), seat_tokens=["t1", "t2"], human_players=["p1", "p2"])
    session.subscribe()      # a spectator: no token at all
    session.subscribe("")    # the same, spelled out
    assert session.connected_seats == set() and not session.humans_present
    session.subscribe("t2")
    assert session.connected_seats == {"p2"} and session.seat_present("p2")


async def test_sse_registers_the_seat_for_its_lifetime(quiet_session, monkeypatch):
    """The stream's token is the presence signal: subscribed for as long as the
    generator lives, gone the moment it closes."""
    monkeypatch.setattr("server.routes.games._HEARTBEAT_SECONDS", 0.01)
    session = quiet_session(FakeGraph([]), seat_tokens=["t1", "t2"], human_players=["p1", "p2"])
    stream = _sse(session, "t1", 0)
    assert (await stream.__anext__()).startswith(": keep-alive")
    assert session.connected_seats == {"p1"}
    await stream.aclose()
    assert session.connected_seats == set()


async def test_shutdown_cancels_a_parked_game(quiet_session):
    """Lifespan teardown path: a game parked mid-stream is cancelled cleanly —
    _finished still fires (the finally), no pending-task noise on server exit."""
    session = quiet_session(HangingGraph())
    session.start()
    await asyncio.sleep(0)  # let the task enter astream
    await asyncio.wait_for(session.suspend(), timeout=5)
    assert session.ended


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
