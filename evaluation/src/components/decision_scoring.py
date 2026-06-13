"""Mechanical, ground-truthed scoring of a frozen day-vote decision.

The objective half of the decision-replay screen: no LLM, no I/O. Vote
correctness is a pure roles lookup, and ``allow_abstain`` is reconstructed from
the game's ``day_resolutions`` exactly as the live vote router computes it
(``Agents.nodes.day.flow.fan_out_vote``: ``abstain_enabled`` AND
``no_lynch_streak < no_lynch_force_after``) — so a replayed decision can be
offered the SAME choice set as the original instead of the harness's silent
``allow_abstain=False`` default. Verdict-aware memory *adherence* is scored
separately; this module stays free and deterministic.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass

from Agents.game_config import GameConfig

# Town wins by removing BOTH threat factions (the wolves and the serial killer),
# so a town vote that lands on either role is the correct decision.
THREAT_ROLES = frozenset({"wolf", "serial_killer"})

# Town's high-value roles — what a deceiver night-kill most wants to remove and
# what the A/B's wolf "power_targeting" proxy measures.
POWER_ROLES = frozenset({"investigator", "healer", "vigilante"})

# Town roles whose day_vote the replay harness can regenerate today — i.e. the
# roles present in evaluation.src.components.application.ACTION_SPECS for
# ("<role>", "day_vote"). Vigilante/serial_killer lack a vote spec there.
REPLAYABLE_TOWN_ROLES = frozenset({"villager", "healer", "investigator"})


@dataclass(frozen=True)
class VoteOutcome:
    """The objective read on one vote, scored against the game's true roles."""

    votee: str
    votee_role: str | None
    """Ground-truth role of the target; None when abstaining or target unknown."""
    is_abstain: bool
    hit_threat: bool
    """Correct town vote: the target was a wolf or the serial killer."""
    is_town_mislynch: bool
    """The target was an actual town player (a wrong, town-costing elimination)."""


def score_vote(votee: str | None, roles: Mapping[str, str]) -> VoteOutcome:
    """Score one vote target against ground-truth roles.

    ``abstain`` (and a missing target) is neither a threat hit nor a mislynch —
    it is its own bucket, because a town agent abstaining with live threats on
    the board is a distinct failure mode from voting a townie.
    """
    is_abstain = not votee or votee == "abstain"
    votee_role = None if is_abstain else roles.get(votee)
    return VoteOutcome(
        votee=votee or "abstain",
        votee_role=votee_role,
        is_abstain=is_abstain,
        hit_threat=votee_role in THREAT_ROLES,
        is_town_mislynch=votee_role is not None and votee_role not in THREAT_ROLES,
    )


def _day_was_no_lynch(resolution: Mapping) -> bool:
    """A no-lynch day has no unique non-abstain plurality (tie / abstain plurality
    / no votes); the orchestrator marks every such day by leaving
    ``voted_player`` None (see Agents.nodes.orchestrator resolve-day)."""
    return resolution.get("voted_player") is None


def no_lynch_streak_before(day: int, day_resolutions: Iterable[Mapping]) -> int:
    """Reconstruct the runtime ``no_lynch_streak`` entering ``day``: the count of
    consecutive no-lynch days immediately before it, a lynch resetting it to 0
    (``no_lynch_streak = 0 if lynched else prev + 1``)."""
    streak = 0
    for res in sorted(day_resolutions, key=lambda r: r.get("day", 0)):
        if res.get("day", 0) >= day:
            break
        streak = streak + 1 if _day_was_no_lynch(res) else 0
    return streak


def allow_abstain_for(
    day: int,
    day_resolutions: Iterable[Mapping],
    config: GameConfig | None = None,
) -> bool:
    """Whether the abstain option was offered at ``day``'s vote — replicating
    ``fan_out_vote`` so a replayed decision is given the SAME choice set as the
    original game (the harness otherwise defaults abstain off, which would
    unfairly strip a choice the original agent had)."""
    cfg = config or GameConfig()
    streak = no_lynch_streak_before(day, list(day_resolutions))
    return cfg.abstain_enabled and streak < cfg.no_lynch_force_after


@dataclass(frozen=True)
class NightOutcome:
    """The objective read on one night target, scored against the game's roles."""

    target: str | None
    target_role: str | None
    hit_power: bool
    """Targeted a town power role (investigator/healer/vigilante) — the deceiver
    night proxy: removing town's tools is the high-value wolf/SK kill."""
    hit_threat: bool
    """Targeted a wolf or the serial killer — the good investigator/vigilante hit."""
    hit_town: bool
    """Targeted any town player."""


def score_night_target(target: str | None, roles: Mapping[str, str]) -> NightOutcome:
    """Score one night target against ground-truth roles. ``hold_fire`` / no-op
    targets (the vigilante banking a bullet) are neither power nor threat hits."""
    is_noop = target in (None, "hold_fire", "abstain")
    role = None if is_noop else roles.get(target)
    return NightOutcome(
        target=target,
        target_role=role,
        hit_power=role in POWER_ROLES,
        hit_threat=role in THREAT_ROLES,
        hit_town=role is not None and role not in THREAT_ROLES,
    )
