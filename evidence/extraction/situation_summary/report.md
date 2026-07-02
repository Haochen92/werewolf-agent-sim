# Situation Summary — how it works today

**Orientation.** On every agent turn, before the agent decides, the situation-summary call turns the current
game state into **1-2 structured search queries** that retrieve the episodic memories the agent will reason
with. It is the front door of the memory *read* path: query quality bounds retrieval quality regardless of how
good the store is.

```
game state ─▶ situation-summary (1-2 structured queries) ─▶ semantic search ─▶ [rerank/filter: off in v6] ─▶ retrieved memories ─▶ agent decision
```

The pass runs many times per game (once per agent per decision), so it must be cheap and fast. This doc is the
current shipped state; the path that got here is [experiment_log.md](experiment_log.md), and how the output is
*measured* — the summary judges and the retrieval golden — lives in the funnel apparatus report
[../../evaluation/llm_judge/agent_decision.md](../../evaluation/llm_judge/agent_decision.md) (Stage 1), because
the diagnostic value is *which* funnel stage fails, so situation-summary is written up beside retrieval and
application rather than alone.

## What it produces (current schema)

**1-2 situation queries**, each a structured **v6 cell-situation** object carrying the dimensional fields
(information landscape, consensus texture, agent exposure, game phase); the `composed_situation` property
concatenates them into the string that retrieval embeds. The central v6 fact:

- **The query uses the same per-cell dimension schema as post-game extraction.** A live query is composed by
  `cell_situation_schema_for(role, phase)` → `compose_situation_embed`, the *same* construction that writes the
  stored v6 observations. So a query and the observations it should match share vocabulary and structure in
  embedding space **by construction** — not merely by convention. This is the structural successor to the
  earlier alignment-by-shared-prose (the `SITUATION_STANDARDS` text composed into both prompts).
- **A legacy v5 fallback** covers any (role, phase) without a v6 cell: the per-role `SituationSummary` prompt,
  emitting free-composed situation strings with no structured dims.

## Guarantee / contract (present-tense)

