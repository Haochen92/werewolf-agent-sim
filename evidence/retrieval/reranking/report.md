> **Write-up: no detailed read needed.** Its blocks (41–42) are already filed in the
> [map](../../../writeup/map.md); read the [retrieval report](../report.md) instead.

> **Superseded record (May 2026).** Written 2026-05-23 and kept as it was, with its 2026-10-14 addendum
> at the end. The read path today, and this study beside the filter and capacity studies, are in the
> [retrieval report](../report.md), "The model reranker". Code paths below are May's; current ones are
> in the addendum.
>
> - **Question.** Does a model call that re-scores the retrieved candidates against the situation give a
>   seat better-fitting, less repetitive lessons?
> - **Test.** The same 5 frozen cases on the nine-seat v4 store, cleaned (v4_deduped) and not, in four
>   configurations; one judge (Gemini 2.5 Flash).
> - **Answer.** For strategy points, reranking alone raised efficiency from 1.80 to 3.60 and relevance
>   from 3.20 to 3.80 on the cleaned store, with smaller sets (2.8 items against 3.8); filtering first
>   scored lower (efficiency 2.20). Observations gained nothing. A direction on 5 cases, not a size.
> - **What followed.** Both rerank switches are off by default; served games do not rerank, so the
>   "Final Pipeline Configuration" below never ran there. A trained cross-encoder built to replace the
>   call is not wired in ([fine-tuning report](../../fine_tuning/report.md)).

---

# Reranking: LLM Re-scoring for Strategy Point Relevance

## The Problem

After store deduplication solved the redundancy problem for observations, strategy points remained the weak spot. On the clean v4_deduped store, strategy point retrieval still showed 72% redundancy ratio, efficiency of 1.80, and unique lessons of 1.20 across 5 evaluation scenarios. The store had relevant strategy points — the bi-encoder just wasn't surfacing the right ones.

The failure mode was situation mismatch: embedding similarity captures topical overlap ("healer," "voting," "consensus") but not game-phase specificity. The retrieval returned mid-game advice for early-game situations, or endgame strategy when the agent faced a Day 1 information void. These items were *about the right topic* but *for the wrong moment*.

## The Solution

The reranker is an LLM re-scorer that takes the top candidates from embedding retrieval and re-orders them by relevance to the actual situation. It uses gemini-3.1-flash-lite — the same model the agents use during games — with a small context window containing only the situation summaries and candidate texts. No full game context is passed.

The pipeline becomes:

```
Retrieve (top_k per situation) → Rerank (LLM re-score) → Cap (3 per situation) → Prompt
```

The reranker makes one LLM call per item type (observations, strategy points) and automatically skips when ≤3 items are retrieved — there's nothing to reorder.

## Evaluation

We tested four configurations on the clean v4_deduped store, plus rerank-only on the original dirty v4 store. Same 5 frozen eval cases, gemini-2.5-flash judge.

### Strategy Points — where reranking matters (n=5 scenarios)

| Config | Store | Retrieved | Relevance | Efficiency | Unique Lessons | Redundancy |
|---|---|---|---|---|---|---|
| Baseline | v4_deduped | 3.80 | 3.20 | 1.80 | 1.20 | 72.3% |
| Filtering only | v4_deduped | 4.00 | 2.80 | 2.00 | 1.00 | 77.3% |
| **Rerank only** | **v4_deduped** | **2.80** | **3.80** | **3.60** | **1.80** | **40.0%** |
| Filter + rerank | v4_deduped | 2.80 | 3.00 | 2.20 | 1.00 | 66.7% |
| **Rerank only** | **v4 (dirty)** | **2.80** | **4.00** | **3.40** | **1.80** | **40.0%** |

Rerank-only doubled efficiency (1.80 → 3.60) and halved redundancy (72% → 40%) on the clean store. On the dirty store, it performed comparably — relevance actually hit 4.00, better than any other configuration on any store.

Case-level highlights:
- Healer/day_discussion: strategy points went from rel=3/eff=2 (baseline) to rel=5/eff=5 (rerank)
- Villager/day_discussion: rel=5/eff=1 (baseline) to rel=5/eff=5 (rerank)
- Healer/day_vote: stayed at rel=1/eff=1 — content gap, no strategy points exist for this situation

### Observations — reranking is unnecessary (n=5 scenarios)

