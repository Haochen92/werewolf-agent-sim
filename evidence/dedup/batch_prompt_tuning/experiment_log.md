# Batch Dedup: Golden Labels and Prompt Tuning

## Motivation

The per-extraction dedup pipeline handles individual new entries against existing candidates. The batch dedup pipeline operates on entire similarity clusters within a namespace, resolving them into DISCARD groups, MERGE groups, and KEEPs. While per-extraction dedup reached 83-85% accuracy through prompt tuning (v1→v11b), the batch dedup prompts were never updated with the refined decision criteria discovered during that process. This experiment ports those criteria to the batch prompts and evaluates their impact.

Batch dedup is more complex than per-extraction: each cluster can contain 2-25 entries and requires multiple operations (not a single D/K decision). The observation batch prompt retains MERGE (dropped from per-extraction) because the model sees full clusters and can consolidate tactic variants with counts.

## Dataset

Source: `eval_sets/batch_dedup_clusters_v4.json` — 34 clusters (19 observation, 15 strategy) with 522 total items, extracted from v4 memory store pre-dedup.

Golden labels: `eval_sets/batch_dedup_golden_labels.json` — 17 clusters, 149 items. Eval set uses 11 clusters (111 keys): 9 with real DISCARD/MERGE operations + 2 pure-KEEP controls. Golden distribution: KEEP=77, DISCARD=20, MERGE=14.

## Prompt Versions

Each important checkpoint is stored in `evidence/dedup/batch_prompt_tuning/prompt_versions/`.

### v0 (baseline)

The original batch prompts before any changes. Stored as `prompt_versions/batch_v0_baseline.py`.

Key gaps vs per-extraction v11b:
- No situation comparison section (4 dimensions + retrieval test)
- No approach/outcome comparison criteria (observations)
- No "all three fields must match for DISCARD" calibration
- No before-DISCARD verification checklist
- Strategy DISCARD rewrite instruction lacks "only when needed" guidance

### v1 (ported per-extraction criteria)

Stored as `prompt_versions/batch_v1_criteria.py`. Ported all refined criteria from per-extraction tuning:
- Situation comparison (4 dimensions + retrieval test) for both prompts
- Approach/outcome comparison criteria for observations
- Field-match calibration (MERGE needs situation+outcome; DISCARD needs all three)
- BEFORE GROUPING verification checklist for strategy DISCARD
- Expanded decision test with confidence posture and opposite action examples
- "Only rewrite when needed" guidance for strategy DISCARD

### v2 (indexed keys + anti-over-merge)

Stored as `prompt_versions/batch_v2_anti_overmerge.py`. Two structural changes:
- **Numbered indices**: Entries formatted as [1], [2], ... instead of UUIDs. Remapped back to real keys after LLM response. Eliminated UUID truncation on longer prompts and fixed 3.5-flash JSON parse failure on 23-entry clusters.
- **BEFORE MERGING checklist**: Replaced "MERGE REQUIRES" with explicit retrieval-diversity gate and merge group size warning (>3-4 entries is a red flag). Changed observation calibration to "when in doubt KEEP".

### v3 (remove KEEP calibration note) — current

Stored as `prompt_versions/batch_v3_no_keep_bias.py`. Removed "when in doubt KEEP" calibration note from observation prompt — it overcorrected 3.5-flash which was already conservative. Kept all other v2 changes. Also lowered `DEFAULT_MAX_CLUSTER_SIZE` from 25 to 15.

## Results

### Model comparison (v1 prompts, UUIDs)

| Model | Accuracy | Time | Notes |
|---|---|---|---|
| gemini-3.5-flash | 89.8% (79/88) | 357s | Cluster 4 JSON parse failure (23 entries) |
| gemini-2.5-pro | 72.1% (80/111) | 687s | Heavy over-merge: 12 KEEP→MERGE |
| gemini-3.1-flash-lite (medium) | 69.4% (77/111) | 126s | Heavy over-merge: 14 KEEP→MERGE |

### Model comparison (v3 prompts, indexed keys)

| Model | Accuracy | Time | Notes |
|---|---|---|---|
| gemini-3.5-flash | 86.5% (96/111) | 343s | All clusters work, 0 KEEP→MERGE |
| gemini-2.5-pro | 83.8% (93/111) | 513s | Over-merge fixed: 12→2 KEEP→MERGE |
| gemini-3.1-flash-lite (medium) | 72.1% (80/111) | 145s | Still over-merges: 19 KEEP→MERGE |

### Accuracy by cluster size (v3)

