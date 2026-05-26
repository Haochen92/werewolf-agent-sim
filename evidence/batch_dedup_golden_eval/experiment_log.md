# Batch Dedup: Golden Labels and Prompt Tuning

## Motivation

The per-extraction dedup pipeline handles individual new entries against existing candidates. The batch dedup pipeline operates on entire similarity clusters within a namespace, resolving them into DISCARD groups, MERGE groups, and KEEPs. While per-extraction dedup reached 83-85% accuracy through prompt tuning (v1→v11b), the batch dedup prompts were never updated with the refined decision criteria discovered during that process. This experiment ports those criteria to the batch prompts and evaluates their impact.

Batch dedup is more complex than per-extraction: each cluster can contain 2-25 entries and requires multiple operations (not a single D/K decision). The observation batch prompt retains MERGE (dropped from per-extraction) because the model sees full clusters and can consolidate tactic variants with counts.

## Dataset

Source: `eval_sets/batch_dedup_clusters_v4.json` — 34 clusters (19 observation, 15 strategy) with 522 total items, extracted from v4 memory store pre-dedup.

Golden labels: `eval_sets/batch_dedup_golden_labels.json` — 17 clusters, 149 items. Eval set uses 11 clusters (111 keys): 9 with real DISCARD/MERGE operations + 2 pure-KEEP controls. Golden distribution: KEEP=77, DISCARD=20, MERGE=14.

## Prompt Versions

Each important checkpoint is stored in `evidence/batch_dedup_golden_eval/prompt_versions/`.

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
5. **flash-lite is not viable** for batch dedup — over-merges regardless of prompt quality.
6. **3.5-flash is the recommended model for decisions** — fastest, most accurate, no over-merge tendency. 2.5-pro is close but 50% slower with no accuracy advantage.

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

### Recommendation

For production batch dedup:
- **2.5-pro for everything** is the simplest path — slightly lower action accuracy (83.8% vs 86.5%) but much better merge quality, and pricing is comparable. Fabrication rate needs monitoring but is addressable through prompt refinement.
- **Two-pass pipeline** (3.5-flash decisions → 2.5-pro rewrites) would get best action accuracy + good rewrite quality but adds complexity.
- **3.5-flash with graceful degradation** — accept missing approach/outcome fields and fall back to survivor entry text or concatenation. Cheapest, but loses the merge quality benefit.
