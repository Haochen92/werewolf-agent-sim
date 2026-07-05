# MDE / power table — compounding plan §0.1 (the pre-run gate)

**Date:** 2026-07-05  ·  **Cost:** $0 (deterministic resampling, no model)  ·  **Standing gate:** no paid
compounding run without a current MDE table.

**Apparatus (standing):** `evaluation/src/instrument_validation/power/mde_simulation.py`.
**Rerun:** `poetry run python -m evaluation.src.instrument_validation.power.mde_simulation`.
This file is the dated readout; the script is the standing instrument.

## Method
- **Ruler.** Per-game de-luck decision score, recomputed at the game grain by
  `evaluation.src.loop.measure.game_score` (the game-grain factoring of `generation_score`: drop day-1;
  in the ON arm count only memory-active decisions; faction credit via `credit_backfill._decision_credit`,
  outcome-independent). Pools are built per corpus × arm(OFF/ON) × faction(town/wolf).
- **Corpora (all existing, $0):** `town_only_run1` (15 games/arm, gen1–3), `v2_full` (24 games/arm,
  gen1–6, all_enabled epoch), `v6ab` (180 games; all-disabled arm = baseline).
- **Design.** Per cell (pool × N × G × injected total-lift): resample N games/gen i.i.d. WITH REPLACEMENT
  from the corpus's memory-OFF pool, inject a known **linear-in-generation** effect
  (per-gen slope = total/(G−1)), run the planned slope test, over **2000 replicates** (seed 20260618),
  arms UNPAIRED at the game grain. Primary estimator = OLS slope of score vs gen over all N·G games
  (two-sided t on the slope); secondary = per-gen Δ design (regress mean_on(g)−mean_off(g) on g,
  costs 2·N·G games). Detection = two-sided slope p<0.05 AND slope>0. The grid and the MDE line read the
  SAME Monte-Carlo draw (computed once per pool) so they never disagree at the 80% boundary.
- **Analytic cross-check (§B2).** A closed-form, no-shared-code derivation — SE(slope) = sd/√(N·Σ(g−ḡ)²),
  detection = P(Z > z₀.₉₇₅ − slope/SE) — printed alongside the simulated values on three anchor cells and
  an effect-scaling ladder at N=4/G=6 up to +0.60. The analytic form assumes normal noise; the simulation
  resamples the real pool, so a few points of divergence is expected.
- **Effect-0 column** = the false-positive check. Because detection is one-directional (slope>0),
  the expected null rate is ~2.5% (half the two-sided 5%), NOT 5%.

## Headline
- **Real per-game noise is ~0.27–0.33 SD — roughly 3× SMALLER than the ±0.9 prior** the plan assumed. The
  ±0.9 is the SD of a single −1/0/+1 decision verdict; a game's score AVERAGES over its ~several creditable
  decisions, so the game-grain SD collapses to ~0.3. This is the load-bearing correction — power is better
  than the prior implied, but the injected effect (+0.1–0.2) is also small relative to it.
- **+0.15 total lift is undetectable at every grid config.** On the primary pool (run-1 OFF town, SD 0.33),
  the best cell (N=20/G=10) hits only ~56% on +0.15; the tighter v6ab anchor (SD 0.27) reaches ~73% — still
  short of 80%. The MDE at the largest affordable config (N=20/G=10) is **+0.20** (81% on the primary pool).
- **At the v2-like config (N=4/G=6), +0.15 detects ~11%** — a coin-flip-losing bet, exactly the
  pre-registration warning: a +0.1–0.2 compounding effect run at affordable N buys near-noise.
- **The per-gen Δ (dual-arm) estimator is strictly WORSE per game** (it regresses only G points): +0.20 at
  N=20/G=10 detects ~42% vs the primary's 81%, at double the cost. Paying for an OFF arm every generation
  buys cost, not power, under this noise model — spend the budget on the primary single-slope read.
- **False-positive check: PASS** — every effect-0 cell sits at 2–3%, matching the ~2.5% one-directional
  expectation; no cell strays.
- **Analytic cross-check: PASS** — the closed-form power lands at 11% / 53% / 78% on the anchor cells vs
  the simulation's 11% / 56% / 81%; the N=4/G=6 ladder agrees within 4 points up to +0.60 (§B2).

---

# Power / MDE simulation — compounding plan §0.1