| Size | Clusters | 3.5-flash | 2.5-pro |
|---|---|---|---|
| 2-5 | C5, C20, C33 | 100% | 100% |
| 8-10 | C0, C11, C16, C21 | 80-100% | 80-100% |
| 11-16 | C14, C25, C28 | 64-100% | 64-100% |
| 23 | C4 | 74% | 65% |

Cluster 25 (strategy, 11 entries) is consistently hard — 64% for both models.

### Key findings

1. **Indexed keys are strictly better** — eliminates UUID truncation and JSON parse failures, saves tokens, no downside.
2. **BEFORE MERGING checklist was the key improvement** for 2.5-pro — reduced over-merge from 12 to 2 errors.
3. **Calibration bias should be neutral** — "when in doubt KEEP" hurt 3.5-flash; "when in doubt DISCARD" only applies to strategy. The right bias depends on downstream retrieval quality and agent strategy application, not on the prompt.
4. **Cluster size limit of 15 is well-supported** — all models degrade sharply above 15 entries.
5. **flash-lite is not viable as a standalone model** for batch dedup — over-merges regardless of prompt quality. However, its high KEEP precision (91.8%) and DISCARD precision (86.7%) make it effective as a triage pass in a two-pass pipeline (see Time and Cost Analysis).
6. **Two-pass pipeline (flash-lite triage → 2.5-pro verification) is the recommended production approach** — combines flash-lite's speed and KEEP/DISCARD precision with 2.5-pro's merge quality, reducing 2.5-pro API volume by ~69% (see Time and Cost Analysis). **3.5-flash remains the best single-model option** — fastest, most accurate, no over-merge tendency. 2.5-pro is close but 50% slower with no accuracy advantage.

## Merge Rewrite Quality

After scoring per-key action accuracy, we evaluated the quality of merged text (merged_situation, merged_approach, merged_outcome) using a separate LLM judge (gemini-2.5-pro). This matters because a correct MERGE decision with bad rewrite text degrades the memory store.

### Judge dimensions

- **Retrieval coverage** (1-5): Will the merged situation be retrieved by the same queries that matched each original entry?
- **Merge quality** (1-5): Is the rewritten text well-formed, specific, and an improvement?
- **Information preservation** (1-5): Were important nuances preserved (tactic counts, conditions, mechanisms)?
- **Fabrication detected** (bool): Did the rewrite introduce context not in source entries?

Pipeline: `evaluation/experiments/batch_dedup_merge_eval.py` extracts MERGE/DISCARD-with-rewrite operations from eval result JSONs, pairs with source entries from the cluster file, and sends to the judge.

### Results (v3 prompts)

| Model | Cases | Retrieval Coverage | Merge Quality | Info Preservation | Fabrication Rate |
|---|---|---|---|---|---|
| gemini-3.5-flash | 6 | 4.33 | 3.00 | 1.67 | 0% |
| gemini-2.5-pro | 6 | 4.33 | 4.00 | 4.00 | 33% |

### Analysis

**3.5-flash drops merged_approach and merged_outcome fields entirely** during MERGE operations — it only outputs merged_situation. This is the root cause of the 1.67 information preservation score. Three attempts to fix this via prompt/schema changes all failed:

1. Verbose "REQUIRED for MERGE" schema descriptions — caused 3+ cluster JSON parse failures
2. Detailed per-field merge rules in prompt (~7750 chars) — 4 cluster failures
3. Minimal one-sentence "all three fields are required" addition (~7425 chars) — 3 cluster failures

The observation prompt at ~7383 chars is at 3.5-flash's structured output capacity limit. Any additional instruction text triggers JSON parse failures on MERGE-heavy clusters. This is a model limitation, not a prompt issue.

**3.5-flash run-to-run variance**: Re-runs with identical v3 prompts showed different clusters failing JSON parse (C25 on one run, none on another) and C14 accuracy fluctuating between 40-100%. The model is non-deterministic near its capacity boundary. Best observed: 86.5% (96/111). Worst same-prompt re-run: 81.0% (81/100, 1 cluster failed).

**2.5-pro writes high-quality merges** with good information preservation (4.0/5) but fabricates 33% of the time — introducing game context not present in source entries.

## Time and Cost Analysis

### Per-model performance on 111-key eval set (11 clusters, v3 prompts)

