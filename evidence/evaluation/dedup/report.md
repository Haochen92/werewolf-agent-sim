# Dedup — Evaluation Apparatus Report

> **Scope: the apparatus, not the design.** This covers *how we measure* whether dedup meets its objective
> and *how far to trust that measurement* (L1 + L2). The dedup **design** (the 3-pass mechanism, the
> gate-partition, prompt v1→v11b) is the memory-pipeline story and stays in
> [`../../dedup/`](../../dedup/) (`report.md`, `per_extraction/`, `batch_dedup/`). The L0/L1/L2 lens +
> segment skeleton: [`../report.md`](../report.md); reliability ledger: [`../source_map.md`](../source_map.md).
>
> **Verdict: 🟡 PARTIAL — the *decision-maker* is the best-validated instrument in the system (human golden +
> deterministic scorer); the *quality judges* on top are uncalibrated, and the golden numbers are stale.**

## Objective the apparatus targets

Dedup keeps the store from bloating by deciding, for each new memory, **KEEP / DISCARD / MERGE** against
already-stored candidates. So the apparatus must answer two different questions, and it uses two different
instruments for them:
1. **Did dedup make the right decision?** (the *predicate* — keep/discard/merge the right things)
2. **When it merged/rewrote, was the merge any good?** (preservation, no fabrication)

## L1 — the instruments (two layers, very different strength)

### Layer 1 — the deterministic golden-label scorer  *(the strong one)*
- `evaluation/src/experiments/dedup_score.py` (`score()` @ `:223`) — compares a dataset's decisions against a
  **human** golden label file, no LLM. Auto-detects legacy/current label scheme, item-type-aware remap
  (`:29-39`), reports **strict + lenient accuracy, per-label P/R/F1, confusion matrix, per-type breakdown,
  mismatch list**. Honours `also_acceptable` / dual-label sets (`:212-215`).
- Batch sibling: `experiments/batch_dedup_eval.py` scores batch clusters vs `batch_dedup_golden_labels.json`.
- ⚠️ **Neither has a console-script entry** — `python -m` only.

### Layer 2 — the LLM "quality" judges  *(the weak one — machine-on-machine)*
- **Online:** `judges/dedup.py::run_dedup_judge` (gemini-2.5-pro, `:15`; `max_retries=1`, `:100`). Scores a
  captured decision on `DedupScores` (`core/schemas.py:378-416`): `decision_correctness 1-5 · merge_quality
  1-5 · information_preservation 1-5 · fabrication_detected bool · brief_reasoning`. Driven by
  `experiments/dedup_eval.py` → **console script `eval-dedup`** (`pyproject.toml:38`).
- **Batch merge:** `judges/batch_dedup.py::run_batch_merge_judge` (gemini-2.5-pro; `max_retries=1`, `:61`).
  Scores a merge/rewrite on `BatchDedupMergeScores` (`core/schemas.py:342-375`): `retrieval_coverage ·
  merge_quality · information_preservation 1-5 · fabrication_detected bool`. Driven by
  `experiments/batch_dedup_merge_eval.py` (`python -m` only).

### Supporting harness
`dedup_builder.py` (`eval-build-dedup-dataset`) freezes `DedupCase` datasets; `dedup_replay.py` re-runs the
*production* decision through a different model/prompt for A/Bs; `labeling/manual_labelers/batch_dedup_labeler.py`
is the interactive tool that produced the batch golden set (moved from `experiments/` into the repurposed
`labeling/manual_labelers/` home 2026-06-29); `eval_auto_dedup.py` calibrates the embedding-prefilter thresholds.

> **The irony (an apparatus finding).** The measurement that *should* be load-bearing — the deterministic
> golden scorer — has **no first-class command**; the weaker, uncalibrated LLM judge is the one wired as
> `eval-dedup`. The system's strongest instrument is the one you have to know to run by module path.

## L2 — how much to trust it

### The golden sets — the centerpiece (validate the *decision-maker*)
Two **human** golden sets anchor the predicate (not the 1-5 judges):

| Golden set | Size | Labelling | What it scores |
|------------|------|-----------|----------------|
| Online (`frozen_eval_sets/dedup_v2_golden_labels.json`) | **65** labels (K=34, D=30, M/K=1; obs=40, SP=25) | human, **2 sessions + 2 revision rounds** (14 labels changed; the "retrieval test" flipped ~10 D→K) | online KEEP/DISCARD/MERGE accuracy |
| Batch (`frozen_eval_sets/batch_dedup_golden_labels.json`) | 17 clusters / 149 items → eval uses **11 clusters = 111 keys** (KEEP 77 / DISCARD 20 / MERGE 14) | human, via `batch_dedup_labeler.py` | batch per-key decision accuracy |

Anchored accuracy (decision-maker vs human golden):
- **Online** baseline gemini-2.5-flash **78% strict / 80% lenient** (39/50); per-label D P=.82/R=.74, **M
  P=.56/R=.83 (over-merges)**, K P=.83/R=.80. Production endpoint (v11b, D/K only): flash-lite & 3.5-flash
  **83.1%**.
- **Batch** two-pass (flash-lite triage → 2.5-pro verify) **89.2% (99/111)**; 3.5-flash single-pass 86.5%.

