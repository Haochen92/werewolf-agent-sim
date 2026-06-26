# Store dedup → retrieval impact — experiment log

**What this is.** The measurement that *started* the dedup workstream — and the one that decided **what
earns its keep at retrieval time.** Two questions, one eval harness:

1. Does cleaning the memory store actually improve retrieval, and how hard should it clean?
2. Does the retrieval-time *filtering* pipeline (dedup gate + MMR + per-situation cap) still earn its
   keep once the store is clean — or does store-dedup solve the redundancy at the root, leaving filtering
   to solve the same problem a second time?

Two phases — an n=5 first look (May 23) and an n=39 replication (May 26) that **corrected** it.

**Bottom line.** Conservative store-dedup helps retrieval (mostly for observations); aggressive
over-merging *hurts*. Retrieval-time filtering does **not** stack on a clean store — it over-corrects on
redundancy that's already gone — so it ships **off by default**. And the most durable finding of all:
**strategy points are a content-coverage problem, not a dedup problem** — no amount of dedup or filtering
moves their numbers, because the store simply lacks entries for many common situations.

*Scope note: this study runs on `baseline retrieval (no filtering, no reranking)` as the control — the
CE **reranker is not evaluated here** (that's a separate study). The "did it earn its keep" verdict is
about the retrieval-time **filtering** layer.*

The destination (how dedup works today) is the folder's [report.md](../report.md); the chronological
overview of the whole effort is [../experiment_log.md](../experiment_log.md).

**Reading contract.** Phases are in time order; the n=5 verdict is shown **as it stood** and then
falsified in place by the n=39 replication — the correction is the point, not an edit to hide. Raw
per-case judge dumps are in [data/](data/).

---

## The Problem

After building the retrieval filtering pipeline (dedup gate, MMR, per-situation cap), evaluation revealed that the biggest quality bottleneck wasn't retrieval sophistication — it was memory content. The v4 store contained 522 items, many of which were near-duplicates: observations teaching the same strategic lesson through different game anecdotes, and strategy points giving identical advice with minor phrasing variations.

The filtering pipeline improved efficiency on this dirty store (redundancy ratio from 51.7% to 44.7% for observations), but it was treating the symptom. The question was whether cleaning the store itself would produce better results than any amount of retrieval-time filtering.

## The Approach

The batch deduplication pipeline groups semantically similar items into **size-capped similarity clusters** (cosine threshold 0.70 — the conservative `bounded` mode), then sends each cluster to gemini-2.5-pro for decisions:

- **Observations**: DISCARD, MERGE, or KEEP. Merge consolidates multiple game anecdotes teaching the same lesson into a single, more general observation.
- **Strategy points**: DISCARD or KEEP. Strategy points are prescriptive rules, so merging is harder — they're either duplicates or they're not.

(*How* the clustering method was chosen — `bounded` vs `connected`/`agglomerative`, and why a single similarity threshold won't cut cleanly — is the [batch_dedup](../batch_dedup/experiment_log.md) chapter's *Forming the clusters*. This study used the cap-bounded default; the size cap is the subject of the next section.)

### Cluster Size Fix

During the first run we hit a cap artifact: with `max_cluster_size=8`, a group of 19 mutually-similar items couldn't all land in one cluster — the cap split them into [8, 8, 3], and items that fell into different sub-clusters were **never compared**, so duplicates straddling the boundary survived. Raising the cap from 8 to 25 fixed it, and the second run caught significantly more duplicates. (The cap was later settled at **15** for the live loop once the eval showed accuracy falls off a cliff above ~15 entries — see [batch_dedup](../batch_dedup/experiment_log.md); the exact 15/25 value doesn't change this study's *direction*.)

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

## Phase 2: v3 Prompt Calibration and Larger Sample (n=39)

The original evaluation above used n=5 frozen cases and v0 (untuned) batch dedup prompts. After tuning batch prompts through v1-v3 (see [batch_dedup](../batch_dedup/experiment_log.md)), we created a third store — v4_deduped_v2 — using v3 prompts, then re-evaluated all three stores on the full 40-case eval set (39 complete).

### Store sizes

| Store | Prompts | Observations | Strategy Points | Total | Reduction |
|---|---|---|---|---|---|
| v4 | — | 324 | 198 | 522 | — |
| v4_deduped | v0 (untuned) | 150 | 167 | 320 | 39% |
| v4_deduped_v2 | v3 (tuned) | 269 | 163 | 432 | 17% |

The v3 prompts are far more conservative — anti-over-merge calibration, BEFORE MERGING checklist, and indexed keys eliminated the aggressive merging that v0 performed.

### Observations (n=39 scenarios)

| Metric | v4 | v4_deduped | v4_deduped_v2 |
|---|---|---|---|
| Avg retrieved | 5.1 | 4.6 | 5.0 |
| Relevance | 4.51 | 4.26 | 4.44 |
| Efficiency | 3.26 | 3.26 | **3.44** |
| Unique Lessons | 2.62 | 2.41 | **2.82** |
| Redundancy ratio | 46% | 46% | **42%** |

### Strategy Points (n=39 scenarios)

| Metric | v4 | v4_deduped | v4_deduped_v2 |
|---|---|---|---|
| Avg retrieved | 4.4 | 4.4 | 4.3 |
| Relevance | 3.85 | 3.62 | 3.72 |
| Efficiency | 2.87 | 3.00 | 2.95 |
| Unique Lessons | 1.87 | 1.79 | 1.90 |
| Redundancy ratio | 59% | 59% | 58% |

### Per-case win/loss analysis (v4_deduped_v2 vs v4)

| Metric | Obs W/T/L | Strat W/T/L |
|---|---|---|
| Relevance | 2/31/7 | 1/34/5 |
| Efficiency | 9/26/5 | 4/35/1 |
| Unique Lessons | 9/26/5 | 4/33/3 |

### Phase 2 findings

**The n=5 sample was optimistic about v4_deduped.** At n=39, v4_deduped (v0 prompts) actually *hurts* relevance for observations (-0.28 mean delta, 2W/24T/14L) without improving efficiency at all. The aggressive 39% store reduction crossed the line from removing redundancy into removing useful entries.

**v4_deduped_v2 (v3 prompts, 17% reduction) is the best of the three stores.** It achieves the highest efficiency (3.44) and unique lessons (2.82) for observations while keeping relevance close to the raw store (4.44 vs 4.51). The conservative dedup preserves diverse entries that v0 would have aggressively merged.

**v4_deduped_v2 clearly dominates v4_deduped.** Across both observations and strategy points, v4_deduped_v2 wins on relevance (+0.17 obs, +0.10 strat), unique lessons (+0.38 obs, +0.10 strat), and is competitive on efficiency. The v3 prompt tuning paid off.

**Strategy points remain a content coverage problem, not a dedup problem.** All three stores show similar strategy metrics (~59% redundancy, ~1.9 unique lessons). This confirms the phase 1 finding — the store lacks entries for common situations.

**The original report's core insight still holds: fix the root cause, not the symptom.** But the *degree* of dedup matters. v0's aggressive merging was itself a new problem — the v3 prompts' anti-over-merge calibration threads the needle between removing true duplicates and preserving useful diversity.

## Artifacts

| File | Description |
|---|---|
| [data/01_v4_vs_v4deduped_baseline.md](data/01_v4_vs_v4deduped_baseline.md) | Phase 1: v4 vs v4_deduped retrieval eval (n=5), raw per-case judge dump |
| [data/02_v4deduped_with_filtering.md](data/02_v4deduped_with_filtering.md) | Phase 1: v4_deduped with filtering pipeline (n=5), raw per-case judge dump |

## Code References

- `Agents/memory_batch_deduplication.py` — batch dedup pipeline, cluster size cap, two-pass support
- `memory_stores/v4_deduped/` — v0-prompt deduped store (320 items)
- `memory_stores/v4_deduped_v2/` — v3-prompt deduped store (432 items)
- `eval_configs/store_dedup/store_dedup_comparison.json` — phase 1 eval config (n=5)
- `eval_configs/store_dedup/dedup_v2_comparison.json` — phase 2 eval config (n=39)
- `eval_results/retrieval_eval_20260526_174803.jsonl` — phase 2 raw results

---

## Current live state (2026-06-25)

The verdict here — **conservative store dedup helps retrieval; aggressive over-merging hurts** — held
and shaped what shipped: batch dedup defaults to the conservative `bounded` clustering mode and is now
gate-partitioned (see [../report.md](../report.md)). Two caveats for a reader arriving from the v6
code:

1. **Path moved.** The pipeline cited above as the monolithic `Agents/memory_batch_deduplication.py`
   is now the package `Agents/memory/batch_deduplication/`.
2. **Numbers are v4-store-era.** These n=5 / n=39 results justify the *direction* (clean
   conservatively, don't over-merge), not absolute scores on today's v6 store — and the n=5 phase is
   superseded by n=39 regardless. The consolidated current-vs-documented gaps live in
   [../report.md](../report.md) § *Current-vs-documented gaps*.