seed=20260618  replicates=2000  alpha=0.05  power_target=80%  grid N(4, 5, 10, 20) x G(6, 8, 10)  effects(total lift @ final gen)(0.0, 0.05, 0.1, 0.15, 0.2, 0.3)

Detection = two-sided slope p<0.05 AND slope>0 (the planned one-directional read), so the effect-0 column is the false-positive check and should sit near ~2.5% (half of the two-sided 5%), NOT 5%.

## (A) Per-game score pools (SD = the noise the slope must beat)

| corpus | arm | faction | n games | mean | SD |
|---|---|---|---|---|---|
| town_only_run1 | off | town | 15 | +0.334 | 0.332 |
| town_only_run1 | on | town | 15 | +0.200 | 0.215 |
| v2_full | off | town | 24 | +0.276 | 0.320 |
| v2_full | off | wolf | 24 | +0.311 | 0.306 |
| v2_full | on | town | 24 | +0.129 | 0.257 |
| v2_full | on | wolf | 24 | +0.445 | 0.257 |
| v6ab | off | town | 30 | +0.215 | 0.266 |
| v6ab | off | wolf | 30 | +0.356 | 0.264 |
| v6ab | on | town | 60 | +0.180 | 0.289 |
| v6ab | on | wolf | 0 | — | — |

## (B) Detection % — town_only_run1 OFF town  (PRIMARY — pending town rerun's noise)  [PRIMARY]  (pool n=15, SD=0.332)

### primary estimator (regress score on gen over all N*G games)

| N | G | 0 (alpha) | +0.05 | +0.10 | +0.15 | +0.20 | +0.30 |
|---|---|---|---|---|---|---|---|
| 4 | 6 | 3% | 3% | 7% | 11% | 15% | 29% |
| 4 | 8 | 3% | 5% | 7% | 14% | 20% | 39% |
| 4 | 10 | 2% | 4% | 9% | 15% | 25% | 44% |
| 5 | 6 | 3% | 5% | 7% | 11% | 19% | 38% |
| 5 | 8 | 2% | 5% | 10% | 14% | 23% | 47% |
| 5 | 10 | 3% | 5% | 10% | 17% | 28% | 53% |
| 10 | 6 | 3% | 6% | 12% | 23% | 37% | 67% |
| 10 | 8 | 2% | 6% | 15% | 29% | 45% | 77% |
| 10 | 10 | 2% | 8% | 16% | 31% | 49% | 84% |
| 20 | 6 | 3% | 8% | 22% | 40% | 63% | 93% |
| 20 | 8 | 3% | 10% | 27% | 49% | 74% | 97% |
| 20 | 10 | 3% | 10% | 30% | 56% | 81% | 99% |

### secondary estimator (per-gen Delta design; costs 2*N*G games)

| N | G | 0 (alpha) | +0.05 | +0.10 | +0.15 | +0.20 | +0.30 |
|---|---|---|---|---|---|---|---|
| 4 | 6 | 2% | 3% | 5% | 7% | 7% | 14% |
| 4 | 8 | 3% | 3% | 5% | 9% | 11% | 16% |
| 4 | 10 | 3% | 4% | 6% | 10% | 12% | 21% |
| 5 | 6 | 2% | 4% | 5% | 7% | 8% | 16% |
| 5 | 8 | 2% | 3% | 6% | 8% | 12% | 21% |
| 5 | 10 | 2% | 4% | 7% | 9% | 14% | 23% |
| 10 | 6 | 3% | 4% | 6% | 11% | 14% | 25% |
| 10 | 8 | 2% | 5% | 8% | 13% | 19% | 39% |
| 10 | 10 | 3% | 5% | 10% | 14% | 25% | 46% |
| 20 | 6 | 3% | 5% | 9% | 14% | 24% | 48% |
| 20 | 8 | 2% | 6% | 11% | 21% | 34% | 62% |
| 20 | 10 | 2% | 6% | 14% | 26% | 42% | 75% |

### MDE (smallest grid effect reaching >=80% primary detection)

| | | MDE (total lift) |
|---|---|---|
| N=4 | G=6 | >0.30 |
| N=4 | G=8 | >0.30 |
| N=4 | G=10 | >0.30 |
| N=5 | G=6 | >0.30 |
| N=5 | G=8 | >0.30 |
| N=5 | G=10 | >0.30 |
| N=10 | G=6 | >0.30 |
| N=10 | G=8 | >0.30 |
| N=10 | G=10 | +0.30 |
| N=20 | G=6 | +0.30 |
| N=20 | G=8 | +0.30 |
| N=20 | G=10 | +0.20 |

