"""Pure resolution rules, shared by the engine nodes and the wire translator.

The single source for the two rule sets that would otherwise exist twice — once in the
resolution nodes and once re-derived on the wire: night attack precedence (SK night-immunity
beats a heal beats a kill, immune whiffs stay silent) and the day-vote plurality
classification. Both consumers supply their own inputs; nothing here touches graph state,
so drift between the game and the wire is impossible by construction.
"""

from collections import Counter
from typing import Iterable, Literal, NamedTuple

AttackerType = Literal["wolves", "serial_killer", "vigilante"]
NightVerdict = Literal["immune", "saved", "killed"]
DayVoteOutcome = Literal["lynched", "tie", "abstain", "no_vote"]


def collect_attacks(
    wolves_target: str | None,
    serial_killer_target: str | None,
    vigilante_target: str | None,
) -> dict[str, list[AttackerType]]:
    """target -> attacker types this night (a target may be hit by more than one killer)."""
    attacks_on: dict[str, list[AttackerType]] = {}
    for target, attacker in (
        (wolves_target, "wolves"),
        (serial_killer_target, "serial_killer"),
        (vigilante_target, "vigilante"),
    ):
        if target:
            attacks_on.setdefault(target, []).append(attacker)
    return attacks_on


def resolve_attacks(
    attacks_on: dict[str, list[AttackerType]],
    healer_target: str | None,
    serial_killer_player: str | None,
) -> dict[str, NightVerdict]:
    """Verdict per attacked target. Precedence: the immune SK never dies at night (and the
    whiff is SILENT — announcing it would out the SK), a healed target is saved, else killed.
    A player attacked by multiple killers still resolves exactly once."""

    def _resolved(target: str) -> NightVerdict:
        if target == serial_killer_player:
            return "immune"
        if target == healer_target:
            return "saved"
        return "killed"

    return {target: _resolved(target) for target in attacks_on}


class DayVoteTally(NamedTuple):
    vote_counts: dict[str, int]
    """Ballot tally as counted, including any "abstain" bucket."""
    candidates: list[str]
    """Every votee sharing the top count (length > 1 = tie)."""
    lynched: str | None
    """The lynched player — set only when the unique plurality is a real player."""
    outcome: DayVoteOutcome
    """lynched / tie / abstain (abstain won the plurality) / no_vote (no ballots)."""


def tally_day_vote(votees: Iterable[str]) -> DayVoteTally:
    """Classify the day vote: a real lynch needs a unique, non-"abstain" plurality; a tie,
    an abstain plurality, or no ballots is a no-lynch day. Deterministic — day votes have
    no random tiebreak (unlike the wolf kill vote)."""
    vote_counts = Counter(votees)
    max_votes = max(vote_counts.values(), default=0)
    candidates = [player for player, votes in vote_counts.items() if votes == max_votes]
    plurality = candidates[0] if len(candidates) == 1 else None
    lynched = plurality if (plurality and plurality != "abstain") else None

    if lynched:
        outcome: DayVoteOutcome = "lynched"
    elif not vote_counts:
        outcome = "no_vote"
    elif plurality == "abstain":
        outcome = "abstain"
    else:
        outcome = "tie"
    return DayVoteTally(dict(vote_counts), candidates, lynched, outcome)
