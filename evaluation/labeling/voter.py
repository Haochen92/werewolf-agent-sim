"""Consensus voting for multi-model label agreement.

Stateless voting functions that take per-model scores and return a
``VoteResult`` with the consensus label and confidence level.
"""
from __future__ import annotations

from collections import Counter

from evaluation.labeling.base import VoteResult
from evaluation.labeling.config import VotingConfig


def vote(
    scores: dict[str, int | str | None],
    config: VotingConfig | None = None,
) -> VoteResult:
    """Compute consensus from multiple model scores.

    Voting logic:
      - All agree → "unanimous"
      - Strict majority (> n/2) → "majority"
      - Tie with tiebreaker model in tied group → "tie_tiebreaker"
      - Unresolvable tie → "tie" (label=None)
      - No valid scores → "no_response" (label=None)
    """
    if config is None:
        config = VotingConfig()

    valid = {k: v for k, v in scores.items() if v is not None}
    if not valid:
        return VoteResult(label=None, confidence="no_response", scores=scores)

    values = list(valid.values())
    counter = Counter(values)
    most_common = counter.most_common()
    n_voters = len(valid)
    top_label, top_count = most_common[0]

    if top_count == n_voters:
        return VoteResult(label=top_label, confidence="unanimous", scores=scores)

    if top_count > n_voters / 2:
        return VoteResult(label=top_label, confidence="majority", scores=scores)

    if len(most_common) >= 2 and most_common[0][1] == most_common[1][1]:
        tb = config.tiebreaker
        if tb and tb in valid:
            tied_labels = {l for l, c in most_common if c == top_count}
            if valid[tb] in tied_labels:
                return VoteResult(
                    label=valid[tb],
                    confidence="tie_tiebreaker",
                    scores=scores,
                )
        return VoteResult(label=None, confidence="tie", scores=scores)

    return VoteResult(label=top_label, confidence="majority", scores=scores)


def agreement_stats(votes: list[VoteResult]) -> dict[str, int]:
    """Summarize a list of vote results by confidence category."""
    stats = Counter(v.confidence for v in votes)
    return dict(stats.most_common())
