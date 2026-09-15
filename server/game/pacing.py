"""The progress bars for the stages of the game a viewer may not watch.

Some stages of the game have several players act in parallel, each unable to see the
others' progress. A player who finishes their turn early has no idea how much longer to
wait for the rest. The PacingTracker here draws a progress bar for such stages: it ticks
when a player finishes and shows how many are still on their turn, "3 of 5 done", without
revealing anything about what is being done. Today that is the night (secret actions,
revealed at dawn) and the day vote (sealed ballots, revealed at the tally). A future
stage where players act in parallel and out of each other's sight can use the same bar.

The bar must not leak what the silence protects. Each leak has its own device:
  - Which special roles are alive. The denominator is the public census, the fixed cast
    minus announced deaths, never the engine's real actor list, which would show for
    instance that the serial killer survived a silenced vigilante shot.
  - Whether the vigilante has bullets left. A spent vigilante has no night phase and
    would never finish, so a timer also finishes every night unit 20 to 30 seconds in,
    and a padded finish looks like a slow real one. Real units finish by the same timer
    too: the bar is a pace, not a report.
  - The size of the pack. The wolves are one unit, however many there are.
  - Who has voted. The vote bar is an anonymous count.
"""

from __future__ import annotations

import asyncio
import random
from collections.abc import Iterable
from typing import Callable

from server.schemas import events as ev

_SPECIAL_UNITS = ("healer", "investigator", "serial_killer", "vigilante")
# Root-level night branch nodes → the public unit each one completes.
BRANCH_UNITS = {
    "WOLF_NIGHT_PHASE": "wolves",
    "HEALER_NIGHT_PHASE": "healer",
    "INVESTIGATOR_NIGHT_PHASE": "investigator",
    "SERIAL_KILLER_NIGHT_PHASE": "serial_killer",
    "VIGILANTE_NIGHT_PHASE": "vigilante",
}
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
                  sets the census; lynch_result and night_result lower it; phase_change
                  opens the night or vote bar or clears one; night_result closes the
                  night bar; vote_cast, which only ever arrives as the post-tally batch,
                  closes the vote bar (the live ticks come from on_chunk).
      on_chunk    the source graph and node names of every stream chunk. A night wrapper
                  finishing at the root marks that unit done; a vote node finishing in
                  the day phase adds one ballot.

    Attributes, by job.
      _public_alive   role -> alive count the audience can derive; the denominators.
      _day            stamped on every frame; from the last phase_change.
    One bar's worth of scratch, wiped together by _reset_stage():
      _stage            "night" | "day_vote" | None (no bar showing).
      _stage_total      the denominator.
      _completed_units  night numerator; a set, so a double mark is a no-op.
      _ballots          vote numerator; anonymous ticks, so a plain counter.
      _padding_timers   the night timers, cancelled when a stage ends before they fire.
      _last_frame       the frame most recently published, or None with no bar showing;
                        what a viewer who connects mid-stage is handed first.
    Everything runs on the event loop."""

    def __init__(self, publish: Callable[[ev.PhaseProgress], None]) -> None:
        self._publish = publish
        self._public_alive: dict[str, int] = {}
        self._day = 1
        self._stage: str | None = None
        self._stage_total = 0
        self._completed_units: set[str] = set()
        self._ballots = 0
        self._padding_timers: list[asyncio.TimerHandle] = []
        self._last_frame: ev.PhaseProgress | None = None

    @property
    def current_frame(self) -> ev.PhaseProgress | None:
        """The bar as it stands, for a viewer joining mid-stage; None when none is showing."""
        return self._last_frame

    # -- public-event feed ----------------------------------------------------------------

    def on_event(self, event: ev.DurableEvent) -> None:
        """Take one delivered event. Five types move the census or a bar (see the class
        docstring); every other type is ignored. Publishes a frame when a bar opens or
        closes."""
        if event.type == "game_started":
            self._public_alive = dict(event.cast_role_counts)
        elif event.type == "lynch_result" and event.role:
            self._public_alive[event.role] = max(0, self._public_alive.get(event.role, 0) - 1)
        elif event.type == "night_result":
            for death in event.deaths:
                self._public_alive[death.role] = max(0, self._public_alive.get(death.role, 0) - 1)
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
        night wrapper finishing at the root marks that unit done; a vote node finishing
        inside the day phase adds one ballot. Anything else is ignored."""
        for node in nodes:
            if scope == "root" and node in BRANCH_UNITS:
                self.on_branch_done(BRANCH_UNITS[node])
            elif scope == "DAY_PHASE" and node in ("vote", "vote_human"):
                self.on_ballot()

    def on_branch_done(self, unit: str) -> None:
        """Mark a night unit ("wolves" or a special role) done. No-op outside the night
        bar or if already marked."""
        self._complete_unit(unit)

    def on_ballot(self) -> None:
        """Count one anonymous ballot, capped at the bar's total, and publish. No-op
        outside the vote bar."""
        if self._stage == "day_vote":
            self._ballots = min(self._ballots + 1, self._stage_total)
            self._publish_snapshot(self._ballots)

    # -- internals ------------------------------------------------------------------------

    def _start_night(self) -> None:
        """Open the night bar: one unit per special role the census says is alive, plus
        the pack if any wolf is. Publishes 0/total and arms a padding timer per unit."""
        self._reset_stage()
        units = [u for u in _SPECIAL_UNITS if self._public_alive.get(u, 0) > 0]
        if self._public_alive.get("wolf", 0) > 0:
            units.append("wolves")  # the pack is one unit: per-wolf ticks would size the pack
        self._stage, self._stage_total, self._completed_units = "night", len(units), set()
        self._publish_snapshot(0)
        # Padding timers do two jobs: complete units that never tick (zero-bullet
        # vigilante), and make a padded completion indistinguishable from a real slow one.
        loop = asyncio.get_running_loop()
        for unit in units:
            self._padding_timers.append(
                loop.call_later(random.uniform(*_PAD_SECONDS), self._complete_unit, unit)
            )

    def _start_voting(self) -> None:
        """Open the vote bar with every publicly alive player as its total. Publishes
        0/total."""
        self._reset_stage()
        self._stage, self._stage_total, self._ballots = (
            "day_vote", sum(self._public_alive.values()), 0)
        self._publish_snapshot(0)

    def _complete_unit(self, unit: str) -> None:
        """Mark one night unit done and publish the new count. The real tick and the
        padding timer both land here, so a second mark is a no-op."""
        if self._stage != "night" or unit in self._completed_units:
            return
        self._completed_units.add(unit)
        self._publish_snapshot(len(self._completed_units))

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
        self._stage, self._stage_total, self._completed_units, self._ballots = None, 0, set(), 0
        self._last_frame = None
