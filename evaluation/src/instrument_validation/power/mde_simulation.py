"""Power / MDE gate for the compounding measurement plan (§0.1) — the standing pre-run apparatus.

QUESTION. At N games/generation x G generations, what compounding effect can the planned slope
analysis actually DETECT at 80% power (alpha 0.05)? Validity (is the de-luck ruler real?) is settled;
power is the orthogonal quantity — the only one that involves N — and the plan gates every paid
compounding run on it: "no paid run without an MDE table". The static A/B says the true effect is
plausibly only +0.1..0.2 per-game de-luck, while per-game noise is ~+-0.9 SD even on matched boards
(plan §0.1/§12b), so at the affordable N the experiment-as-designed may buy a coin flip. This script
proves and SIZES that wall for $0 before anyone pays.

METHOD ($0, deterministic, no model, no spend). Recompute the per-game de-luck decision score for
every existing whole-game record (factoring measure.py's generation_score down to the game grain via
`game_score`), pooling per corpus x arm x faction. Then, per cell (pool x faction x N x G x injected
effect): resample N games/gen i.i.d. WITH REPLACEMENT from the corpus's memory-OFF pool, inject a known
linear-in-generation effect, run the PLANNED slope test, and count detection over 2000 replicates.
Arms are treated as UNPAIRED at the game grain (pairing collapses after the first vote divergence, plan
§0.1). The effect-0 column doubles as the false-positive (alpha) check.

CORPORA (all existing, $0):
  - town_only_run1 : evidence/v7_final/runs/town_only_run1/gen{1..3}_{on,off}.jsonl  (15 games/arm)
      -> OFF town-grain is the PRIMARY pool: the pending town rerun's own noise.
  - v2_full        : evidence/v7_final/runs/v2_full/gen{1..6}_{on,off}.jsonl          (24 games/arm)
      -> OFF town-grain sensitivity (all_enabled epoch) + OFF WOLF-grain (the gated wolf arm).
  - v6ab           : batch_results/v6ab_*.jsonl                                        (180 games)
      -> the all-disabled baseline arm's town-grain = the N=90 SD sanity anchor.

INVOKE (from the repo root):
    poetry run python -m evaluation.src.instrument_validation.power.mde_simulation

No console entry, no manifest stamping — this is a standing $0 apparatus. It prints markdown tables
(pool SD preamble, primary-estimator detection grid, per-gen-Delta secondary grid, MDE lines, a
closed-form ANALYTIC cross-check (anchor cells + an effect-scaling ladder at N=4/G=6), cost lines,
limitations). The dated readout it produced lives at evidence/execution_plan/power_analysis/mde_table.md.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))  # repo root, for `evaluation.src.*`

from evaluation.src.data.sources.batch_records import read_records_file  # noqa: E402
from evaluation.src.instrument_validation.proxies.metrics_common import load_v6ab  # noqa: E402
from evaluation.src.loop.measure import game_score  # noqa: E402

SEED = 20260618
REPLICATES = 2000
N_GRID = (4, 5, 10, 20)
G_GRID = (6, 8, 10)
EFFECTS = (0.0, 0.05, 0.10, 0.15, 0.20, 0.30)  # TOTAL lift at the final generation
LADDER_EFFECTS = (0.15, 0.30, 0.45, 0.60)      # effect-scaling ladder at the v2-like N=4/G=6 config
ALPHA = 0.05
POWER_TARGET = 0.80

REPO = Path(__file__).resolve().parents[4]
V2_DIR = REPO / "evidence/v7_final/runs/v2_full"
RUN1_DIR = REPO / "evidence/v7_final/runs/town_only_run1"

# Per-game $ derived from the v2_full actual spend (games_total_usd 13.43 / 48 games), the only
# on-disk cost record for a compounding run. Source: evidence/v7_final/runs/v2_full/cost_report.json.
USD_PER_GAME = 13.43 / 48  # ~= $0.28/game (blended on+off)


# --------------------------------------------------------------------------- pools

def _pool(records: list[dict], arm: str, faction: str) -> np.ndarray:
    """Per-game mean de-luck score at one faction grain for every game with >=1 such decision."""
    out = []
    for rec in records:
        sums, ns = game_score(rec, arm)
        if ns.get(faction):
            out.append(sums[faction] / ns[faction])
    return np.asarray(out, dtype=float)


def _load_gen_arm(base: Path, gens: range, arm: str) -> list[dict]:
    recs: list[dict] = []
    for g in gens:
        f = base / f"gen{g}_{arm}.jsonl"
        if f.exists():
            recs.extend(read_records_file(f))
    return recs


def load_pools() -> dict[str, dict]:
    """corpus -> {'off': records, 'on': records}. v6ab is split by memory_config (all-False = OFF)."""
    v6ab = load_v6ab()
    v6_off = [r for r in v6ab if not any((r.get("memory_config") or {}).values())]
    v6_on = [r for r in v6ab if any((r.get("memory_config") or {}).values())]
    return {
        "town_only_run1": {"off": _load_gen_arm(RUN1_DIR, range(1, 4), "off"),
                           "on": _load_gen_arm(RUN1_DIR, range(1, 4), "on")},
        "v2_full": {"off": _load_gen_arm(V2_DIR, range(1, 7), "off"),
                    "on": _load_gen_arm(V2_DIR, range(1, 7), "on")},
        "v6ab": {"off": v6_off, "on": v6_on},
    }


# --------------------------------------------------------------------------- OLS (vectorized)

def _ols_slope_detect(x: np.ndarray, y: np.ndarray) -> np.ndarray:
    """Vectorized two-sided slope test across replicates. x: (M,) shared design; y: (reps, M).
    Returns a boolean array: p<ALPHA AND slope>0 (the planned one-directional detection)."""
    m = x.size
    xc = x - x.mean()
    sxx = float(np.dot(xc, xc))
    ybar = y.mean(axis=1, keepdims=True)
    slope = (y - ybar) @ xc / sxx                       # (reps,)
    intercept = ybar[:, 0] - slope * x.mean()
    resid = y - (intercept[:, None] + slope[:, None] * x[None, :])
    sse = np.einsum("ij,ij->i", resid, resid)
    var_slope = (sse / (m - 2)) / sxx
    with np.errstate(divide="ignore", invalid="ignore"):
        t = slope / np.sqrt(var_slope)
    p = 2.0 * stats.t.sf(np.abs(t), df=m - 2)
    return (p < ALPHA) & (slope > 0)


def detect_primary(pool: np.ndarray, n: int, g: int, total_effect: float, rng) -> float:
    """Primary estimator: regress score on gen index over ALL N*G games. Detection rate over REPLICATES.
    Injected effect is linear in generation: slope_per_gen = total_effect / (G-1)."""
    slope_gen = total_effect / (g - 1)
    gens = np.arange(g)
    x = np.repeat(gens, n).astype(float)                # (G*N,)
    draws = rng.choice(pool, size=(REPLICATES, g, n))   # (reps, G, N)
    draws += (slope_gen * gens)[None, :, None]
    y = draws.reshape(REPLICATES, g * n)
    return float(_ols_slope_detect(x, y).mean())


def analytic_power(sd: float, n: int, g: int, total_effect: float) -> float:
    """Closed-form OLS slope power under NORMAL noise — the no-shared-code cross-check on the
    simulation. SE(slope) = sd / sqrt(N * Sxx) with Sxx = sum over gen indices of (g - gbar)^2 (each
    gen contributes N games at the same x); slope = total_effect / (G-1); one-directional detection
    = P(Z > z_{1-alpha/2} - slope/SE). Assumes normal noise, so it should land within a few points of
    the simulation (which resamples the real, non-normal pool), not exactly on it."""
    gens = np.arange(g)
    sxx = float(((gens - gens.mean()) ** 2).sum())
    se = sd / np.sqrt(n * sxx)
    slope = total_effect / (g - 1)
    return float(stats.norm.sf(stats.norm.ppf(1 - ALPHA / 2) - slope / se))


def detect_delta(pool: np.ndarray, n: int, g: int, total_effect: float, rng) -> float:
    """Secondary estimator: per-gen Delta design. Each gen draws N ON games (with effect) AND N OFF
    games (no effect); regress the G points (mean_on(g) - mean_off(g)) on g. Costs 2*N*G games."""
    slope_gen = total_effect / (g - 1)
    gens = np.arange(g).astype(float)
    on = rng.choice(pool, size=(REPLICATES, g, n)) + (slope_gen * gens)[None, :, None]
    off = rng.choice(pool, size=(REPLICATES, g, n))
    delta = on.mean(axis=2) - off.mean(axis=2)          # (reps, G)
    return float(_ols_slope_detect(gens, delta).mean())


# --------------------------------------------------------------------------- readouts

def compute_grid(pool: np.ndarray, estimator, rng) -> dict[tuple[int, int], list[float]]:
    """(N, G) -> detection rate per injected effect. Computed once per pool so the grid table and the
    MDE line read the SAME Monte-Carlo numbers (no boundary disagreement from a second resample)."""
    return {(n, g): [estimator(pool, n, g, e, rng) for e in EFFECTS]
            for n in N_GRID for g in G_GRID}


def _grid_table(grid: dict[tuple[int, int], list[float]]) -> list[str]:
    # rows = (N, G); columns = injected total lift; the 0 column is the alpha (false-positive) check.
    out = ["| N | G | " + " | ".join(f"+{e:.2f}" if e else "0 (alpha)" for e in EFFECTS) + " |",
           "|---|---|" + "---|" * len(EFFECTS)]
    for (n, g), cells in grid.items():
        out.append("| " + str(n) + " | " + str(g) + " | "
                   + " | ".join(f"{c*100:.0f}%" for c in cells) + " |")
    return out


def _mde_lines(grid: dict[tuple[int, int], list[float]]) -> list[str]:
    out = []
    for (n, g), cells in grid.items():
        mde = ">0.30"
        for e, rate in zip(EFFECTS, cells):
            if e and rate >= POWER_TARGET:
                mde = f"+{e:.2f}"
                break
        out.append(f"| N={n} | G={g} | {mde} |")
    return out


def main() -> int:
    rng = np.random.default_rng(SEED)
    pools = load_pools()

    print("# Power / MDE simulation — compounding plan §0.1\n")
    print(f"seed={SEED}  replicates={REPLICATES}  alpha={ALPHA}  power_target={POWER_TARGET:.0%}  "
          f"grid N{N_GRID} x G{G_GRID}  effects(total lift @ final gen){EFFECTS}\n")
    print("Detection = two-sided slope p<0.05 AND slope>0 (the planned one-directional read), so the "
          "effect-0 column is the false-positive check and should sit near ~2.5% (half of the two-sided "
          "5%), NOT 5%.\n")

    # (A) preamble: per-game score pools (validate the +-0.9 SD prior against real data)
    print("## (A) Per-game score pools (SD = the noise the slope must beat)\n")
    print("| corpus | arm | faction | n games | mean | SD |")
    print("|---|---|---|---|---|---|")
    grains = {"town_only_run1": ("town",), "v2_full": ("town", "wolf"),
              "v6ab": ("town", "wolf")}
    pool_cache: dict[str, np.ndarray] = {}
    for corpus, arms in pools.items():
        for arm in ("off", "on"):
            for fac in grains[corpus]:
                p = _pool(arms[arm], arm, fac)
                pool_cache[f"{corpus}/{arm}/{fac}"] = p
                if p.size:
                    print(f"| {corpus} | {arm} | {fac} | {p.size} | {p.mean():+.3f} | {p.std(ddof=1):.3f} |")
                else:
                    print(f"| {corpus} | {arm} | {fac} | 0 | — | — |")
    print()

    # (B) simulation pools, in priority order
    sim_pools = [
        ("town_only_run1 OFF town  (PRIMARY — pending town rerun's noise)", "town_only_run1/off/town"),
        ("v2_full OFF town  (sensitivity — all_enabled epoch)", "v2_full/off/town"),
        ("v6ab baseline OFF town  (sensitivity — N=90 SD anchor)", "v6ab/off/town"),
        ("v2_full OFF wolf  (the gated wolf arm)", "v2_full/off/wolf"),
    ]

    primary_pool_grid: dict[tuple[int, int], list[float]] = {}
    for label, key in sim_pools:
        pool = pool_cache[key]
        primary = key == "town_only_run1/off/town"
        tag = "PRIMARY" if primary else "sensitivity"
        primary_grid = compute_grid(pool, detect_primary, rng)
        delta_grid = compute_grid(pool, detect_delta, rng)
        if primary:
            primary_pool_grid = primary_grid
        print(f"## (B) Detection % — {label}  [{tag}]  (pool n={pool.size}, SD={pool.std(ddof=1):.3f})\n")
        print("### primary estimator (regress score on gen over all N*G games)\n")
        for ln in _grid_table(primary_grid):
            print(ln)
        print("\n### secondary estimator (per-gen Delta design; costs 2*N*G games)\n")
        for ln in _grid_table(delta_grid):
            print(ln)
        print("\n### MDE (smallest grid effect reaching >=80% primary detection)\n")
        print("| | | MDE (total lift) |")
        print("|---|---|---|")
        for ln in _mde_lines(primary_grid):
            print(ln)
        print()

    # (B2) analytic cross-check: closed-form OLS slope power vs the simulation, on the primary pool.
    # Simulated anchor/ladder values come from the SAME grid draw as section (B) where the cell exists;
    # the two extra ladder cells (+0.45/+0.60, outside the main grid) use a FRESH rng stream so the
    # published grid numbers can never shift when this section evolves.
    pri_pool = pool_cache["town_only_run1/off/town"]
    sd = float(pri_pool.std(ddof=1))
    xrng = np.random.default_rng(SEED)
    print("## (B2) Analytic cross-check — closed-form OLS slope power vs the simulation "
          f"(primary pool, sd={sd:.3f})\n")
    print("Closed form: SE(slope) = sd/sqrt(N*Sxx), Sxx = sum((g-gbar)^2) over gen indices; detection "
          "= P(Z > z_0.975 - slope/SE). NOTE: the analytic form assumes NORMAL noise while the "
          "simulation resamples the real (non-normal) pool, so a few points of divergence is expected "
          "— agreement within that band is the cross-check passing.\n")
    print("### anchor cells\n")
    print("| cell | injected total lift | analytic | simulated |")
    print("|---|---|---|---|")
    for n, g, e in ((4, 6, 0.15), (20, 10, 0.15), (20, 10, 0.20)):
        sim = primary_pool_grid[(n, g)][EFFECTS.index(e)]
        print(f"| N={n} G={g} | +{e:.2f} | {analytic_power(sd, n, g, e)*100:.0f}% | {sim*100:.0f}% |")
    print("\n### effect-scaling ladder at N=4/G=6 (the v2-like config)\n")
    print("| injected total lift | analytic | simulated |")
    print("|---|---|---|")
    for e in LADDER_EFFECTS:
        if e in EFFECTS:
            sim = primary_pool_grid[(4, 6)][EFFECTS.index(e)]
        else:
            sim = detect_primary(pri_pool, 4, 6, e, xrng)
        print(f"| +{e:.2f} | {analytic_power(sd, 4, 6, e)*100:.0f}% | {sim*100:.0f}% |")
    print()

    # (C) costed deferral for rung 3
    print("## (C) Costed deferral (rung 3)\n")
    print(f"Per-game $ = ${USD_PER_GAME:.2f}/game (source: v2_full/cost_report.json, "
          f"games_total_usd 13.43 / 48 games — blended on+off).\n")
    print("| N/gen | G | games (primary N*G) | games (Delta 2*N*G) | $ primary | $ Delta |")
    print("|---|---|---|---|---|---|")
    for n in N_GRID:
        for g in G_GRID:
            ng, ng2 = n * g, 2 * n * g
            # one arm per gen for primary readout inflation vs paired: report the ON-arm-only game count;
            # a paired run doubles it. We report per-arm N*G as the slope-analysis game count.
            print(f"| {n} | {g} | {ng} | {ng2} | ${ng*USD_PER_GAME:.0f} | ${ng2*USD_PER_GAME:.0f} |")
    print()

    print("## (D) Limitations\n")
    print(
        "- i.i.d. resampling ignores cross-generation store-state CORRELATION within a run (a real run's "
        "generations are not independent draws); this likely makes these detection rates optimistic for "
        "the primary estimator.\n"
        "- The injected effect is LINEAR in generation by construction; a real compounding curve may be "
        "convex/saturating, which the straight-line slope test is not tuned for.\n"
        "- Arms are analyzed UNPAIRED at the game grain, per the plan's pairing-collapse note (§0.1).\n"
        "- Source pools are small (v2 ~24 games/arm; run1 15) so the pool SD is itself uncertain; the "
        "v6ab all-disabled baseline (n~90) is the SD sanity anchor — compare its town SD to the others."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
