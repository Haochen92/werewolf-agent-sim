# A/B Methodology — Evaluation Apparatus Report

> **Scope: the apparatus.** The "fair & directional at low N" machinery — drift guards, the arm-guard,
> variance/power tooling. This layer is almost pure L1+L2 (little design). Lens + skeleton:
> [`../report.md`](../report.md); ledger: [`../source_map.md`](../source_map.md).
>
> **Verdict: 🟡 — strong where enforced (arm-guard, in-run fingerprint, validated pairing math, honest MDE);
> the two highest-stakes drift surfaces (cross-epoch gate, embedding alias) are MANUAL/undetected.**

## Objective the apparatus targets

At N=30 with a temp=1.0 generative game, a memory A/B is one drift event or one config slip away from a
fake result. This layer's job is to make low-N runs *directional and trustworthy*: cancel board luck, hold
the epoch fixed, catch arm slips before they cost money, and be honest about what's detectable.

## L1 — the instrument

- **Drift guards.** (i) **Interleave-arms rule** — ON+OFF in one run window so drift hits both equally;
  ENFORCED in code only in the **loop** driver (`loop/driver.py:136-155` `_run_arms_parallel`, paired by
  `game_id`), **NOT** in `scripts/run_batch.py` (`--configs` takes `nargs="+"` but there's no per-game
  alternation — the "alternates per game" ergonomics TODO is unbuilt). (ii) **$3 memory-off canary** — 10
  `all_disabled` games on the baseline seeds before trusting a cross-day read; **manual** pre-registered step.
  (iii) **Fingerprint stamping** — `run_fingerprint.py:79-124` records backend, region, model IDs,
  **embedding model ID**, temp, thinking levels, prompt-bundle content hash, git commit + dirty.
- **Arm-guard (hard-fail ×2)** — `assert_arm_declared` (fail-closed pre-spend; raise unless `--expect-factions`
  or `--unchecked-arm`) + `assert_arm_factions` (per-gen: reads the ON arm's *actual* `memory_config`, raises
  ARM MISMATCH vs declared intent). In `loop/{invariants,driver,config}.py`, correctly **not** in run_batch.
- **Variance / power tooling:** **pairing is BUILT** (`game_id` pins board+tiebreak; paired tests
  `mcnemar_exact`/`wilcoxon_paired` in `core/stats.py`, used by the evidence analyzers). **Bootstrap CIs**
  PROPOSED for the A/B (one exists, but only in the reranker trainer). **CUPED** ruled **NOT APPLICABLE**
  (no pre-treatment covariate; recorded covariates are post-treatment → adjusting biases).

## L2 — trust

- **Jun-11 drift catch:** 10 fresh baseline games came back villagers 10% / SK 60% / wolves 30% vs the
  original 67% / 27% / 7% (Fisher **p=0.0028**) — systematic shift despite byte-identical prompts and no code
  change. This motivated interleave-by-default. *The apparatus caught its own confound.*
- **Enforced vs manual:** ENFORCED (hard-assert) = arm-guard ×2 + `assert_fingerprint_consistent` (any
  backend/model/prompt/commit flip *within* a loop run → crash). MANUAL = the **cross-day/cross-epoch gate**
  (fingerprint consistency holds only within one run; cross-run is detection-not-pinning — a human must check)
  and the **$3 canary**. **Embedding alias is unpinnable AND its drift is undetectable** — Vertex exposes only
  the alias, `model_version` echoes the alias, so the recorded ID tells you *which* alias, not *when it moved*;
  the proposed embedding-canary-pairs test is **unbuilt**.
- **Pairing variance-reduction empirically validated — and it deflates the pairing claim.** Canary
  decomposition: **seed (role-draw) effect ≈ ZERO** (within-seed sd 0.249 ≈ across-seed 0.211-0.262) → "pairing
  on game_id adds ~no power; same-epoch was the load-bearing part." So pairing is *validated as near-zero-power*
  for variance reduction; its real value is board-cancellation + the same-epoch discipline.
- **MDE / power:** two-arm N=30, 80% power, p<0.05 → **~0.18 vote-acc, ~36pp win**; per-game sd ~0.25 vote /
  0.5 win; subtle effects (Δ≈0.10) need ~100 games/arm → measure at the component level. (Source: the
  2026-06-12 canary-pair decomposition in the **drift doc**, not the variance-levers doc — see corrections.)

## Verdict + cheapest upgrade

**🟡.** Strong where enforced (arm-guard ×2 fail-closed, in-run fingerprint hard-assert, validated
pairing/de-luck math, honest MDE), but the **two highest-stakes drift surfaces are unguarded in code** — the
cross-epoch gate and the embedding alias are manual, and the embedding alias drift is *silent + undetectable*.
Variance *measurement* is solid; variance *reduction* via pairing is empirically ~null (correctly downgraded);
no CUPED is the right call (inapplicable, not a gap).

**Cheapest upgrade:** build the **embedding-canary-pairs test** (~12 fixed text pairs with tuning-time
similarities, asserted at batch start within epsilon) — it converts the one *silent + undetectable* failure
mode (store↔query embedding-space drift that quietly deflates retrieval and invalidates the dedup thresholds)
into a loud crash; it's the only drift surface with no detection at all. Second-cheapest: make `run_batch.py`
alternate `--configs` per game so the interleave rule is enforced outside the loop driver too.

## Evidence (code + L2 artifacts)

- **Code:** `Agents/run_fingerprint.py`, `evaluation/src/loop/{invariants,driver,config}.py`,
  `evaluation/src/core/stats.py`.
- **L2 artifacts:** `../../model_drift/drift_surfaces_and_guards.md` (the drift hub + the MDE/seed-effect
  numbers), `../../metrics/variance_reduction_levers.md` (the levers audit).

## Colocation call (JIT, 2026-06-28)

- **`variance_reduction_levers.md`** is genuinely mis-filed in `metrics/` (it's methodology) and **belongs
  here** — BUT it is **not a clean `git mv`**: it has **6 outbound relative links** (to `../caching/`,
  `../memory_system/effectiveness/report.md`, same-dir `experiment_log.md`) + **~5 inbound refs**
  (source_map ×3, CONSOLIDATION_PLAN ×2) that all need rewriting. **Deferred to the batched reorg** (flagged,
  not executed now) — the cost is a link-rewrite, not a move, and it's the one piece worth physically
  relocating in the whole eval segment.
- **`model_drift/drift_surfaces_and_guards.md`** — **point-at, don't move** (heavily inbound-linked from 4
  docs; mixes A/B methodology with a component-drift map that belongs to the memory narrative).

*(Inspected 2026-06-28.)*
