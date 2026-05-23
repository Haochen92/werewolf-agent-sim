# Store Deduplication: Fixing Redundancy at the Source

## The Problem

After building the retrieval filtering pipeline (dedup gate, MMR, per-situation cap), evaluation revealed that the biggest quality bottleneck wasn't retrieval sophistication — it was memory content. The v4 store contained 522 items, many of which were near-duplicates: observations teaching the same strategic lesson through different game anecdotes, and strategy points giving identical advice with minor phrasing variations.

The filtering pipeline improved efficiency on this dirty store (redundancy ratio from 51.7% to 44.7% for observations), but it was treating the symptom. The question was whether cleaning the store itself would produce better results than any amount of retrieval-time filtering.

## The Approach

The batch deduplication pipeline uses agglomerative clustering (cosine similarity threshold 0.70) to group semantically similar items, then sends each cluster to gemini-2.5-pro for decisions:

- **Observations**: DISCARD, MERGE, or KEEP. Merge consolidates multiple game anecdotes teaching the same lesson into a single, more general observation.
- **Strategy points**: DISCARD or KEEP. Strategy points are prescriptive rules, so merging is harder — they're either duplicates or they're not.

### Cluster Size Fix

During the first run, we discovered that the pipeline capped cluster size at 8 and naively chunked larger clusters into sequential groups. A cluster of 19 items became [8, 8, 3], with no cross-chunk comparison — duplicates landing in different chunks survived. Raising the cap from 8 to 25 fixed this, and the second run caught significantly more duplicates.

| Run | Max Cluster | Observations | Strategy Points | Total |
|---|---|---|---|---|
| Original v4 | — | 324 | 198 | 522 |
| Dedup (cap=8) | 8 | 217 (-33%) | 167 (-16%) | 384 (-26%) |
| Dedup (cap=25) | 25 | 150 (-54%) | 167 (-16%) | 297 (-43%) |

Observations saw the biggest cleanup because their redundancy pattern is "same lesson, different game" — exactly what MERGE handles well. Strategy points were already more distinct; 31 true duplicates were discarded.

## Evaluation

We ran the same 5 frozen eval cases (2 healer, 2 investigator, 1 villager) against both the original v4 and deduped v4 stores, using baseline retrieval (no filtering, no reranking) with gemini-2.5-flash as the judge.

### Observations (n=5 scenarios)

| Metric | v4 baseline | v4_deduped baseline |
|---|---|---|
| Avg retrieved | 4.60 | 4.00 |
| Relevance | 4.40 | 4.60 |
| Efficiency | 3.00 | **4.00** |
| Unique Lessons | 2.20 | **3.00** |
| Redundancy ratio | 51.7% | **25.0%** |

### Strategy Points (n=5 scenarios)

| Metric | v4 baseline | v4_deduped baseline |
|---|---|---|
| Avg retrieved | 4.00 | 3.80 |
| Relevance | 3.00 | 3.20 |
| Efficiency | 2.00 | 1.80 |
| Unique Lessons | 1.00 | 1.20 |
| Redundancy ratio | 77.0% | 72.3% |

Observations improved significantly across the board — efficiency jumped a full point, unique lessons increased by 36%, and redundancy nearly halved. The store dedup removed the duplicate anecdotes, so retrieval naturally surfaces more diverse items without any filtering.

Strategy points barely changed. The redundancy ratio stayed above 70% even on the clean store. This confirmed that the strategy point problem isn't duplication — it's content coverage. The store lacks entries for certain common situations (early-game healer, information-starved voting scenarios).

## Filtering on a Clean Store

We then tested whether the retrieval filtering pipeline (dedup gate at 0.92, MMR λ=0.8) would stack with store dedup. It didn't.

### Observations: v4_deduped + filtering

| Metric | Baseline | + Filtering |
|---|---|---|
| Relevance | 4.60 | 4.00 |
| Efficiency | 4.00 | 3.60 |
| Unique Lessons | 3.00 | 3.00 |
| Redundancy ratio | 25.0% | 40.0% |

Filtering made scores *worse*. Two mechanisms caused this:

1. **Wider retrieval pulled in less relevant items.** The filtering pipeline uses top_k=10 (vs baseline's 3) to give dedup and MMR room to work. On a clean store, this wider net catches topically related but situation-mismatched items that the simpler top-3 would have excluded.

2. **The dedup gate over-removed.** In one case, it treated two observations sharing vocabulary ("endgame consensus voting") as duplicates, even though one taught a lesson about passive communication danger and the other about vote alignment. On a dirty store with true duplicates, this aggressiveness helped. On a clean store, it hurt.

**Conclusion: store dedup and retrieval filtering solve the same problem (redundancy). Applying both is over-correction.** The filtering layer is kept as a configurable safety net for periods between batch dedup runs, but it's off by default when the store is clean.

## What I Learned

**Fix the root cause, not the symptom.** The retrieval filtering pipeline was a reasonable first attempt, but it was compensating for store-level duplication with retrieval-time tricks. Cleaning the store directly was simpler, more effective, and didn't risk accidentally removing useful items.

**Cluster size matters for batch operations.** The naive chunking at max_cluster_size=8 silently allowed cross-chunk duplicates to survive. This is a general lesson for any batch processing pipeline — when the batch boundary is arbitrary, items near the boundary interact poorly.

**Content coverage is the real bottleneck.** After both store dedup and retrieval filtering, strategy points still showed 70%+ redundancy and unique_lessons near 1. The store simply doesn't contain entries for many common situations. No amount of retrieval engineering can surface knowledge that doesn't exist.

## Artifacts

| File | Description |
|---|---|
| [01_v4_vs_v4deduped_baseline.md](01_v4_vs_v4deduped_baseline.md) | Retrieval eval: v4 vs v4_deduped, baseline pipeline |
| [02_v4deduped_with_filtering.md](02_v4deduped_with_filtering.md) | Retrieval eval: v4_deduped with filtering pipeline |

## Code References

- `Agents/memory_batch_deduplication.py` — batch dedup pipeline, cluster size cap, Langfuse tracing
- `Agents/memory_stores/v4_deduped/` — deduped store output
- `eval_configs/store_dedup_comparison.json` — v4 vs v4_deduped eval config
- `eval_configs/deduped_filtering.json` — filtering on clean store eval config
