# Agents/memory — the episodic memory subsystem

What agents **write** after each game and **read** during each turn. This README is the navigation
map; each subpackage's `__init__.py` documents its internals, and the measurement record lives in
`evidence/` (dedup, extraction, retrieval, memory_system).

## Write path (post-game, off the critical path of play)

Runs once per finished game, from `post_game_analysis` (`Agents/nodes/orchestrator.py`):

```
game transcript
  → extraction/            per-(role×phase)-cell LLM fan-out → observations
                           (entry: extract_postgame_per_cell)
  → deduplication/         ONLINE dedup of each new entry vs the store: KEEP/DISCARD only,
                           writing the survivors into the live store (store.py singleton)
  → persistence/           dump the live store to the versioned JSON files on disk
  → batch_deduplication/   OFFLINE whole-store cluster sweep (can MERGE/rewrite), config-gated
```

Strategy points are **not** minted per game (v7 design): they are synthesized cross-game from
observation clusters during loop consolidation — that policy currently lives in
`evaluation/src/loop/consolidate.py` (planned to graduate here at loop go-live) with the offline
primitive in `strategy_synthesis.py`.

## Read path (every agent turn)

Orchestrated by `retrieval/pipeline.py` (`enrich_payload_with_memory`, called from
`Agents/turn/pipeline.py`):

```
plan_gating.py       whether/what to retrieve this turn (builds the frozen RetrievalPlan)
  → situation_agent.py   the query: structured situation summary of the current game state
  → accessors.py         embedding search over role-keyed namespaces
  → filters.py           dedup-gate (observations) + MMR diversity (strategy points)
  → rerank_agent.py      LLM re-scoring of observations and/or strategy points, each independently gated
  → dimension_gating.py  per-item soft reweight by situation dimensions (default OFF)
  → cap                  per-situation item cap → into the agent prompt
```

## The three dedup homes (the axis that matters)

| Home | When | Scope | Can merge? |
|---|---|---|---|
| `dedup_gate.py` | both paths | deterministic partition (role/phase + gate key) shared by online and batch | — |
| `deduplication/` | online, per game | each NEW entry vs its bucket | no — KEEP/DISCARD only |
| `batch_deduplication/` | offline, on demand | whole store, in clusters | yes — MERGE/rewrite |

## Loose top-level files

- `store.py` — the shared in-memory vector store + embeddings singletons (instantiated at import)
- `vectors.py` — shared low-level vector primitives (embedding I/O + cosine similarity)
- `validators.py` — write-time coercions applied at store-write
- `dedup_gate.py` — shared deterministic partition (see table)
- `strategy_synthesis.py` — offline cross-game SP synthesis primitive
