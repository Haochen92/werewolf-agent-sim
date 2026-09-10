"""The pacing bars: ephemeral phase_progress snapshots from PUBLIC knowledge only.

Night and the day vote deliberately withhold their events (secrecy tiers, blind voting),
so a live viewer needs proof of motion without proof of content. Denominators come from
the publicly derivable alive-role census, never the real fan-out; padded 20–30 s
completions make a non-actor (a vigilante out of bullets) indistinguishable from a slow
one. Extracted from GameSession, which feeds it public events and part-level ticks.
"""

from __future__ import annotations

import asyncio
import random
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
    """Ephemeral phase_progress snapshots from PUBLIC knowledge only.

    The two bars exist because night and the day vote deliberately withhold their events
    (secrecy tiers, blind voting) — a live viewer needs proof of motion without proof of
    content. Denominators come from the publicly-derivable alive-role census (fixed cast
    minus announced deaths), NEVER the real fan-out. Certain roles, such as vigilante, would
    not have a night phase if their bullets are used up. Showing the real counter would
    leak information to other roles, hence a pseudo role counter will represent them. 
    Night units all complete on a minimal padded 20-30s so that pseudo counters will not complete
    instantly, which is another role leak. 
    Runs entirely on the event loop."""

    def __init__(self, publish: Callable[[ev.PhaseProgress], None]) -> None:
        # The one capability the tracker gets: emit a snapshot (GameSession.publish_pacing).
        # A callback, not the session object — the signature IS the coupling contract.
        self._publish = publish
        # Game-lifetime facts.
        self._public_alive: dict[str, int] = {}  # role -> alive count the AUDIENCE can derive
        self._day = 1
        # Per-stage scratch: one bar's worth of state, wiped together by _reset_stage().
        self._stage: str | None = None  # "night" | "day_vote" | None = no bar showing
        self._stage_total = 0
        self._completed_units: set[str] = set()  # night numerator; a set so double marks no-op
        self._ballots = 0  # vote numerator; anonymous ticks, so a plain counter
        self._padding_timers: list[asyncio.TimerHandle] = []

    # -- public-event feed ----------------------------------------------------------------

    def on_event(self, event: ev.DurableEvent) -> None:
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

    # -- part-level ticks (via GameSession) -----------------------------------------------

    def on_branch_done(self, unit: str) -> None:
        self._complete_unit(unit)

    def on_ballot(self) -> None:
        if self._stage == "day_vote":
            self._ballots = min(self._ballots + 1, self._stage_total)
            self._publish_snapshot(self._ballots)

    # -- internals ------------------------------------------------------------------------

    def _start_night(self) -> None:
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
        self._reset_stage()
        self._stage, self._stage_total, self._ballots = (
            "day_vote", sum(self._public_alive.values()), 0)
        self._publish_snapshot(0)

    def _complete_unit(self, unit: str) -> None:
        """Idempotent: the real branch tick and the padding timer both land here."""
        if self._stage != "night" or unit in self._completed_units:
            return
        self._completed_units.add(unit)
        self._publish_snapshot(len(self._completed_units))

    def _publish_snapshot(self, done: int) -> None:
        """Absolute done/total frames, never increments — a late joiner needs one full frame."""
        if self._stage is None or self._stage_total == 0:
            return
        self._publish(ev.PhaseProgress(
            day=self._day, stage=self._stage, done=done, total=self._stage_total
        ))

    def _finish_stage(self) -> None:
        """The stage's result went public: leave the bar complete, then reset."""
        if self._stage is not None:
            self._publish_snapshot(
                self._stage_total if self._stage == "night" else self._ballots)
        self._reset_stage()

    def _reset_stage(self) -> None:
        for timer in self._padding_timers:
            timer.cancel()  # a dawn that beats the timers must not leave callbacks pending
        self._padding_timers.clear()
        self._stage, self._stage_total, self._completed_units, self._ballots = None, 0, set(), 0
