# Evidence Directory

Experiment reports documenting the evaluation and tuning of the werewolf agent memory system. Each subdirectory contains a self-contained experiment with its report, eval configs, eval results, and supporting artifacts.

## Organization

Experiments are grouped by subsystem. Within each group, experiments are independent unless noted otherwise.

### [dedup/](dedup/) — Deduplication

Removing redundant entries from the memory store, both at batch level (periodic maintenance) and per-extraction level (after each game).

| Experiment | Sample | Date | Status |
|---|---|---|---|
| [store_retrieval_impact](dedup/store_retrieval_impact/report.md) | n=5 + n=39 | May 23, 26 | Phase 1 (n=5) superseded; phase 2 (n=39) is current |
| [batch_prompt_tuning](dedup/batch_prompt_tuning/experiment_log.md) | n=111 golden | May 26 | Current |
| [per_extraction](dedup/per_extraction/experiment_log.md) | n=50 golden | May 26 | Current |
| [embedding_prefilter](dedup/embedding_prefilter/) | n=65+232 | May 26 | Current |

`store_retrieval_impact` and `batch_prompt_tuning` form a timeline — see [dedup/README.md](dedup/README.md).

### [retrieval/](retrieval/) — Retrieval Pipeline

Tuning how memories are retrieved at game time: filtering, reranking, and capacity limits.

| Experiment | Sample | Date | Notes |
|---|---|---|---|
| [filtering](retrieval/filtering/report.md) | n=5 | May 23 | Pre-dedup store; filtering shown unnecessary on clean store |
| [reranking](retrieval/reranking/report.md) | n=5 | May 23 | Strategy-only reranking on v4_deduped; small sample |
| [capacity_limits](retrieval/capacity_limits/report.md) | n=120 | May 24 | Observations-only, top_k=3 vs 5 |

`filtering` and `reranking` used n=5 on v4_deduped (v0 prompts). Their directional findings hold but absolute numbers are noisy.

### [extraction/](extraction/) — Extraction Quality

Quality of what goes into the memory store and what queries are generated at retrieval time.

| Experiment | Sample | Date | Notes |
|---|---|---|---|
| [quality](extraction/quality/report.md) | n=48 | May 24-26 | Multi-phase: judge comparison, per-role, model comparison |
| [situation_summary](extraction/situation_summary/report.md) | n=15 | May 24 | 4-model comparison for situation summary generation |

### [memory_system/](memory_system/) — Memory System Impact

End-to-end measurements of whether and how episodic memory helps gameplay.

| Experiment | Sample | Date | Notes |
|---|---|---|---|
| [effectiveness](memory_system/effectiveness/report.md) | n=30 games | May 24 | With/without memory; strongest evidence memory works |
| [ablation](memory_system/ablation/report.md) | n=120 | May 24 | Observations vs strategy points vs both |
| [strategy_adoption](memory_system/strategy_adoption/report.md) | n=120 | May 24 | Adoption tracking prompt v1-v3 |

## Reading Guide

Reports vary in maturity. The key distinction:

- **n=5 experiments** (filtering, reranking, store_retrieval_impact phase 1): Directional signals only. Useful for understanding the evaluation journey but absolute numbers should not be cited. These predate the batch dedup prompt tuning (v0 prompts). store_retrieval_impact was extended with a phase 2 (n=39) that supersedes the original numbers.
- **n=15-50 experiments** (situation_summary, extraction_quality, golden label evals): Moderate confidence. Golden label evals are deterministic and don't suffer from small-sample noise the way judge-scored evals do.
- **n=120+ experiments** (ablation, capacity_limits, adoption): High confidence. Large sample, robust methodology.

All experiments use the v4 memory store family (522 base items from 48 games). Eval judge is gemini-2.5-flash unless noted.
