# Labeling Pipeline — Build Plan (the second half)

> **What this is.** The build plan for the label-*validation* half of the pipeline — the calibration /
> bias-detection / confidence layer that [`report.md`](report.md) §3 lists as the headline gap. The
> *design* is not invented here: it is the pre-registered protocol in
> [`../../retrieval/context_eval/experiment_log.md`](../../retrieval/context_eval/experiment_log.md) §6.
> This doc maps that protocol onto concrete code. **Status: designed, not built. Gated** (see §Gates).

## The reframe

It is **not one script — it is a staged human-in-the-loop loop.** The built triage front feeds a new
calibration back-end, with human pauses between. The pipeline already does steps 0–3 of the protocol
(produce labels, route disagreements); the build adds steps 4–7 (validate them) plus the prerequisites
that feed the human (anchor sampling, rubric parity).

```
1. engine            → vendor-diverse panel labels (CoT)
2. voter+consolidate → consensus + agreement tiers + ties.json            [BUILT]
3. anchor.py         → stratified pilot (~40–50, oversample unanimous tier) → exporter
   ⟶ [HUMAN labels the pilot — ~one focused day]
4. consolidate reads → calibration: agreement+CI, McNemar+TOST vs δ, tier_audit
5. staged_decision   → STOP (clear) | EXPAND (export more, toward ~96) → back to 3
6. on ACCEPT         → assemble_gold + report (coverage, CI, κ, per-judge skew, %routed)
```

Adapter-agnostic, so one back-end serves all three labelling tracks (reranker · dedup · situation-retrieval).

## Component map (protocol step → artifact → status)

| Protocol step (`context_eval` §6) | Artifact | Status |
|---|---|---|
| 0. Shared rubric (0/1/2 defs + 6–8 worked edge cases) | `adapters/*.format_prompt`; **must also feed** `exporter.format_for_manual` | 🟡 panel side built; human-export parity is a gap |
| 1. Stratified anchor (~150 *judgments*, oversample agree-tier, spread across cases) | **new** `anchor.py` | ❌ new (`data/sampling.py` samples game cases — wrong unit) |
| 2. Vendor-diverse panel @ scale, CoT | `engine.py` + `voter.py` | ✅ built (diversity = a `ModelSpec` config choice) |
| 3. Human labels anchor + routed hard cases | `exporter.py` + `pipeline.consolidate` | 🟡 built; selection must be anchor/routing-driven, not a case range |
| 4. Calibrate panel→human + acceptance test | **new** `calibration.py::calibrate()` | ❌ new (core of the half) |
| 5. Staged bias detection (δ, McNemar + TOST, stop-early) | **new** `calibration.py::{bias_test, staged_decision}()` | ❌ new |
| 6. Unanimity-tier audit (agree-tier is suspect) | **new** `calibration.py::tier_audit()` | ❌ new |
| 7. Final gold + report (coverage, CI, κ, per-judge skew, %routed) | **new** `calibration.py::{assemble_gold, report}()` | 🟡 `pipeline.consolidate` does consensus + a tally; calibrated gold + full report is the gap |

## The new code

**`labeling/calibration.py`** — the validation back-end. Consumes the merge output (panel consensus +
per-model scores + vote confidence) + a human-anchor file; emits a calibration report:
- `calibrate()` — panel-vs-human agreement + CI → the acceptance gate (≥80% agreement, CI-lower-bound
  ≥75%, no significant directional bias).
- `bias_test(discordant_pairs, δ)` — McNemar/sign (presence of skew) **and** TOST vs ±δ (absence).
- `staged_decision(pilot, δ)` — `STOP_NEGLIGIBLE` / `STOP_LARGE` / `EXPAND`, with pre-registered looks
  (n≈50, n≈100) so optional-stopping stays honest.
- `tier_audit(tier="unanimous", δ)` — the skew test on the agree-tier subset → "unanimity earned-reliable"
  (route humans to disagreements only) vs "not safe" (keep human coverage on the agree-tier).
- `assemble_gold()` + `report()` — calibrated panel where confident (soft where it splits) + human on
  routed; the protocol's step-5 report line.

**`labeling/anchor.py`** — the stratified anchor sampler (judgment-level, by type × agreement-pattern ×
role, oversampling the confident-agree zone, spread across cases for design-effect) + the routed-hard-case
selector (from voter confidence) + `sample_size_for_ci(half_width)` (the ±X%→N table).

**Stats — mostly reuse, three additions** (in `core/stats.py`, so the evidence scripts share them):
- **Reuse:** `binomial_ci` (Clopper–Pearson), `mcnemar_exact`.
- **Add (small):** `tost_proportion` (two one-sided tests, equivalence); `cohens_kappa` (inter-annotator).
- **Add (the one non-trivial piece):** a **cluster-robust agreement CI** — a **by-case bootstrap** of the
  agreement proportion. The protocol explicitly warns judgments cluster within a case (design effect), so
  the naive IID `binomial_ci` overstates precision on ~150 judgments from ~25 cases. This is the only
  stats addition that is more than a formula.

**Config + driver:** a `CalibrationConfig` (anchor path, δ, acceptance thresholds, tier-to-audit) and a
thin staged CLI subcommand running `panel → sample → [pause] → calibrate → decide → maybe expand → gold`.

## Build sequencing

- **Phase 1 — the acceptance test.** `calibrate()` + agreement + Clopper–Pearson CI + McNemar + the gate.
  Answers the load-bearing question "is the panel good enough to be gold?" **Pure `core/stats` reuse, ~1
  module.** This is the minimum that turns the pipeline from production-only into production+validation.
- **Phase 2 — staged + equivalence.** `tost_proportion`, the pilot→expand `staged_decision`,
  `sample_size_for_ci`.
- **Phase 3 — tier audit + κ + per-judge skew + the cluster-robust CI + full report.**
- **Phase 0 (prereq, parallel).** Rubric parity in the exporter + `anchor.py` + anchor/routing-driven
  export. These feed the human step and are needed before any *real* run, but not before Phase-1 code can
  be written and unit-tested against synthetic labels.

## Gates (why this is designed-not-built)

Three real dependencies make the build well-scoped but deferred:
1. **A vendor-diverse panel run** — a config choice, but it must actually be run on the target corpus.
2. **~100–250 human judgments** (the anchor) — a *fixed* cost (set by target CI half-width, **not** corpus
   size; ~one focused day per the protocol). Phase 1 code can be written + tested on synthetic data, but it
   produces nothing real without the anchor.
3. **A stable substrate** — `context_eval` §6 carries a **"🛑 EXECUTION DEFERRED"** banner: golden built on
   about-to-change games is wasted. Labelling restart is itself gated on v7 (see [[project-ship-roadmap]]).

**Recommendation:** keep this as the shovel-ready plan; build Phase 1 as a working skeleton only if we
want to prove the design on synthetic labels before a real run. Do not stand up the full back-end with no
panel run or human anchor to feed it.

*(Build plan, drafted 2026-06-29. Subject to revision as the labelling + scorer inspection continues.)*
