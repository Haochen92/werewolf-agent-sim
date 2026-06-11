"""Statistical tests for batch win-rate comparisons.

Thin wrappers around scipy so evidence reports cite computed numbers instead of
eyeballed ones. McNemar/Wilcoxon for the paired A/B land here when that batch runs.
"""

from __future__ import annotations

from dataclasses import dataclass

from scipy import stats


@dataclass
class ProportionComparison:
    """Two independent win-rate arms compared with Fisher's exact test."""

    wins_a: int
    n_a: int
    wins_b: int
    n_b: int
    rate_a: float
    rate_b: float
    ci_a: tuple[float, float]
    ci_b: tuple[float, float]
    fisher_p: float

    def row(self, label_a: str = "A", label_b: str = "B") -> str:
        def cell(rate: float, wins: int, n: int, ci: tuple[float, float]) -> str:
            return f"{rate:.1%} ({wins}/{n}) [{ci[0]:.1%}, {ci[1]:.1%}]"

        return (
            f"{label_a}: {cell(self.rate_a, self.wins_a, self.n_a, self.ci_a)} vs "
            f"{label_b}: {cell(self.rate_b, self.wins_b, self.n_b, self.ci_b)} — "
            f"Fisher p={self.fisher_p:.4f}"
        )


def binomial_ci(wins: int, n: int, confidence: float = 0.95) -> tuple[float, float]:
    """Exact (Clopper–Pearson) confidence interval for a win proportion."""
    ci = stats.binomtest(wins, n).proportion_ci(confidence)
    return (ci.low, ci.high)


def compare_proportions(wins_a: int, n_a: int, wins_b: int, n_b: int) -> ProportionComparison:
    """Fisher's exact test on two independent arms, with per-arm exact CIs."""
    _, p = stats.fisher_exact([[wins_a, n_a - wins_a], [wins_b, n_b - wins_b]])
    return ProportionComparison(
        wins_a=wins_a,
        n_a=n_a,
        wins_b=wins_b,
        n_b=n_b,
        rate_a=wins_a / n_a,
        rate_b=wins_b / n_b,
        ci_a=binomial_ci(wins_a, n_a),
        ci_b=binomial_ci(wins_b, n_b),
        fisher_p=p,
    )


def point_biserial(binary: list[int], values: list[float]) -> tuple[float, float]:
    """Correlation between a binary outcome (e.g. faction win) and a dense proxy.

    Returns (r, p). Degenerate inputs (constant on either side) return (nan, nan)
    rather than raising — small per-proxy sub-Ns make that common.
    """
    if len(binary) < 3 or len(set(binary)) < 2 or len(set(values)) < 2:
        return (float("nan"), float("nan"))
    result = stats.pointbiserialr(binary, values)
    return (result.statistic, result.pvalue)