## (B) Detection % — v2_full OFF town  (sensitivity — all_enabled epoch)  [sensitivity]  (pool n=24, SD=0.320)

### primary estimator (regress score on gen over all N*G games)

| N | G | 0 (alpha) | +0.05 | +0.10 | +0.15 | +0.20 | +0.30 |
|---|---|---|---|---|---|---|---|
| 4 | 6 | 3% | 4% | 7% | 11% | 17% | 31% |
| 4 | 8 | 3% | 4% | 7% | 12% | 19% | 38% |
| 4 | 10 | 2% | 5% | 9% | 14% | 22% | 48% |
| 5 | 6 | 2% | 4% | 9% | 13% | 21% | 40% |
| 5 | 8 | 2% | 6% | 9% | 16% | 25% | 49% |
| 5 | 10 | 3% | 6% | 10% | 19% | 29% | 57% |
| 10 | 6 | 3% | 6% | 14% | 26% | 38% | 70% |
| 10 | 8 | 3% | 6% | 15% | 28% | 46% | 80% |
| 10 | 10 | 2% | 8% | 17% | 32% | 54% | 86% |
| 20 | 6 | 3% | 10% | 22% | 42% | 66% | 95% |
| 20 | 8 | 3% | 9% | 26% | 51% | 74% | 98% |
| 20 | 10 | 3% | 11% | 30% | 58% | 81% | 98% |

### secondary estimator (per-gen Delta design; costs 2*N*G games)

| N | G | 0 (alpha) | +0.05 | +0.10 | +0.15 | +0.20 | +0.30 |
|---|---|---|---|---|---|---|---|
| 4 | 6 | 3% | 4% | 5% | 6% | 8% | 14% |
| 4 | 8 | 2% | 4% | 5% | 8% | 11% | 17% |
| 4 | 10 | 2% | 4% | 6% | 8% | 13% | 23% |
| 5 | 6 | 2% | 3% | 5% | 7% | 9% | 17% |
| 5 | 8 | 3% | 4% | 7% | 8% | 13% | 21% |
| 5 | 10 | 2% | 5% | 7% | 10% | 14% | 26% |
| 10 | 6 | 2% | 4% | 7% | 11% | 14% | 26% |
| 10 | 8 | 2% | 5% | 8% | 13% | 19% | 37% |
| 10 | 10 | 3% | 5% | 9% | 16% | 26% | 46% |
| 20 | 6 | 2% | 5% | 10% | 17% | 25% | 48% |
| 20 | 8 | 3% | 6% | 12% | 22% | 36% | 64% |
| 20 | 10 | 3% | 7% | 13% | 27% | 44% | 77% |

### MDE (smallest grid effect reaching >=80% primary detection)

| | | MDE (total lift) |
|---|---|---|
| N=4 | G=6 | >0.30 |
| N=4 | G=8 | >0.30 |
| N=4 | G=10 | >0.30 |
| N=5 | G=6 | >0.30 |
| N=5 | G=8 | >0.30 |
| N=5 | G=10 | >0.30 |
| N=10 | G=6 | >0.30 |
| N=10 | G=8 | >0.30 |
| N=10 | G=10 | +0.30 |
| N=20 | G=6 | +0.30 |
| N=20 | G=8 | +0.30 |
| N=20 | G=10 | +0.20 |

## (B) Detection % — v6ab baseline OFF town  (sensitivity — N=90 SD anchor)  [sensitivity]  (pool n=30, SD=0.266)

### primary estimator (regress score on gen over all N*G games)

