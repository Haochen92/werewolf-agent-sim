"""The day vote's classification, shared by the engine node and the wire translator.

One implementation of the plurality rule, so the game and the wire cannot drift. (The night's
rules, which lived here too, are the night layer in ``Agents/rules/night.py`` since Phase 3.)
"""

from collections import Counter
from typing import Iterable, Literal, NamedTuple

DayVoteOutcome = Literal["lynched", "tie", "abstain", "no_vote"]


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
