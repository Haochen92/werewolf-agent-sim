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

from Agents.board_clocks import criticality_from_counts
from Agents.game_config import GameConfig

# Town wins by removing BOTH threat factions (the wolves and the serial killer),
# so a town vote that lands on either role is the correct decision.
THREAT_ROLES = frozenset({"wolf", "serial_killer"})

# Town's high-value roles — what a deceiver night-kill most wants to remove and
# what the A/B's wolf "power_targeting" proxy measures.
POWER_ROLES = frozenset({"investigator", "healer", "vigilante"})

# Town roles whose day_vote the replay harness can regenerate today — i.e. the
# roles present in evaluation.src.replay.turn_action.ACTION_SPECS for
# ("<role>", "day_vote"). vigilante is town but now also has a vote spec (see
# REPLAYABLE_DECEIVER_ROLES note); kept off this town-default set only because the
# default screen is town-lensed and vigilante is opted in explicitly by --roles.
REPLAYABLE_TOWN_ROLES = frozenset({"villager", "healer", "investigator"})

# Roles scored with the DECEIVER lens (a good day-vote INDUCES a town mislynch, the
# mirror of town's hit_threat). wolf + serial_killer both have day_vote ACTION_SPECS;
# vigilante is town-lensed (it is a town power role) even though it now has a spec too.
REPLAYABLE_DECEIVER_ROLES = frozenset({"wolf", "serial_killer"})


def wolf_vote_is_good(outcome: "VoteOutcome") -> bool:
    """Deceiver-lens read on a day vote: a wolf/SK advances its faction by driving a
    town MISLYNCH (voting an actual town player off), so ``is_town_mislynch`` — NOT the
    town's ``hit_threat`` — is the "correct" deceiver vote. Voting a fellow threat is
    self-sabotage (neither), abstaining is neutral. Named distinctly so a deceiver run
    never silently reuses town hit_threat semantics."""
    return outcome.is_town_mislynch


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


def query_criticality(
    surviving_players: Iterable[str], roles: Mapping[str, str]
) -> tuple[int, int, bool]:
    """Deterministic query criticality from the frozen board: ``(players_alive,
    distance_to_parity, is_swing)``, mirroring ``determine_winner``'s three terminal
    clocks (Agents.nodes.orchestrator) — eliminations until each faction's win:

    - wolf clock = (town + SK) − wolves. Counting the SK among the bodies is exact,
      not an approximation: wolves cannot win while the SK lives, so its death is one
      of the eliminations the clock counts.
    - SK clock = (town + wolves) − 1 (night-immune + a guaranteed kill ⇒ wins at one
      other survivor); absent when no SK is alive.
    - town clock = wolves + SK (town wins when both threat factions are gone).

    ``distance_to_parity`` = min of the two EVIL clocks — matching the model-facing
    field description ("the leading remaining evil faction") the dimension audit grades
    fills against. ``is_swing`` = min of ALL THREE clocks <= 1: faction-neutral "the
    game can end within one elimination, in some direction" (2026-07-11 ruling,
    evidence/credit/report.md §6; both were wolf-only before, which graded correct
    SK-endgame fills as wrong and under-weighted deceiver do-or-die boards near a town
    win). Computed here from the true role map, but the values are PUBLIC-derivable
    (fixed cast + role-revealing deaths -> the census gives the same counts), so the
    live memory query states them as known board facts; for these dims the dimension
    audit now checks fill WIRING, not an epistemic gap.

    The clock arithmetic lives in ``Agents.board_clocks`` (shared with the live fill)
    so the audit, the screens, and the live query can never disagree on the definition.
    ``criticality_screen`` re-imports this wrapper.
    """
    alive = list(surviving_players)
    wolves = sum(1 for p in alive if roles.get(p) == "wolf")
    sk = sum(1 for p in alive if roles.get(p) == "serial_killer")
    return criticality_from_counts(wolves, sk, len(alive) - wolves - sk)


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