| N | G | 0 (alpha) | +0.05 | +0.10 | +0.15 | +0.20 | +0.30 |
|---|---|---|---|---|---|---|---|
| 4 | 6 | 2% | 5% | 8% | 15% | 24% | 46% |
| 4 | 8 | 2% | 6% | 11% | 18% | 29% | 54% |
| 4 | 10 | 2% | 5% | 11% | 21% | 33% | 62% |
| 5 | 6 | 3% | 6% | 11% | 18% | 28% | 56% |
| 5 | 8 | 3% | 6% | 12% | 19% | 34% | 65% |
| 5 | 10 | 2% | 6% | 14% | 23% | 41% | 73% |
| 10 | 6 | 2% | 8% | 17% | 33% | 51% | 84% |
| 10 | 8 | 2% | 7% | 21% | 39% | 59% | 91% |
| 10 | 10 | 3% | 9% | 21% | 45% | 67% | 95% |
| 20 | 6 | 2% | 12% | 31% | 54% | 82% | 98% |
| 20 | 8 | 2% | 12% | 35% | 66% | 88% | 100% |
| 20 | 10 | 3% | 13% | 40% | 74% | 92% | 100% |

### secondary estimator (per-gen Delta design; costs 2*N*G games)

| N | G | 0 (alpha) | +0.05 | +0.10 | +0.15 | +0.20 | +0.30 |
|---|---|---|---|---|---|---|---|
| 4 | 6 | 2% | 3% | 5% | 7% | 12% | 20% |
| 4 | 8 | 2% | 4% | 7% | 10% | 13% | 26% |
| 4 | 10 | 3% | 4% | 8% | 11% | 16% | 32% |
| 5 | 6 | 3% | 5% | 6% | 8% | 12% | 21% |
| 5 | 8 | 3% | 5% | 7% | 10% | 16% | 31% |
| 5 | 10 | 3% | 5% | 7% | 12% | 19% | 37% |
| 10 | 6 | 2% | 5% | 9% | 12% | 20% | 38% |
| 10 | 8 | 3% | 5% | 10% | 19% | 25% | 51% |
| 10 | 10 | 3% | 7% | 11% | 21% | 33% | 63% |
| 20 | 6 | 2% | 6% | 12% | 21% | 34% | 62% |
| 20 | 8 | 3% | 7% | 17% | 30% | 47% | 78% |
| 20 | 10 | 3% | 8% | 18% | 36% | 60% | 90% |

### MDE (smallest grid effect reaching >=80% primary detection)

| | | MDE (total lift) |
|---|---|---|
| N=4 | G=6 | >0.30 |
| N=4 | G=8 | >0.30 |
| N=4 | G=10 | >0.30 |
| N=5 | G=6 | >0.30 |
| N=5 | G=8 | >0.30 |
| N=5 | G=10 | >0.30 |
| N=10 | G=6 | +0.30 |
| N=10 | G=8 | +0.30 |
| N=10 | G=10 | +0.30 |
| N=20 | G=6 | +0.20 |
| N=20 | G=8 | +0.20 |
| N=20 | G=10 | +0.20 |

## (B) Detection % — v2_full OFF wolf  (the gated wolf arm)  [sensitivity]  (pool n=24, SD=0.306)

### primary estimator (regress score on gen over all N*G games)

| N | G | 0 (alpha) | +0.05 | +0.10 | +0.15 | +0.20 | +0.30 |
|---|---|---|---|---|---|---|---|
| 4 | 6 | 3% | 5% | 8% | 15% | 22% | 39% |
| 4 | 8 | 3% | 6% | 8% | 16% | 26% | 46% |
| 4 | 10 | 2% | 5% | 10% | 18% | 28% | 53% |
| 5 | 6 | 3% | 6% | 10% | 15% | 23% | 44% |
| 5 | 8 | 3% | 6% | 11% | 17% | 28% | 53% |
| 5 | 10 | 3% | 5% | 12% | 21% | 32% | 63% |
| 10 | 6 | 2% | 8% | 14% | 27% | 42% | 74% |
| 10 | 8 | 2% | 8% | 16% | 33% | 49% | 83% |
| 10 | 10 | 2% | 10% | 19% | 36% | 56% | 88% |
| 20 | 6 | 3% | 9% | 25% | 47% | 70% | 95% |
| 20 | 8 | 3% | 10% | 28% | 55% | 78% | 98% |
| 20 | 10 | 3% | 11% | 32% | 61% | 85% | 100% |

### secondary estimator (per-gen Delta design; costs 2*N*G games)

