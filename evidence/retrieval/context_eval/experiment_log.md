# Context-Based Retrieval Evaluation

## Motivation

The current retrieval eval labels memory relevance against the **situation summary query** — "is this memory relevant to the situation description?" This makes the ground truth query-dependent: if the situation summary misses a key tension, a memory that addresses that tension scores 0 even though it's exactly what the agent needs.

This creates a blind spot: we can measure reranker quality and retrieval NDCG, but we cannot evaluate the situation summary itself or whether the agent uses retrieved memories effectively. The only end-to-end signal is LLM-as-judge, which misses information gain (see `feedback-llm-judge-limitations.md`).

## Proposed approach

Label memory relevance against the **game context** instead of the situation summary. The situation summary is used only to fetch a candidate pool — the ground truth is "would this memory help the player in this game state?"

### Labeling process

1. For each eval case, use a good situation summary to retrieve top-N candidate memories (observations + strategy points)
2. Show the labeler the full game context (same as `format_game_state` renders) plus each candidate memory
3. Label: "Is this memory useful for a player in this game situation?" (0/1/2 graded scale)
4. The situation summary is NOT shown to the labeler — relevance is judged against the raw game state

### What this enables

The same label set serves two modular evaluations:

**1. Situation summary recall**

For a given situation summary, retrieve memories and measure what fraction of context-labeled golden memories appear in the top-K. Different summaries can be compared on the same fixed ground truth:

- Summary A (2.5-pro, v4b prompt) retrieves 9/10 golden memories → recall 0.90
- Summary B (flash-lite, old prompt) retrieves 6/10 → recall 0.60
- Summary C (new prompt iteration) retrieves 10/10 → recall 1.00

This directly evaluates whether the situation summary captures the right dynamics without needing to judge the agent's action.

**2. Strategy adoption**

Given the golden relevant memories (the "right inputs"), does the agent actually use them? This isolates the downstream question: retrieval delivered good content — did the agent apply it?

- Measures the gap between "had the right memory" and "acted on it"
- Can evaluate different action prompts or models with retrieval held constant

### Key difference from current labels

| | Current (query-based) | Proposed (context-based) |
|---|---|---|
| Ground truth tied to | Situation summary | Game state |
| Can evaluate situation summary | No (circular) | Yes (recall metric) |
| Can evaluate strategy adoption | No | Yes (given golden memories) |
| Reusable across prompt iterations | No (new query = new labels) | Yes (game state is fixed) |
| Reranker training data | Yes | Also yes (query, memory, label triples still valid) |

### Relationship to current work

The reranker cross-encoder training (see `evidence/fine_tuning/cross_encoder/experiment_log.md`) trains on (query, memory, relevance) pairs. This is unaffected — the reranker scores relevance to a query regardless of how the query was generated. The two efforts are complementary:

- **Reranker CE**: improves scoring given a fixed query
- **Context-based eval**: evaluates whether the query itself is good

## Status

Idea stage. Not yet implemented. Current labeling sprint (109 cases for reranker CE) uses query-based labels. A future iteration could re-label a subset against game context to bootstrap this eval.
