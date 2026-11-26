# Deduplication

How the project keeps duplicate observations and lessons out of the memory store.

- **[report.md](report.md)**: how dedup runs today, layer by layer, with the evidence behind each layer
  and what is built but switched off. Start here.
- **[experiment_log.md](experiment_log.md)**: the journey in time order, from cosine-only dedup to the
  structured gate, with the dated audit of where the code moved after June 2026.

The studies, one folder each:

| Record | Question |
|---|---|
| [per_extraction/](per_extraction/experiment_log.md) | How well does the one-at-a-time judge tell a duplicate from a distinct lesson? (the 65-case labelled set) |
| [batch_dedup/](batch_dedup/experiment_log.md) | How should the whole-store pass cluster, which model should judge, and can it merge safely? (the 111-entry labelled set) |
| [embedding_prefilter/](embedding_prefilter/experiment_log.md) | Which cases can an embedding check settle without a judge? (the 65 and 232 cases) |
| [store_retrieval_impact/](store_retrieval_impact/experiment_log.md) | Does a deduplicated store retrieve better, and how hard should dedup cut? (5, then 40 scenarios) |
| [incremental_convergence.md](incremental_convergence.md) | Why repeated batch runs erode a store, and the two fixes (diagnosis record) |
| [dedup_clustering_and_sp_extraction_plan.md](dedup_clustering_and_sp_extraction_plan.md) | The June 2026 plan that produced the gate (historical) |
| [batch_architecture.md](batch_architecture.md) | A pointer: its content moved into the report on 2026-10-26 |

*2026-10-26: this file was a per-experiment index with the 39-scenario retrieval table; the table's
observation columns are now in the report, and the full table is in the retrieval-impact log, phase 2.
The earlier version is in git history.*