| Config | Store | Retrieved | Relevance | Efficiency | Unique Lessons | Redundancy |
|---|---|---|---|---|---|---|
| Baseline | v4_deduped | 4.00 | 4.60 | 4.00 | 3.00 | 25.0% |
| Rerank only | v4_deduped | 3.00 | 4.40 | 3.80 | 2.00 | 33.3% |
| Rerank only | v4 (dirty) | 3.00 | 4.60 | 3.60 | 2.00 | 33.3% |

Observations were already well-served by bi-encoder ranking. Reranking maintained quality but reduced unique lessons from 3.00 to 2.00 by being more selective (3 items vs 4). The bi-encoder ordering was sufficient for observations because their redundancy was narrative-level (same lesson, different game), which store dedup already handled.

### Why filter + rerank over-corrects

Adding filtering before reranking consistently hurt. The pattern was the same as filtering on a clean store: wider retrieval (top_k=10) pulled in less relevant items, and dedup/MMR removed items the reranker would have kept. The reranker already handles both relevance and implicit diversity — layering filtering on top just removes options.

## Final Pipeline Configuration

Based on these results, the recommended configuration is:

- **Observations**: baseline retrieval + per-situation cap (3). No reranking, no filtering.
- **Strategy points**: baseline retrieval + LLM rerank + per-situation cap (3). Rerank uses flash-lite with minimal context.
- **Filtering**: available as a toggle, default off. Safety net for periods between batch dedup runs.
- **Store dedup**: run periodically when new game data accumulates.

Cost profile:
- Baseline + cap: zero additional cost (embedding search only)
- Reranking: one flash-lite call per turn, only when >3 strategy points retrieved. Small context (situations + candidate texts). Essentially free.
- Store dedup: periodic batch cost (gemini-2.5-pro), amortised across many game runs.

## What I Learned

**Different content types need different retrieval strategies.** Observations and strategy points look similar but have different failure modes. Observations fail on narrative duplication (solved by store dedup). Strategy points fail on situation mismatch (solved by LLM re-scoring). Using the same pipeline for both left one problem solved and the other untouched.

**The reranker works because it reads situations, not just topics.** Embedding similarity captures "this is about a healer voting." The reranker captures "this is about a healer voting *in an early-game, information-starved scenario where they're under direct scrutiny*." That specificity is exactly what strategy points need — the advice for a mid-game healer with voting records is different from advice for a Day 1 healer with no data.

**Simpler pipelines compose better.** The filtering pipeline had three stages (dedup gate, MMR, cap) each solving a piece of the redundancy problem. But they interacted poorly — wider retrieval for dedup pulled in bad items, MMR reordered in ways that conflicted with the downstream cap. Reranking is a single stage that handles both relevance and implicit diversity, with fewer failure modes.

**Don't stack solutions for the same problem.** Store dedup + filtering + reranking all partially address redundancy. Each individually helps; combining them over-corrects. The best results came from matching one solution to one problem: store dedup for content duplication, reranking for relevance ranking, cap for volume control.

## Artifacts

| File | Description |
|---|---|
| [01_rerank_on_clean_store.md](01_rerank_on_clean_store.md) | Rerank + filter+rerank on v4_deduped |
| [02_rerank_on_dirty_store.md](02_rerank_on_dirty_store.md) | Rerank-only on original v4 store |

## Code References

- `Agents/reranker.py` — rerank pipeline, RERANK_TOP_K, RERANK_KEEP
- `Agents/agents.py:_reranking_enabled_for_role` — per-role reranking toggle
- `eval_configs/reranking_experiment.json` — clean store reranking eval config
- `eval_configs/rerank_dirty_store.json` — dirty store reranking eval config

*Addendum 2026-10-14.* Where this stands in today's code. The reranker is in
`Agents/memory/retrieval/rerank_agent.py`, with observations and strategy points switched separately
per role by `reranking_config` on `RunConfig` (`Agents/config/run.py`). Both are off by default.
The served game retrieves strategy points only and does not rerank them, so the recommended
configuration above does not run in the deployed demo. The paired memory A/B
(`../../memory_system/effectiveness/`) ran a reranked arm, and its result is reported there. A
cross-encoder was later trained as a cheaper replacement for this LLM call
(`../../fine_tuning/cross_encoder/`). It was not wired into the read path. The eval configs are
now in `evaluation/config/reranking/`. Every number above comes from 5 scenarios on the nine-seat
v4 store, so it gives a direction and is not a score.
