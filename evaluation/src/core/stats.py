"""Statistical tests for batch win-rate comparisons.

Thin wrappers around scipy so evidence reports cite computed numbers instead of
eyeballed ones. McNemar/Wilcoxon for the paired A/B landed here with that batch
(2026-06-11).
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


def pearson(x: list[float], y: list[float]) -> tuple[float, float]:
    """Pearson r between two dense vectors. Degenerate (constant either side, n<3)
    returns (nan, nan) rather than raising — the small per-proxy sub-Ns make that common."""
    if len(x) != len(y) or len(x) < 3 or len(set(x)) < 2 or len(set(y)) < 2:
        return (float("nan"), float("nan"))
    result = stats.pearsonr(x, y)
    return (result.statistic, result.pvalue)


def partial_correlation(
    x: list[float], y: list[float], controls: list[list[float]]
) -> tuple[float, float, int]:
    """Partial correlation of x and y controlling for one or more covariates.

    Residualizes x and y on the controls (via OLS with an intercept) and correlates
    the residuals; the t-test uses df = n - k - 2 (k = number of controls), so the
    p-value already pays for each thing partialled out. Used to ask whether a proxy's
    win-correlation survives conditioning on an environmental dominator (e.g. sk_lynched)
    or a confound (game_length). Returns (r, p, n); degenerate inputs return (nan, nan, n).
    """
    import numpy as np

    n = len(x)
    if n != len(y) or any(len(c) != n for c in controls):
        raise ValueError("x, y and every control must be equal-length")
    k = len(controls)
    if n < k + 3 or len(set(x)) < 2 or len(set(y)) < 2:
        return (float("nan"), float("nan"), n)
    design = np.column_stack([np.ones(n)] + [np.asarray(c, float) for c in controls])
    xa = np.asarray(x, float)
    ya = np.asarray(y, float)
    rx = xa - design @ np.linalg.lstsq(design, xa, rcond=None)[0]
    ry = ya - design @ np.linalg.lstsq(design, ya, rcond=None)[0]
    if np.allclose(rx, rx[0]) or np.allclose(ry, ry[0]):
        return (float("nan"), float("nan"), n)
    r = float(np.corrcoef(rx, ry)[0, 1])
    df = n - k - 2
    if df <= 0 or abs(r) >= 1.0:
        return (r, float("nan"), n)
    t = r * (df ** 0.5) / ((1 - r * r) ** 0.5)
    p = float(2 * stats.t.sf(abs(t), df))
    return (r, p, n)


@dataclass
class McNemarResult:
    """Paired binary outcomes (off vs on, one pair per game) — exact McNemar."""

    n_pairs: int
    off_rate: float
    on_rate: float
    b_off_only: int  # off won, on lost
    c_on_only: int  # on won, off lost
    p_value: float

    def row(self, label: str = "arm") -> str:
        return (
            f"{label}: off {self.off_rate:.1%} -> on {self.on_rate:.1%} "
            f"(b={self.b_off_only}, c={self.c_on_only}, n={self.n_pairs}) — "
            f"McNemar p={self.p_value:.4f}"
        )


def mcnemar_exact(off: list[int], on: list[int]) -> McNemarResult:
    """Exact McNemar test on paired binary outcomes (0/1), one pair per game.

    Only discordant pairs carry signal — b (off-only win) and c (on-only win); the
    p-value is the exact two-sided binomial of min(b, c) over b + c at 0.5. The
    pairing controls the shared per-game variance (role draw), so this beats an
    unpaired Fisher test at the same N.
    """
    if len(off) != len(on):
        raise ValueError("off and on must be equal-length paired sequences")
    b = sum(1 for o, n in zip(off, on) if o == 1 and n == 0)
    c = sum(1 for o, n in zip(off, on) if o == 0 and n == 1)
    p = stats.binomtest(min(b, c), b + c, 0.5).pvalue if (b + c) else 1.0
    n = len(off)
    return McNemarResult(
        n_pairs=n,
        off_rate=sum(off) / n if n else 0.0,
        on_rate=sum(on) / n if n else 0.0,
        b_off_only=b,
        c_on_only=c,
        p_value=p,
    )


def wilcoxon_paired(off: list[float], on: list[float]) -> tuple[float, float]:
    """Wilcoxon signed-rank on paired dense values (a proxy off vs on per game).

    Returns (statistic, p). Degenerate inputs (length mismatch, <1 pair, or all
    differences zero) return (nan, nan) rather than raising.
    """
    if len(off) != len(on) or len(off) < 1 or all(o == n for o, n in zip(off, on)):
        return (float("nan"), float("nan"))
    try:
        result = stats.wilcoxon(on, off)
    except ValueError:
        return (float("nan"), float("nan"))
    return (result.statistic, result.pvalue)