- **Query↔store embedding alignment by construction.** Because the live query and the stored observation are
  composed by the same v6 cell schema
  ([situation_agent.py:85-94](../../../Agents/memory/enrichment/situation_agent.py#L85-L94)), they land in the
  same region of embedding space. Alignment is a property of the shared schema, not of the model remembering to
  match a house style.
- **At most two queries, each a distinct decision.** The structured container caps output at 1-2
  (`min_length=1, max_length=2`,
  [situation_agent.py:62](../../../Agents/memory/enrichment/situation_agent.py#L62)), and the prompt requires a
  second only if it captures a genuinely independent decision. The pipeline never reliably produced three
  useful queries and filled the extra slots with rephrasings of the first (experiment_log §3).
- **A summary failure never blocks a turn.** One retry, then a trivial fallback string
  (`"Day {d} as {role}, round {r}"`,
  [situation_agent.py:113-114](../../../Agents/memory/enrichment/situation_agent.py#L113-L114)). A failure
  degrades that turn's retrieval; it does not stall the decision.
- **Role perspective is locked.** Per-role prompts frame the query from the agent's own vantage and private
  knowledge (with an investigator lens fix that front-loads private findings), so retrieval returns
  role-relevant memories. Role perspective was a hidden failure mode — a model can be factually faithful yet
  write an omniscient query that retrieves the wrong strategies (experiment_log §1).
- **What is NOT guaranteed.** The two live summary-*content* judges (pairwise + single-rubric) are
  **uncalibrated** (no ground truth); the human-anchored **NDCG golden** that grades the *retrieval* is stale
  (v4 store, 2026-05 prompts) and **not wired into the live retrieval judge**; and the shipped prompt lineage
  (v4b) and its NDCG numbers predate the v6 cell schema. See the gaps table.

## The mechanism / model

- **Live entry point.** `_generate_situations_for_agent`
  ([situation_agent.py:71](../../../Agents/memory/enrichment/situation_agent.py#L71)), called once per agent
  turn from the enrichment pipeline
  ([enrichment/pipeline.py:63](../../../Agents/memory/enrichment/pipeline.py#L63)).
- **Model.** The default agent model `get_llm()` = **gemini-3.1-flash-lite**, no thinking
  ([accessors.py:17](../../../Agents/llm_factory/accessors.py#L17)). The model comparison profiled 3.5-flash
  and 2.5-flash as upgrades and kept flash-lite: the gain was modest on rubric scores, the cost 6× and latency
  ~3×, and this runs on every turn (experiment_log §1). Notably, *medium thinking made flash-lite worse*, not
  better.
- **v6 path vs v5 fallback.** `cell_situation_schema_for(role, phase)` returns the v6 cell schema when one
  exists (the concurrent structured path); otherwise the call drops to the legacy per-role prompt with the flat
  `SituationSummary` schema.
- **Prompt.** `V6_SITUATION_SUMMARY` plus the per-role situation-summary prompts and `compose_cell_guidance`.
  The design carries the prompt-iteration study's endpoints: **structured dimensional fields** (to match the
  indexed store's format), **no "core dilemma"** dimension (added in v2, found net-negative on clean cases and
  removed in v4), and the **investigator lens fix** (experiment_log §3).

## Config / defaults

| Setting | Value | Where |
|---|---|---|
| queries per turn | 1-2 structured situations | `_summary_container` (situation_agent.py:62) |
| model | flash-lite, no thinking (`get_llm`) | accessors.py:17 |
| situation schema | v6 per-cell (embed-aligned with extraction); v5 fallback | `cell_situation_schema_for` (schemas/memory.py:635) |
| retries | 1, then trivial fallback string | situation_agent.py:101-114 |
| prompt design | structured dims · no core dilemma · investigator-lens-first (v4b lineage, now on the v6 cell schema) | prompts/memory, per-role prompts |

## Verification

**Verdict.** Situation-summary is measured two ways, with different strengths, and both are written up in
[../../evaluation/llm_judge/agent_decision.md](../../evaluation/llm_judge/agent_decision.md) (Stage 1):

- **Query content — two uncalibrated LLM judges.** A pairwise-preference judge and a single-rubric judge score
  the query on faithfulness, specificity, retrieval usefulness, non-redundancy, and role perspective. Neither
  has ground truth. They told us flash-lite is adequate and caught the role-perspective failure mode, and the
  pairwise judge proved *more sensitive* than the independent rubric (it preferred 3.5-flash 14/15 while the
  rubric averages tied) — but with no anchor they cannot certify a query as good.
- **Retrieval ranking — a real human-anchored golden.** A graded-relevance (0/1/2) NDCG golden over ~20
  human-labelled cases is the strongest anchor design in the repo: proper offline NDCG, zero API. It set the
  baseline at **NDCG@10 ≈ 0.83** and drove the prompt from v1 to v4b (**+0.061** on expanded labels).

**What it can't do.** The golden is stale (v4 store, 2026-05 prompts), has grown partly machine-augmented (108
cases with auto-labels, never human-re-validated), and is not wired into the live retrieval judge. It also
cannot separate a bad *query* from a bad *store entry* — the largest per-role "win" (villager +0.196) was an
upstream store-coverage gap surfacing through stage 1, not a summary-quality improvement.

## Current-vs-documented gaps (freshness: 2026-07-02)

Ordered by how misleading each is to a reader. Severity weighs likelihood, impact, and detectability together,
not impact alone.

| # | Gap | State | Severity |
|---|---|---|---|
| 1 | **Shipped prompt + golden are v5-era** | The v4b prompt and every NDCG number were tuned on the `v4_deduped_v2` store and 2026-05 prompts; the live path is the v6 cell schema. The cheapest refresh is to re-run NDCG golden-mode against the v6_1 store — offline and free, just repoint the hard-coded store/dataset constants in `situation_retrieval_ndcg.py`. | Med |
| 2 | **Summary-content judges uncalibrated** | The pairwise and single-rubric judges grade query content with no ground truth — the same no-anchor gap as day-summary. Situation-summary is fundamentally an extraction task (extract what is critical about the situation), so the fix is a reference-point golden: critical situation elements → coverage/recall, game-state faithfulness → precision. Method: [../../evaluation/llm_judge/golden_set_method.md](../../evaluation/llm_judge/golden_set_method.md). Distinct from the NDCG golden, which anchors retrieval *ranking*, not query *content*. | Med |
| 3 | **NDCG golden is partly machine-augmented** | It grew from ~20 human cases to 108 via 4-model-consensus auto-labels, never human-re-validated. The headline 0.83 is the linear-gain N=20-human baseline; the exponential re-score is 0.732@10. Treat the augmented numbers as directional. | Low-Med |
| 4 | **Query quality and store coverage are entangled** | NDCG measured through stage 1 cannot attribute a miss to a bad query vs a thin store namespace. Known and documented (the villager gains were store-coverage), but it caps how much a summary-prompt change can be credited on NDCG alone. | Low |

**Open work.** The situation-summary prompt is a viable retrieval lever (v4b showed +0.061), but the honest
next step is a **free v6_1 re-baseline of the NDCG golden** (gap 1) before further prompt tuning is worth
crediting, and — if query-*content* certification is ever needed — the reference-point golden (gap 2). Both
stay deferred while the binding memory constraint is store content and the investigator-transmission cap, not
query phrasing.
