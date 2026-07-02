"""Paired-statistics helper for the decision screen's discordant-pair tests."""

from __future__ import annotations

from math import comb


# NOTE: overlaps evaluation/src/core/stats.py::mcnemar_exact in intent (two-sided
# exact-binomial McNemar); kept separate here to preserve the screen's exact
# historical behavior — do NOT consolidate without a paired-output re-verify.
def mcnemar_p(b: int, c: int) -> float:
    """Two-sided exact-binomial McNemar p over the discordant pairs (b = memory
    HURT: off-correct & stored-wrong; c = memory HELPED: stored-correct &
    off-wrong). Concordant pairs carry no paired signal and are excluded."""
    m = b + c
    if m == 0:
        return 1.0
    k = min(b, c)
    tail = sum(comb(m, i) for i in range(k + 1)) / (2**m)
    return min(1.0, 2 * tail)
