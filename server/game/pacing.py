"""The progress bars for the stages of the game a viewer may not watch.

Some stages of the game have several players act in parallel, each unable to see the
others' progress. A player who finishes their turn early has no idea how much longer to
wait for the rest. The PacingTracker here draws a progress bar for such stages: it ticks
when a player finishes and shows how many are still on their turn, "3 of 5 done", without
revealing anything about what is being done. Today that is the night (secret actions,
revealed at dawn) and the day vote (sealed ballots, revealed at the tally). A future
stage where players act in parallel and out of each other's sight can use the same bar.

The bar must not leak what the silence protects. Each leak has its own device:
  - Which roles are alive, and which still have uses left. The total is the number of
    publicly alive players, one unit per living seat, every night, whether or not that
    seat acts tonight: a spent vigilante, a necromancer on night 1, a speculator that has
    already picked and a seat with no night action all count as one. It comes from the
    public roster (the seats at the start, then each survivor list announced after a
    death), never from the engine's real actor list, and not from the role census
    either, which cannot place a concealed body and so would still count it alive.
  - Which seats acted. Most units never tick, so a timer completes every unit 20 to 30
    seconds in, and a padded finish looks like a slow real one. A real finish only adds
    one to the count; it names no unit, and the count stops at the total, so real ticks
    and timers together never overshoot.
  - The size of the pack. The pack finishing is one tick, however many wolves.
  - Who has voted. The vote bar is an anonymous count against the same roster total.

What the bar still shows: before the first timer fires, every tick is a real one, so the
count in those first 20 seconds is how many night turns have already finished, and so a
floor on how many seats act tonight. The bar showed the same before this design (a real
turn ticked the moment it finished then too). It is accepted, not hidden: hiding it would
mean holding every real tick back until the timers, which makes the bar a clock.
"""

from __future__ import annotations

import asyncio
import random
from collections.abc import Iterable
from typing import Callable

from server.schemas import events as ev

# The solo night roles of the pool; each one's turn is a root node of its own.
_SOLO_NIGHT_ROLES = (
    "investigator", "sentinel", "trailseer", "vigilante", "sigilist", "healer",
    "serial_killer", "necromancer", "speculator", "fortune_teller",
)
# Root-level night nodes whose finish adds one to the night bar; the pack is one node.
BRANCH_UNITS = frozenset(
    {f"{role.upper()}_NIGHT_PHASE" for role in _SOLO_NIGHT_ROLES} | {"PACK_NIGHT_PHASE"})
_PAD_SECONDS = (20.0, 30.0)