This is genuinely the **strongest L2 artifact in the eval system**: human ground truth, deterministic scoring,
documented relabelling rounds, per-class + confusion-matrix reporting, and a cross-game robustness check.

### Why it is still only 🟡
1. **The LLM quality judges are uncalibrated (machine-on-machine).** `DedupScores`/`BatchDedupMergeScores`
   were built *because* the LLM-judge path "had no ground-truth anchor" (`per_extraction/experiment_log.md`
   §①) — and that anchor was built for the *decision*, never for the *quality dimensions*. So `merge_quality`,
   `information_preservation`, and especially **`fabrication_detected`** are unvalidated. The one load-bearing
   number these judges produce — the **33% 2.5-pro merge-fabrication rate** — is itself from an uncalibrated
   judge on **n=9** ops (3/9). The top production risk is asserted by the least-trusted instrument.
2. **Staleness — the golden numbers are not current-code measurements.** Golden labels were sampled on the
   **v4-era store + pre-v6 prompts**, before the **deterministic gate** and the per-dimension `situation`
   fields existed. The live pipeline (v6.1 prompt + gate) would change *which candidates the LLM even sees*,
   so 83.1% does not describe the shipping code.
3. **Backend shift confounds the series.** Google AI Studio through v9d, **Vertex from v10** — moves outputs
   even at temp 0 (flash-lite v10: 76.9% Google vs 73.8% Vertex). Pre/post-v10 numbers aren't directly
   comparable. *(See [`../source_map.md`](../source_map.md) drift row + `feedback-vertex-backend-affects-scores`.)*
4. **Prefilter open loop.** Embedding-prefilter thresholds are "zero-error" on the golden set only because the
   0.90 SP gap was a 25-case artifact (the 232-case cross-game set forced 0.93); auto-decision coverage caps
   at ~15-30% (topic-not-stance ceiling); the promised **wild-trace re-validation has never run**.
5. **✅ Silent-failure bug — FIXED 2026-06-28.** `judges/batch_dedup.py` (handler now at `:87`, shifted up from `:86` by the added `ValidationError` import) had `except
   (json.JSONDecodeError, Exception)` — `Exception` subsumed `JSONDecodeError`, swallowing *every* error (API,
   schema-validation, attribute) into one "parse failure → None", silently dropped from aggregates. Fixed to
   match the online judge (`dedup.py:138-147`): split into `(JSONDecodeError, ValidationError)` → "invalid
   scores" vs a catch-all `Exception` → "call failed" (added the `ValidationError` import). Uncommitted.
6. **Small-N throughout** — online golden 65, batch 111 keys / 11 clusters, fabrication rate n=9; 3.5-flash is
   non-deterministic near its output ceiling (86.5% best vs 81.0% worst, same prompt).

**No leak** in either path (the quality judges never see the golden label; the scorer is deterministic).

## Verdict + cheapest credible upgrade

**🟡 PARTIAL.** Decision-maker measurement = ✅ validated (the system's best); overall apparatus = 🟡 because
the quality judges are uncalibrated, the golden accuracy is on stale code/backend, and the prefilter
re-validation is open.

**Cheapest credible upgrade:** hand-label ~20-30 of the **already-frozen** 2.5-pro merge operations
(`../../dedup/batch_dedup/data/merge_quality_*.json`) for fabrication true/false and score
`batch_dedup_merge_eval`'s `fabrication_detected` against them. Zero new generation — a read-and-label pass —
and it calibrates the single highest-stakes uncalibrated signal (the 33% fabrication rate the report leans on
to gate the offline pass). Second-cheapest: give `dedup_score.py` a console entry and re-run it on
current-prompt replays to retire the staleness gap.

## Evidence (code + L2 artifacts)

- **Code (the instruments):** `evaluation/src/judges/dedup.py`, `judges/batch_dedup.py`,
  `core/schemas.py::{DedupScores,BatchDedupMergeScores}`, `experiments/{dedup_score,dedup_eval,dedup_replay,
  dedup_builder,batch_dedup_eval,batch_dedup_merge_eval}.py`.
- **L2 artifacts (pointed-at — see colocation note):** golden labels
  `evaluation/frozen_eval_sets/{dedup_v2_golden_labels,batch_dedup_golden_labels}.json`; frozen results
  `../../dedup/per_extraction/data/dedup_score_original_v2.json`, `../../dedup/batch_dedup/data/eval_*.json`,
  `../../dedup/batch_dedup/data/merge_quality_*.json`; prefilter data `../../dedup/embedding_prefilter/data/`.

## Colocation call (JIT decision, 2026-06-28)

**Original folder stays put; nothing moved — all pointed-at.** Rationale: the two golden label files live in
the **live data plane** (`frozen_eval_sets/`) and are referenced by live code (`eval_auto_dedup.py`,
`batch_dedup_eval.py:400`); `golden_eval/embedding_cache.json` is a **hard default** in
`fine_tuning/cross_encoder/dedup_prefilter/eval_modal.py:180` — moving it silently breaks the Modal eval. The
frozen result JSONs *are* clean pure-L2, but they're referenced by their L0 `experiment_log.md` siblings, so
moving them would break the design log's links for no real gain. The key numbers are distilled into the tables
above, giving this report standalone value without a physical move.

*(Inspected 2026-06-28.)*