| N | G | 0 (alpha) | +0.05 | +0.10 | +0.15 | +0.20 | +0.30 |
|---|---|---|---|---|---|---|---|
| 4 | 6 | 2% | 4% | 5% | 7% | 9% | 16% |
| 4 | 8 | 3% | 3% | 6% | 8% | 11% | 20% |
| 4 | 10 | 3% | 4% | 6% | 9% | 12% | 28% |
| 5 | 6 | 2% | 4% | 6% | 8% | 10% | 19% |
| 5 | 8 | 3% | 3% | 7% | 10% | 13% | 24% |
| 5 | 10 | 3% | 4% | 7% | 12% | 16% | 31% |
| 10 | 6 | 3% | 5% | 7% | 12% | 14% | 30% |
| 10 | 8 | 2% | 5% | 8% | 12% | 23% | 43% |
| 10 | 10 | 3% | 6% | 10% | 16% | 25% | 50% |
| 20 | 6 | 2% | 5% | 11% | 19% | 28% | 54% |
| 20 | 8 | 2% | 7% | 13% | 23% | 37% | 69% |
| 20 | 10 | 3% | 6% | 16% | 28% | 46% | 79% |

### MDE (smallest grid effect reaching >=80% primary detection)

| | | MDE (total lift) |
|---|---|---|
| N=4 | G=6 | >0.30 |
| N=4 | G=8 | >0.30 |
| N=4 | G=10 | >0.30 |
| N=5 | G=6 | >0.30 |
| N=5 | G=8 | >0.30 |
| N=5 | G=10 | >0.30 |
| N=10 | G=6 | >0.30 |
| N=10 | G=8 | +0.30 |
| N=10 | G=10 | +0.30 |
| N=20 | G=6 | +0.30 |
| N=20 | G=8 | +0.30 |
| N=20 | G=10 | +0.20 |

## (B2) Analytic cross-check — closed-form OLS slope power vs the simulation (primary pool, sd=0.332)

Closed form: SE(slope) = sd/sqrt(N*Sxx), Sxx = sum((g-gbar)^2) over gen indices; detection = P(Z > z_0.975 - slope/SE). NOTE: the analytic form assumes NORMAL noise while the simulation resamples the real (non-normal) pool, so a few points of divergence is expected — agreement within that band is the cross-check passing.

### anchor cells

| cell | injected total lift | analytic | simulated |
|---|---|---|---|
| N=4 G=6 | +0.15 | 11% | 11% |
| N=20 G=10 | +0.15 | 53% | 56% |
| N=20 G=10 | +0.20 | 78% | 81% |

### effect-scaling ladder at N=4/G=6 (the v2-like config)

| injected total lift | analytic | simulated |
|---|---|---|
| +0.15 | 11% | 11% |
| +0.30 | 33% | 29% |
| +0.45 | 62% | 58% |
| +0.60 | 86% | 85% |

## (C) Costed deferral (rung 3)

Per-game $ = $0.28/game (source: v2_full/cost_report.json, games_total_usd 13.43 / 48 games — blended on+off).

| N/gen | G | games (primary N*G) | games (Delta 2*N*G) | $ primary | $ Delta |
|---|---|---|---|---|---|
| 4 | 6 | 24 | 48 | $7 | $13 |
| 4 | 8 | 32 | 64 | $9 | $18 |
| 4 | 10 | 40 | 80 | $11 | $22 |
| 5 | 6 | 30 | 60 | $8 | $17 |
| 5 | 8 | 40 | 80 | $11 | $22 |
| 5 | 10 | 50 | 100 | $14 | $28 |
| 10 | 6 | 60 | 120 | $17 | $34 |
| 10 | 8 | 80 | 160 | $22 | $45 |
| 10 | 10 | 100 | 200 | $28 | $56 |
| 20 | 6 | 120 | 240 | $34 | $67 |
| 20 | 8 | 160 | 320 | $45 | $90 |
| 20 | 10 | 200 | 400 | $56 | $112 |

## (D) Limitations

- i.i.d. resampling ignores cross-generation store-state CORRELATION within a run (a real run's generations are not independent draws); this likely makes these detection rates optimistic for the primary estimator.
- The injected effect is LINEAR in generation by construction; a real compounding curve may be convex/saturating, which the straight-line slope test is not tuned for.
- Arms are analyzed UNPAIRED at the game grain, per the plan's pairing-collapse note (§0.1).
- Source pools are small (v2 ~24 games/arm; run1 15) so the pool SD is itself uncertain; the v6ab all-disabled baseline (n~90) is the SD sanity anchor — compare its town SD to the others.