class PacingTracker:
    """One game's tracker, fed by the session for the length of the game.

    Inputs, all from GameSession:
      publish     the one thing the tracker can do: send a PhaseProgress frame to every
                  viewer. A function, not the session object, so the tracker can reach
                  nothing else and a test can pass a list's append. Frames are absolute
                  done/total snapshots, never increments, on the separate pacing channel:
                  not stored, not replayed.
      on_event    every durable event as it is delivered. Five types matter: game_started
                  and roster_update set the alive count; phase_change opens the night or
                  vote bar or clears one; night_result closes the night bar; vote_cast,
                  which only ever arrives as the post-tally batch, closes the vote bar
                  (the live ticks come from on_chunk).
      on_chunk    the source graph and node names of every stream chunk. A night turn
                  finishing at the root adds one to the night bar; a vote node finishing
                  in the day phase adds one ballot.

    Attributes, by job.
      _alive          how many players are publicly alive; the total of both bars.
      _day            stamped on every frame; from the last phase_change.
    One bar's worth of scratch, wiped together by _reset_stage():
      _stage            "night" | "day_vote" | None (no bar showing).
      _stage_total      the denominator.
      _night_done       night numerator; real ticks and timers both add one, capped at
                        the total.
      _ballots          vote numerator; anonymous ticks, so a plain counter.
      _padding_timers   the night timers, cancelled when a stage ends before they fire.
      _last_frame       the frame most recently published, or None with no bar showing;
                        what a viewer who connects mid-stage is handed first.
    Everything runs on the event loop."""

    def __init__(self, publish: Callable[[ev.PhaseProgress], None]) -> None:
        self._publish = publish
        self._alive = 0
        self._day = 1
        self._stage: str | None = None
        self._stage_total = 0
        self._night_done = 0
        self._ballots = 0
        self._padding_timers: list[asyncio.TimerHandle] = []
        self._last_frame: ev.PhaseProgress | None = None

    @property
    def current_frame(self) -> ev.PhaseProgress | None:
        """The bar as it stands, for a viewer joining mid-stage; None when none is showing."""
        return self._last_frame

    # -- public-event feed ----------------------------------------------------------------

    def on_event(self, event: ev.DurableEvent) -> None:
        """Take one delivered event. Five types move the alive count or a bar (see the
        class docstring); every other type is ignored. Publishes a frame when a bar opens
        or closes."""
        if event.type == "game_started":
            self._alive = len(event.seats)
        elif event.type == "roster_update":
            # Public, after every resolution with a death; counts a concealed body too.
            self._alive = len(event.surviving_players)
        elif event.type == "night_result":
            self._finish_stage()  # dawn: force the night bar full, whatever the timers did
        elif event.type == "phase_change":
            self._day = event.day
            if event.phase == "night":
                self._start_night()
            elif event.phase == "voting":
                self._start_voting()
            else:
                self._reset_stage()
        elif event.type == "vote_cast":
            self._finish_stage()  # result announced: the vote bar is over

    # -- chunk-level ticks (via GameSession) -----------------------------------------------

    def on_chunk(self, scope: str, nodes: Iterable[str]) -> None:
        """Take the source graph and node names of one stream chunk, contents unseen. A
        night turn finishing at the root adds one to the night bar; a vote node finishing
        inside the day phase adds one ballot. Anything else is ignored."""
        for node in nodes:
            if scope == "root" and node in BRANCH_UNITS:
                self.on_branch_done()
            elif scope == "DAY_PHASE" and node in ("vote", "vote_human"):
                self.on_ballot()

    def on_branch_done(self) -> None:
        """Count one finished night turn (a solo role's or the pack's), capped at the
        total. It names no unit. No-op outside the night bar."""
        self._complete_unit()

    def on_ballot(self) -> None:
        """Count one anonymous ballot, capped at the bar's total, and publish. No-op
        outside the vote bar."""
        if self._stage == "day_vote":
            self._ballots = min(self._ballots + 1, self._stage_total)
            self._publish_snapshot(self._ballots)

    # -- internals ------------------------------------------------------------------------

    def _start_night(self) -> None:
        """Open the night bar: one unit per publicly alive player, whether or not that
        seat acts tonight. Publishes 0/total and arms a padding timer per unit."""
        self._reset_stage()
        self._stage, self._stage_total, self._night_done = "night", self._alive, 0
        self._publish_snapshot(0)
        # Padding timers do two jobs: complete the units that never tick (most seats, a
        # spent role), and make a padded completion indistinguishable from a real slow one.
        loop = asyncio.get_running_loop()
        for _ in range(self._stage_total):
            self._padding_timers.append(
                loop.call_later(random.uniform(*_PAD_SECONDS), self._complete_unit))

    def _start_voting(self) -> None:
        """Open the vote bar with every publicly alive player as its total. Publishes
        0/total."""
        self._reset_stage()
        self._stage, self._stage_total, self._ballots = "day_vote", self._alive, 0
        self._publish_snapshot(0)

    def _complete_unit(self) -> None:
        """Add one to the night count and publish it. Real ticks and padding timers both
        land here; once the count reaches the total, further ones are no-ops."""
        if self._stage != "night" or self._night_done >= self._stage_total:
            return
        self._night_done += 1
        self._publish_snapshot(self._night_done)

    def _publish_snapshot(self, done: int) -> None:
        """Send one absolute done/total frame for the current bar. Nothing is sent when
        no bar is showing or its total is zero."""
        if self._stage is None or self._stage_total == 0:
            return
        frame = ev.PhaseProgress(
            day=self._day, stage=self._stage, done=done, total=self._stage_total)
        self._last_frame = frame
        self._publish(frame)

    def _finish_stage(self) -> None:
        """Close the bar because its result went public: publish it full (night) or at
        its count (vote), then clear the stage."""
        if self._stage is not None:
            self._publish_snapshot(
                self._stage_total if self._stage == "night" else self._ballots)
        self._reset_stage()

    def _reset_stage(self) -> None:
        """Clear the bar without publishing: cancel any padding timers, wipe the scratch."""
        for timer in self._padding_timers:
            timer.cancel()  # a dawn that beats the timers must not leave callbacks pending
        self._padding_timers.clear()
        self._stage, self._stage_total, self._night_done, self._ballots = None, 0, 0, 0
        self._last_frame = None
