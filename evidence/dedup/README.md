# Deduplication Experiments

All experiments related to identifying and removing redundant entries from the memory store.

## Timeline: Batch Dedup Retrieval Impact

These two experiments form a progression — the second supersedes the first with larger sample size and tuned prompts.

### Phase 1: [Store Retrieval Impact](store_retrieval_impact/report.md) (May 23)

First measurement of whether batch dedup improves retrieval quality. Compared v4 (522 items) vs v4_deduped (320 items, v0 prompts) on **n=5 frozen cases** with baseline retrieval.

Key finding at the time: observations efficiency jumped from 3.00 to 4.00 and redundancy halved. This motivated all subsequent dedup work.

**Caveat**: The n=5 sample was optimistic. The full n=39 replication (May 26) showed v4_deduped actually *loses* observation relevance (-0.28 mean delta, 2W/24T/14L vs v4) with zero efficiency gain. The aggressive 39% store reduction (v0 prompts) crossed the line into information loss.

### Phase 2: [Batch Prompt Tuning](batch_prompt_tuning/experiment_log.md) + [Retrieval Impact](store_retrieval_impact/report.md#phase-2) (May 26)

Principled evaluation of batch dedup prompts using 111-key golden label set. Tuned prompts from v0 through v3, adding anti-over-merge calibration, indexed keys, and verification checklists. Tested three models (3.5-flash, 2.5-pro, flash-lite).

Then measured retrieval impact of the v3-calibrated store on the full 40-case eval set (n=39 complete). Results:

| Store | Obs Relevance | Obs Efficiency | Obs Unique | Strat Relevance | Strat Efficiency |
|---|---|---|---|---|---|
| v4 (522 items) | 4.51 | 3.26 | 2.62 | 3.85 | 2.87 |
| v4_deduped (320, v0) | 4.26 | 3.26 | 2.41 | 3.62 | 3.00 |
| **v4_deduped_v2 (432, v3)** | **4.44** | **3.44** | **2.82** | 3.72 | 2.95 |

v4_deduped_v2 is the best store: highest observation efficiency and unique lessons, competitive relevance. Conservative dedup (17% reduction) outperforms both no dedup and aggressive dedup (39% reduction).

## Standalone Experiments

### [Per-Extraction Prompt Tuning](per_extraction/experiment_log.md) (May 26)

Golden label evaluation of the per-extraction dedup pipeline (runs after every game on individual new entries). Tuned prompts v1 through v11b, reaching 83-85% accuracy. Includes embedding pre-filter calibration for deterministic auto-decisions on easy cases.

### [Embedding Pre-filter Data](embedding_prefilter/) (May 26)

Cached embeddings and golden labels used by the pre-filter calibration in the per-extraction experiment. Contains cross-game validation datasets (232 cases) and embedding caches at multiple dimensionalities.
