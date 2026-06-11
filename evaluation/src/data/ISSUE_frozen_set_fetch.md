# ISSUE: Frozen-set builders 422 on heavy traces (Langfuse fetch) — open, 2026-06-11

## Summary
Building a frozen eval set from Langfuse (`extraction_builder.py` and the dedup / day-summary /
retrieval builders) fails with a Langfuse **422** on *heavy* games (long sequential matches). The
shared fetch helper over-fetches every span of a trace via paginated `observations.get_many`, which
is an expensive table-query that Langfuse rejects once a trace has enough spans. It is **systemic**
(all builders share the helper) and **worsens over time** (more/longer games → 422 spreads from long
games to all games). It is a *latent* inefficiency exposed by v5's span volume — it was tolerable on
the smaller v4 games the builder was written for.

## Symptom
```
langfuse.api.core.api_error.ApiError: status_code: 422,
body: {'message': 'Your query could not be completed. Please narrow your request by adding more
specific filters (e.g., a shorter date range).', 'error': 'Unprocessable Content'}
```
Occurs inside the per-trace observation fetch. In one session (`v5_seed_b1_all_disabled`, 5 traces):
**3 ok / 2 errored** — short games succeed, long games 422. `session_id` vs `session_prefix` makes
no difference (the failure is per-trace, in the inner fetch).

## Root cause (verified)
1. **`_fetch_all_observations(trace_id)`** (`evaluation/src/data/langfuse.py:251`) pages
   `observations.get_many(trace_id, page, limit=100)` to pull **every** span of a game (a 9-player
   sequential game logs hundreds–thousands of spans), then filters client-side. `get_many` is a
   **paginated table-QUERY** whose cost scales with offset + total observations table → Langfuse's
   cost guard fires on heavy traces. (NOT a whole-table scan — short traces work, so it's per-trace
   result size + table growth.)
