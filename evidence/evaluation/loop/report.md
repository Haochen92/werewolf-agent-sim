# v7 Loop — Evaluation Apparatus Report

> **Scope: the apparatus, not the verdict.** Covers *how the loop measures compounding* (the slope
> instrument, the credit proxies, the discussion tagger, the invariants) and *how far to trust those
> measurements* (L1 + L2) — NOT whether memory compounds (the open science). Design + run records stay in
> [`../../v7_final/`](../../v7_final/). Lens + skeleton: [`../report.md`](../report.md); ledger:
> [`../source_map.md`](../source_map.md).
>
> **Verdict: ✅ mechanics sound · 🟡 the science is open.** The measurement plumbing is the best-tested part
> of the eval system and it **caught its own invalid runs**; the compounding verdict is not in.

## Objective the apparatus targets

Across generations, does a memory-on arm's de-lucked decision quality rise faster than memory-off? The loop
must measure that **cheaply, deterministically, and without confounding the arms.**

## L1 — the instrument

- **Slope instrument** `loop/measure.py::generation_score` (**LLM-free**, pure file read): mean de-luck
  decision *value* per faction per generation, split by arm; each creditable decision → `VERDICT_VALUE`
  {+1/0/−1} via `_decision_credit`. It emits one slope **point** per generation (the OLS *slope* is computed
  downstream in the salvage scripts — see corrections). Policies: **skip day-1** (memoryless in both arms),
  **on-memory-active-only** (count only `memory_enabled` ON decisions), **bucket by ARM not by per-decision
  flag** (keeps on/off like-for-like). Unit-tested.
- **Credit proxies** `loop/credit_backfill.py` (the deterministic engine both `measure.py` and `credit.py`
  import): `_vote_credit` (town = hit_threat; SK = any non-self lynch; **wolf = blend with room plurality**,
  bussing-aware), `_night_credit` (investigator hit_threat [flagged weak]; vigilante threat+/friendly-fire−;
  wolf/SK power-targeting). De-luck baseline = per-(role/phase) mean outcome of **memory-OFF** decisions;
  `lift` = vs base rate, `shrunk_lift` ×follow/(follow+5). Unit-tested (`test_credit_blend`, 12 cases).
- **Discussion tagger** `loop/discussion_tagger.py` (the paid deceiver-skill metric): omniscient end-of-day
  per-player verdict — DISCUSSION (holistic positive/neutral/negative weighing framing/credibility/role_reveal,
  "advanced their faction's win, independent of outcome") + NIGHT (read-quality of the target). flash-lite,
  `with_structured_output`, all-required schema, cached per (game_id, v2). Wired into the **paid** credit
  tier (`credit.py::_tagger_ledger`); the **free** tier credits discussion by the day-vote endpoint instead.
- **Invariants** `loop/invariants.py`: fail-loud guards — strict eval-case iteration (unresolvable path →
  RAISE), dead-credit guard, base-rate guard, empty-score guard, the **arm-guard ×2**, and fingerprint-drift
  guard. These are what protect a *valid* run.

## L2 — trust

- **`measure.py` = ✅ LLM-free deterministic** — no model import, deterministic verdict mapping, unit-tested
  (`test_generation_score_buckets_by_arm_not_flag`). The soundest instrument in the loop.
- **The tagger = VALIDATED METRIC, not a memory effect.** The N=24 blinded+verbosity-controlled retest
  (`tagger_skill_retest.py`): partial r(disc verdict, **won** | deluck, verbosity) = **+0.56 wolf / +0.60 SK
  / +0.02 town** — i.e. the wolf/SK discussion verdict predicts the win *beyond* the vote proxy, survives
  blinding the tagger to the outcome AND partialling out verbosity → **real deceiver skill the vote proxy
  can't see**, not leak or wordiness. Bounds: **N=24, single-epoch, correlational — validates the METRIC, not
  a memory effect.** The 2×2 deleak ablation (N=6) confirms outcome-leak negligible. **Halo-tension RESOLVED:**
  the retracted "+0.556" is a *different quantity* (undifferenced **town** credit-LEVEL), not this wolf/SK
  corr-with-win; the retest's town row (+0.02) agrees with the retraction.
