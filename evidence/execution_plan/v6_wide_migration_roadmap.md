# v6-wide migration roadmap — which consumers need the new dimensional framework (2026-06-16)

The v6 dimensional framework (schema-derived per-cell dims via `cell_prompt.dimension_menu`, replacing
the fixed v5 prose `SITUATION_STANDARDS`) cascades through the memory pipeline. This records WHO needs it,
how much, and the sequencing — so `SITUATION_STANDARDS` isn't naively find-replaced (each consumer
migrates on its own terms).

## The cascade

| Consumer | Needs v6 dims? | What migration means | Status |
|---|---|---|---|
| **Extraction** (`V6_CELL_EXTRACTION_PROMPT`) | — | already on the menu + `compose_cell_guidance` | ✅ done |
| **Situation summary** (live query) | — | already v6; query composes from `compose_cell_guidance` | ✅ done (+ cleanup 2026-06-16) |
| **Dedup + batch dedup** (`dedup_agent`, `cluster_agent`) | **yes** | rewrite merged situations from the STRUCTURED v6 fields (gate-then-embed), not the prose blob + `SITUATION_STANDARDS` | **already scoped** = `evidence/dedup/dedup_clustering_and_sp_extraction_plan.md` |
| **Eval judges / labelers** (retrieval relevance, extraction quality, dedup, context) | **yes** | score v6 content against the v6 quality bar, not the v5 rubric — else judging v6 dims by v5 standards | pending (separate eval pass) |
| **Day summary** (`summary_agent`) | loosely | a different artifact (accusations / claims / dynamics), not a cell observation — can stay on a general standard | low priority / optional |

## Why it's phased, not a monolith

- **`SITUATION_STANDARDS` is not globally swappable.** ~12 consumers, each needing a *different* migration
  (dedup → structured fields; judges → v6 rubric; day-summary → maybe unchanged). It's a find-and-rethink.
- **The store rebuild is the sync point.** The shared dimension content (menu / driver / quality) +
  extraction + dedup all converge when the v6 store is rebuilt. So the big coordinated step is:
  finalize shared dimension prompts **and** dedup-tuning together → ONE store rebuild → then migrate the
  judges to score it. Eval-judge migration can lag (it only gates *trusting* eval numbers, not the runtime).
- The single composer (`compose_cell_guidance`) makes the runtime alignment structural: the query and
  extraction sides can't silently drift, because they assemble from one function.

## Sequence

1. Extraction ✅ → 2. Situation-summary cleanup ✅ (this step) →
3. **[dedup-tuning + final shared dimension content + store rebuild]** as ONE coordinated package
   (store-gated; prompt-freeze applies to the shared content) →
4. Eval-judge / labeler migration to the v6 quality bar →
5. Day summary (optional, light touch).

Not started below step 3. Steps 3+ are explicitly out of scope until the rebuild package is greenlit.