2. **`date-bounding does NOT help`** — the games are same-date, and the cost is the heavy trace's own
   span count, which a window inside that trace's ~15-min lifetime doesn't shrink. (Langfuse's "add a
   date range" message is generic advice that misfits this already-`trace_id`-filtered query.)
3. **`trace.get(trace_id)` does NOT fix it** — it returns all span names/ids in one call (good for
   *enumeration*, no 422: 1333 obs / 235 span-types on a trace that 422'd) BUT **truncates large
   `output`**: the extraction span's `output` came back 8341 chars with **no `extraction_case` key**,
   vs `get_many`'s full 38262-char `formatted_discussions`. So `trace.get` cannot supply the case
   content.
4. **Only `get_many` returns full `output`** — and the case lives there:
   `extraction_case_from_span` (`evaluation/src/data/extraction_cases.py:14`) reads
   `span["output"]["extraction_case"]`.
5. **Span-name prefix collision** — `postgame_extraction_` matches BOTH the parent case-span
   `postgame_extraction_<game_id>` (holds `output.extraction_case`) AND per-role child generation
   spans `postgame_extraction_<role>_..._cached` (no case). The builder works today only because
   fetch-all returns everything and `extraction_case_from_span` returns `None` for the children,
   leaving the parent. A naive name-scoped fetch can grab a child and get nothing.

## Affected code
- `evaluation/src/data/langfuse.py`: `_fetch_all_observations` (251), `_filter_spans_by_prefix`
  (331), `fetch_extraction_cases` (357), `fetch_dedup_cases`, `fetch_day_summary_cases`, and the
  action-eval/retrieval fetch (`_filter_eval_spans`). All route through `_fetch_all_observations`.
- `evaluation/src/data/extraction_cases.py`: `extraction_case_from_span` (reads `output.extraction_case`).
- `evaluation/src/experiments/extraction_builder.py`: the CLI that drives the build.

## Repro
```python
from evaluation.src.data.langfuse import fetch_trace_ids_for_session_id, fetch_extraction_cases
tids = fetch_trace_ids_for_session_id('v5_seed_b1_all_disabled')
fetch_extraction_cases(tids[0])   # short game — OK, formatted_discussions = 38262
fetch_extraction_cases(tids[2])   # long game — 422
```
Build that 422s: `extraction_builder` config `{"session_prefix": "v5_seed_b", "max_games": 0,
"max_samples": 0, "eval_set_id": "extraction_v5_0", "output":
"evaluation/frozen_eval_sets/extraction/extraction_v5_0.jsonl"}` → "Found 20 traces" then 422.
(Local-hosted Langfuse — no rate limits; the 422 is a query-cost guard, not throttling.)

## Fix

### PRIMARY — local eval-case emission at game-time (the original design intent)
The in-run eval-case builder ALREADY exists: `Agents/nodes/orchestrator.py:433` builds the
`ExtractionCase` (1/game) and `model_dump`s it at :452; `Agents/turn/actions.py:172,329` build
per-decision `EvalCase`s. **But the sink is Langfuse-only** — the case is dumped into the trace span;
`run_batch` persists only `raw_metrics` (resolutions/dedup_stats, `scripts/run_batch.py:432-436`),
NOT the eval cases. Fix = route the already-built+dumped case into the game OUTPUT so `run_batch`
persists it locally (batch record, or a sidecar `eval_cases/*.jsonl`); the frozen-set builder then
becomes a local SELECTOR. **Benefits:** no Langfuse read path → no 422, no truncation, no prefix
collision, durable; also captures `wolf_channel` + strategy notes the batch JSONL currently drops.
Small change (the hard part — building the case — is done). NOTE: this fixes FUTURE games only; the
already-run v5_0 games emitted Langfuse-only, so building *their* frozen set needs the secondary fix.

### SECONDARY — Langfuse-read, for already-run games + retroactive mining of un-emitted spans
Keep Langfuse usable as the universal archive (you can mine ANY span into a new eval-case type
later, even spans never wrapped as an `EvalCase` — a real benefit of local-hosted Langfuse). Pattern:
1. `trace.get(trace_id)` → enumerate observations (names/ids), no 422.
2. Identify the PARENT case-span (e.g. `type == SPAN`, or name matches `postgame_extraction_<uuid>`
   not `_<role>_...`, or `output` contains `extraction_case`).
3. Name-scoped `get_many(trace_id, name=<exact parent name>)` → 1 row WITH full `output` → reconstruct
   via `extraction_case_from_span`. Cheap query → no 422; full content (unlike trace.get).
This changes `_fetch_all_observations`'s contract (it must know which span/prefix to target) →
per-builder call-site change. Fiddlier than the primary fix; secondary by design.

## Acceptance criteria
- Build `extraction_v5_0.jsonl` from all 20 `v5_seed_b*` games with **zero 422**, and every record's
  `formatted_discussions` is full-length (~tens of KB), not truncated/empty.
- All four builders (extraction / dedup / day_summary / retrieval) still work.
- Retroactive "fetch any span" capability preserved (don't hard-restrict the reader to one span type).

## Related / do alongside
- **DRY the span names (producer⟺consumer drift):** span names are hardcoded independently on both
  sides — producers (`orchestrator.py:409` `postgame_extraction_{game_id}`; `day/flow.py:226`
  `day_summary_eval_{game_id}_day_{day}`; `deduplication/pipeline.py:318` `dedup_{...}`;
  `turn/actions.py` `agent_action_eval_*`) vs consumer constants (`langfuse.py:52-55` `*_SPAN_PREFIX`).
  Rename on the producer side → builder silently matches nothing. Fix = a single source of truth, e.g.
  `Agents/observability/span_names.py` exporting prefix constants + name-builder fns; both sides
  import it. Prompt-freeze-NEUTRAL.
- Constraints: all of the above is **data/plumbing only — prompt-freeze-neutral** (no model-visible
  prompt changes).
```
