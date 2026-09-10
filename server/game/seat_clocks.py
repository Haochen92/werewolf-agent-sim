"""The clocks that stop one silent player from stalling a game other people are in.

When the game asks a human seat a question, that seat has 120 seconds to answer. If the
seat has no browser connected, it gets 30 seconds instead, which is enough to survive a
dropped connection. Each waiting seat runs a single clock set to whichever of the two
comes first, restarted rather than stacked as that seat's connection goes and returns.

When the clock runs out, the question is not simply skipped. If any human is connected,
that seat's turn is played by the seat's own AI so the rest of the table can carry on. If
nobody is connected, the game parks: it just waits, nothing is spent, and the question is
still there when someone comes back.

Only games with more than one human seat use these clocks; a solo player may think for as
long as they like. This file holds the timing and nothing else. GameSession lends it the
two things it cannot work out itself: who is connected, and how to hand a turn to an AI.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Callable

from Agents.schemas.human_player import HumanTurnRequest

logger = logging.getLogger(__name__)

# How long a game with more than one human waits for a connected seat to answer before
# the turn goes to that seat's AI. Solo games never use it: nobody else is waiting.
AFK_TIMEOUT_SECONDS = 120.0
# How long a waiting seat with no connection open has to come back. Measured 2026-09-09:
# a closed connection is noticed within 1-10 s, so 30 s still leaves room for a retry.
ABSENCE_GRACE_SECONDS = 30.0


def _now() -> datetime:
    return datetime.now(timezone.utc)


class SeatClocks:
    """One game's clocks, one for each seat that has been asked something.

    ``pending`` is the session's own dictionary of unanswered questions, shared by
    reference so both sides always see the same one. ``deadlines`` is the moment each
    seat's clock runs out, which is also the countdown the players are shown."""

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
        """A new question was asked: the seat's 120 seconds start now and do not move."""
        if not self._enabled:
            return
        seat = request.player_id
        self._thinking[seat] = _now() + timedelta(seconds=AFK_TIMEOUT_SECONDS)
        self.reschedule(seat, request)

    def reschedule(self, seat: str, request: HumanTurnRequest) -> None:
        """Start, or restart, this seat's single clock at whichever comes first: the 120
        seconds it was given to think, or 30 seconds from now when the seat has no
        connection open. Being away can only shorten the wait, never lengthen it: a seat
        that reconnects after 29 seconds still has 91 seconds to think. Called when the
        question is asked, when the seat's connection drops, and when it comes back. The
        deadline the players are shown is the one actually in use."""
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
        """Wait until the deadline, then decide what becomes of this question.

        What is checked is the question, not the seat. If the seat answered at 119 seconds
        and was asked something new half a second later, it is waiting again, but on a
        different question with a clock of its own, so this clock must stop quietly.
        Nothing is awaited between that check and the handover, so an answer arriving at
        the same moment either wins, in which case this clock finds the question gone, or
        arrives second and is refused the way a double-click is.

        If any human seat is connected, this one turn is played by the seat's own AI. If
        nobody is connected the game parks, which simply means nothing happens: the
        question stays unanswered, the engine idles, no tokens are spent, and the first
        player to reconnect starts the clocks again."""
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
        """Stop every clock; the game is over."""
        for task in list(self._tasks.values()):
            task.cancel()

    def is_running(self, seat: str) -> bool:
        return seat in self._tasks

    # -- presence transitions -------------------------------------------------------------

    def on_seat_returned(self, seat: str) -> None:
        """A human seat connected again. If that seat was running on the short absence
        window, it goes back to its full thinking time, and if the game was parked the
        returning seat's own question starts a fresh 120 seconds, since nobody was kept
        waiting while it was parked. Every other seat still waiting has its clock started
        again too, and when one of those runs out there is now someone connected, so that
        turn goes to the seat's AI."""
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
        """The seat's last connection closed while it still owed an answer, so its clock
        drops to the 30-second absence window: the browser may be reconnecting, or the
        player may be gone for good."""
        request = self._pending.get(seat)
        if request is not None and self.is_running(seat):
            self.reschedule(seat, request)
