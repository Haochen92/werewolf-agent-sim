"""The AFK clocks of one game — two clocks, one deadline, and the table's decision at
expiry (seat_continuity.md §4–§5). Extracted from GameSession, which keeps the graph,
the log, and the viewers; this class keeps only time.

Per parked seat there is one stopwatch, rescheduled and never stacked, running to the
EFFECTIVE deadline: the thinking deadline (absolute from the ask) or the absence grace
when the seat has no open stream — whichever is earlier. When it rings, the presence
test decides: someone connected → delegate this one turn; nobody → park, which is
simply not delegating. The session supplies presence and the delegate action as
callables, so this class never touches a stream or the graph.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Callable

from Agents.schemas.human_player import HumanTurnRequest

logger = logging.getLogger(__name__)

# The thinking window: how long a MULTI-human game waits on a connected seat before the
# turn is delegated to the seat's agent (one absent player must not hold the table
# hostage). Solo games never arm it — the lone human may think forever, nobody is waiting.
AFK_TIMEOUT_SECONDS = 120.0
# The absence grace: a parked seat with NO open stream gets this long to reconnect before
# its clock fires — enough for a browser retry plus the heartbeat lag, short enough that one
# closed tab does not cost the table two minutes on every one of that seat's turns. It never
# extends the thinking deadline. Measured 2026-09-09: detection lag is 1–10 s, bounded by
# the 15 s heartbeat — 30 s leaves ~10 s of margin.
ABSENCE_GRACE_SECONDS = 30.0


def _now() -> datetime:
    return datetime.now(timezone.utc)


class SeatClocks:
    """One game's stopwatches. ``pending`` is the session's live registry of parked
    questions (shared by reference, never rebound); ``deadlines`` is the effective
    deadline per seat, served to clients as their countdown."""

    def __init__(self, game_id: str, pending: dict[str, HumanTurnRequest], *,
                 enabled: bool,
                 seat_present: Callable[[str], bool],
                 anyone_present: Callable[[], bool],
                 delegate: Callable[[str], None]) -> None:
        self._game_id = game_id
        self._pending = pending
        self._enabled = enabled  # multi-human tables only
        self._seat_present = seat_present
        self._anyone_present = anyone_present
        self._delegate = delegate
        self.deadlines: dict[str, str] = {}
        self._thinking: dict[str, datetime] = {}
        self._tasks: dict[str, asyncio.Task] = {}

    # -- the clocks -----------------------------------------------------------------------

    def arm(self, request: HumanTurnRequest) -> None:
        """A new question: the thinking deadline is absolute from the ask."""
        if not self._enabled:
            return
        seat = request.player_id
        self._thinking[seat] = _now() + timedelta(seconds=AFK_TIMEOUT_SECONDS)
        self.reschedule(seat, request)

    def reschedule(self, seat: str, request: HumanTurnRequest) -> None:
        """(Re)start the seat's one stopwatch at its EFFECTIVE deadline: the thinking
        deadline, or the absence grace when the seat has no open stream — whichever is
        earlier. Absence never extends the clock (back at 29 s means 91 s left). Called
        on the ask, when the seat's stream drops, and when a stream returns (which lifts
        a grace back to the thinking deadline). The served deadline is the effective
        one, so the countdown the table sees is the truth."""
        deadline = self._thinking[seat]
        if not self._seat_present(seat):
            deadline = min(deadline, _now() + timedelta(seconds=ABSENCE_GRACE_SECONDS))
        self.deadlines[seat] = deadline.isoformat()
        stale = self._tasks.pop(seat, None)
        if stale is not None:
            stale.cancel()
        task = asyncio.get_running_loop().create_task(
            self._expire(seat, request, deadline), name=f"afk-{self._game_id}-{seat}")
        self._tasks[seat] = task
        task.add_done_callback(
            lambda t: self._tasks.pop(seat, None) if self._tasks.get(seat) is t else None)

    async def _expire(self, seat: str, request: HumanTurnRequest,
                      deadline: datetime) -> None:
        """The stopwatch: sleep to the deadline, then let the TABLE decide this question.

        The expiry check is request IDENTITY, not seat membership: if the seat answered
        at 119s and its next turn parked at 119.5s, the seat is pending again — but on a
        different question, which has its own stopwatch. This one must die quietly.
        No await sits between the check and the delegate, so a real answer racing the
        expiry either lands first (identity check fails) or second (LookupError inside
        submit_turn — the same bounce as a double-click).

        The presence test runs over every human seat: someone connected → delegate this
        one turn to the seat's agent; nobody → PARK. Parking is the absence of delegation
        — the question keeps waiting exactly as a solo game does, the graph idles, no
        tokens burn, and the first returning human stream re-arms the clocks."""
        await asyncio.sleep(max(0.0, (deadline - _now()).total_seconds()))
        if self._pending.get(seat) is not request:
            return
        if not self._anyone_present():
            self.deadlines.pop(seat, None)  # no countdown while parked
            logger.info("game %s: seat %s AFK on %s and nobody connected — parking",
                        self._game_id, seat, request.phase)
            return
        logger.info("game %s: seat %s AFK on %s — delegating the turn to its agent",
                    self._game_id, seat, request.phase)
        try:
            self._delegate(seat)
        except Exception:  # a failed default must be loud, never a vanished task error
            logger.exception("game %s: AFK delegation for %s failed", self._game_id, seat)

    def clear(self, seat: str) -> None:
        """The seat answered: its clock is over."""
        self.deadlines.pop(seat, None)
        self._thinking.pop(seat, None)
        stopwatch = self._tasks.pop(seat, None)
        if stopwatch is not None:
            stopwatch.cancel()

    def cancel_all(self) -> None:
        """Stopwatches die with the game."""
        for task in list(self._tasks.values()):
            task.cancel()

    def is_running(self, seat: str) -> bool:
        return seat in self._tasks

    # -- presence transitions -------------------------------------------------------------

    def on_seat_returned(self, seat: str) -> None:
        """A human seat's stream (re)connected. Lifts that seat's running absence grace
        back to its thinking deadline, and un-parks a parked table: the returning seat's
        own question gets a fresh thinking window (nobody waited during the park); every
        other parked seat gets the grace, after which the presence test finds someone."""
        if not self._enabled or not self._pending:
            return
        for pending_seat, request in list(self._pending.items()):
            running = self.is_running(pending_seat)
            if running and pending_seat != seat:
                continue  # someone else's return does not touch a live clock
            if not running and pending_seat == seat:
                self._thinking[seat] = _now() + timedelta(seconds=AFK_TIMEOUT_SECONDS)
            self.reschedule(pending_seat, request)

    def on_seat_left(self, seat: str) -> None:
        """The seat's last stream closed mid-question: its clock drops to the absence
        grace — the tab may be retrying, or may be gone."""
        request = self._pending.get(seat)
        if request is not None and self.is_running(seat):
            self.reschedule(seat, request)