| Model | Accuracy | Total Time | Time/Cluster | Relative Speed |
|---|---|---|---|---|
| gemini-3.1-flash-lite (medium) | 72.1% | 145s | 13.2s | 1.0x (baseline) |
| gemini-3.5-flash | 86.5% | 342s | 31.1s | 2.4x slower |
| gemini-2.5-pro | 83.8% | 513s | 46.7s | 3.5x slower |

At production scale (v4 store: 522 items, ~50 clusters), a full 2.5-pro batch dedup run takes 30-40 minutes. This makes it a periodic maintenance operation, not something to run after every game. Cost per run is comparable across models (2.5-pro and 3.5-flash have similar per-token pricing), but the time cost is significant.

### Two-pass pipeline: flash-lite triage + 2.5-pro verification

Analysis of flash-lite's per-prediction precision revealed an asymmetric error pattern that enables a two-pass pipeline:

**Flash-lite confusion matrix (v3 prompts, 111 keys):**

| Golden ↓ \ Model → | KEEP | DISCARD | MERGE | MISSING |
|---|---|---|---|---|
| KEEP (77) | **56** | 2 | 19 | 0 |
| DISCARD (20) | 2 | **13** | 4 | 1 |
| MERGE (14) | 3 | 0 | **11** | 0 |

**Flash-lite precision by predicted action:**

| Prediction | Precision | Interpretation |
|---|---|---|
| KEEP | 56/61 = **91.8%** | Highly reliable — only 5 errors out of 61 predictions |
| DISCARD | 13/15 = **86.7%** | Reliable — only 2 errors out of 15 predictions |
| MERGE | 11/34 = **32.4%** | Unreliable — 23 of 34 predictions were wrong (19 KEEP, 4 DISCARD) |

Flash-lite's dominant error mode is over-merging: it flags entries as MERGE that should be KEEP. But when it says KEEP or DISCARD, it's right ~90% of the time. This makes it an effective triage model.

**Two-pass design:**

1. **Pass 1 (flash-lite, medium thinking):** Runs on all clusters. KEEP and DISCARD decisions are trusted. All MERGE decisions are escalated to pass 2.
2. **Pass 2 (2.5-pro):** Only processes the keys flash-lite flagged as MERGE (~30% of total). Re-decides KEEP/MERGE/DISCARD and writes merge text where appropriate.

**Projected cost/time savings on 111-key eval set:**

- Pass 1: 11 clusters at 13.2s/cluster = ~145s (111 keys)
- Pass 2: ~34 MERGE-flagged keys across fewer, smaller clusters at 46.7s/cluster ≈ ~140s
- Total: ~285s vs 513s for pure 2.5-pro (44% time reduction)
- 2.5-pro API volume: ~34 keys vs 111 keys (69% reduction)

At production scale (522 items), the savings compound because flash-lite processes the full store cheaply and only the ambiguous MERGE cases reach 2.5-pro.

**For strategy points** (KEEP/DISCARD only, no MERGE operation), flash-lite may be sufficient on its own — the over-merge problem doesn't apply. This needs separate validation.

### Recommendation

For production batch dedup:
- **Two-pass pipeline** (flash-lite triage → 2.5-pro verification + rewrites) is the recommended path. Flash-lite's KEEP/DISCARD precision is high enough to trust, and escalating only MERGE decisions to 2.5-pro dramatically reduces cost and time while preserving merge quality.
- **2.5-pro for everything** remains the simplest fallback — slightly lower action accuracy (83.8% vs 86.5%) but no pipeline complexity. Viable for small stores or infrequent runs.
- **3.5-flash with graceful degradation** — accept missing approach/outcome fields and fall back to survivor entry text. Cheapest single-pass option, but loses merge quality benefit.

## Next Steps

1. ~~**Implement and validate the two-pass pipeline**~~ — **Done.** Two-pass infrastructure added to `memory_batch_deduplication.py` (CLI: `--two-pass`, `--triage-model`, `--verify-model`). End-to-end accuracy validation on golden eval set is pending.
2. ~~**Measure retrieval impact of v3-calibrated store**~~ — **Done.** v4_deduped_v2 (v3 prompts, 432 items) outperforms both v4 and v4_deduped on retrieval quality at n=39. See [store_retrieval_impact](../store_retrieval_impact/report.md#phase-2).
3. **Validate flash-lite-only for strategy points** — strategy uses only KEEP/DISCARD (no MERGE), so flash-lite's over-merge weakness does not apply. Run a dedicated eval to confirm standalone flash-lite is sufficient for strategy batch dedup.
4. **Integrate batch dedup into the game pipeline** — once the pipeline approach is validated, wire batch dedup into the post-game flow as a periodic maintenance operation.