- **Credit proxies sound** (deterministic, faction-relative, unit-tested) with acknowledged limits: wolf
  credit is the *blend* proxy (concealment r≈+0.22, not direct deception); investigator find-rate is a flagged
  weak channel; **de-luck removes outcome luck, NOT opponent strength** — the root of the arms-race confound.
- **⚠️ WHY both v2 runs were invalid — and the apparatus caught them** (the honesty signal): run-1 had a
  distorted/unpaired baseline (→ distorted lift); v2_full silently ran the ON arm as `all_enabled` not
  `town_only` (driver default) — so the "null control" was a live treatment arm and the town number is
  **irreparably confounded** (better-concealed memory-wolves mechanically depress the town vote proxy; de-luck
  doesn't remove opponent strength), compounded by a tag-cache `game_id` collision that scored OFF with ON
  tags. **Both caught on (re-)audit; both are now an automated invariant** — the arm-guard would make the slip
  a $0.50 gen-1 crash instead of a $65 null (~$130 lost across two runs of the same failure class).
- **Consolidation quality is NOT measured** (`consolidate.py` has no judge/score path — only prune mechanics);
  the loop measures the *downstream* slope, not consolidation output. Known dead levers: the evict rule is
  inert (`retrieved_count` never wired → `evicted=0`), the new-clusters-only synth gate was a no-op at k=1.
- 5-axis: (a) not flat (per-faction × per-channel); (b) the **arms-race opponent-strength confound** is NOT
  removed by de-luck + pairing decays after the first divergent decision — caught, not silently passed;
  (c) the tagger metric is correlational/uncalibrated; (d) staleness handled by design (rolling-window recompute,
  versioned tag cache, fingerprint guard); (e) small-N (N=24 retest, 4 games/gen × 6 gens, ±0.2-0.3 swings).

## Verdict + cheapest upgrade

**✅ mechanics · 🟡 science.** The plumbing is the asset: LLM-free deterministic slope, deterministic
unit-tested credit proxies, real fail-loud invariants that demonstrably caught the run-invalidities, and a
*validated* deceiver-skill tagger. The compounding verdict is not in — the tagger metric is
correlational/single-epoch/uncalibrated, consolidation quality isn't measured, and both paid runs were invalid.

**Cheapest upgrade:** a single **VALID paired `town_only` rerun** (~$15) with the now-shipped locks
(`--expect-factions town_only` fail-closed, paired same-board arms, same-epoch OFF baseline, fingerprint
guard) — the clean experiment that was never run — **plus a wolf-direct arm** (a direct wolf SP/obs A/B, the
one missing direct measurement) to convert the tagger's tentative wolf signal from a correlational metric into
a memory verdict.

## Evidence (code + L2 artifacts)

- **Code:** `evaluation/src/loop/{measure,credit,credit_backfill,discussion_tagger,invariants,consolidate}.py`;
  unit tests `tests/test_loop_{measure,invariants,consolidate,merge}.py`, `test_credit_blend.py`,
  `test_tagger_inputs.py`.
- **L2 artifacts (the loop's KEY L2 proof — pointed-at):** `../../v7_final/v2_full/tagger_skill_retest.py`
  (N=24 blinded+verbosity retest) + `tagger_deleak_ablation.py` (N=6 2×2). ⚠️ **Both print to stdout — no
  result file**; the only durable record of the numbers is `v7_final/experiment_log.md` §12g. If those numbers
  are load-bearing proof, capture them to a `.md`/`.json` next to the scripts (flagged, not done). `__pycache__`
  is committable cruft to drop.

## Colocation call (JIT, 2026-06-28)

**Stays put — point-at.** The retest scripts are dated post-hoc salvage code colocated inside the frozen
`v2_full/` run record (the "study code embedded in evidence as a dated artifact" CLAUDE.md says to FREEZE),
and they depend on co-located relative data — a move breaks them. The live tagger
(`evaluation/src/loop/discussion_tagger.py`) already points at them. One durability gap noted above (stdout-only
results).

*(Inspected 2026-06-28. Apparatus characterised, not the compounding verdict.)*
