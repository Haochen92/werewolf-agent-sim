# Batch Dedup: Golden Labels and Prompt Tuning

## Motivation

The per-extraction dedup pipeline handles individual new entries against existing candidates. The batch dedup pipeline operates on entire similarity clusters within a namespace, resolving them into DISCARD groups, MERGE groups, and KEEPs. While per-extraction dedup reached 83-85% accuracy through prompt tuning (v1→v11b), the batch dedup prompts were never updated with the refined decision criteria discovered during that process. This experiment ports those criteria to the batch prompts and evaluates their impact.

Batch dedup is more complex than per-extraction: each cluster can contain 2-25 entries and requires multiple operations (not a single D/K decision). The observation batch prompt retains MERGE (dropped from per-extraction) because the model sees full clusters and can consolidate tactic variants with counts.

## Dataset

Source: `eval_sets/batch_dedup_clusters_v4.json` — 34 clusters (19 observation, 15 strategy) with 522 total items, extracted from v4 memory store pre-dedup.

## Prompt Versions

Each important checkpoint is stored in `evidence/batch_dedup_golden_eval/prompt_versions/`.

### v0 (baseline)

The current batch prompts before any changes. Stored as `prompt_versions/batch_v0_baseline.py`.

Key gaps vs per-extraction v11b:
- No situation comparison section (4 dimensions + retrieval test)
- No approach/outcome comparison criteria (observations)
- No "all three fields must match for DISCARD" calibration
- No before-DISCARD verification checklist
- Strategy DISCARD rewrite instruction lacks "only when needed" guidance
