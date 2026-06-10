# Incremental batch dedup: non-convergence (old entries are not frozen)

Diagnosed 2026-06-09. The post-game **incremental** batch dedup
(`run_batch_memory_dedup(incremental=True)`, driven by the `IncrementalDedupConfig` gate) is
**idempotent in the narrow sense** but **does not converge**. The gate is currently dormant
(`enabled=False`), so this is latent — but it must be fixed before incremental dedup is turned on
as a routine post-game pass.

## TL;DR

- Narrow idempotency *holds*: re-running incremental with **no new entries** is a no-op.
- The real defect is **non-convergence**: as entries stream in game-by-game, old (already-deduped)
  entries get repeatedly re-litigated by the LLM whenever a new neighbour lands in their cluster, so
  the store erodes **non-deterministically** with no stable fixed point — drifting past the optimal
  dedup point (README: ~17% reduction is the sweet spot; ~39% crosses into information loss).
- So describe it as **non-convergence / "old data is not frozen"**, *not* "not idempotent".

## How incremental mode actually works (mechanism)

1. `.last_dedup_at` — a file named by `DEDUP_TIMESTAMP_FILE` in the **store dir** (co-located with
   `observations.json`/`strategy_points.json`, travels with the store), holding an ISO-8601 UTC
   timestamp written at the **end of every applied run** ([orchestration.py:190](../../Agents/memory/batch_deduplication/orchestration.py#L190)).
2. `_collect_new_keys(store_dir, since)` returns keys whose envelope `created_at > since` — **missing
   `created_at` ⇒ treated as new** ([incremental.py:31-49](../../Agents/memory/batch_deduplication/incremental.py#L31-L49)).
3. A cluster is processed **iff it contains ≥1 new key**:
   `clusters = [c for c in clusters if any(k in new_keys for k in c)]`
   ([orchestration.py:236](../../Agents/memory/batch_deduplication/orchestration.py#L236)). All-old
   clusters are skipped — that is the only cost win incremental buys.
4. A processed cluster is judged as a **whole** by **one** LLM call over all its live keys
   (`_format_cluster_entries` → `_call_cluster_llm`); the model returns a list of operations.
5. **Batch operation vocabulary** ([schemas.py:22-71](../../Agents/memory/batch_deduplication/schemas.py#L22-L71)):
   Observations `{KEEP, MERGE, DISCARD}`; Strategy points `{KEEP, DISCARD}` (DISCARD may carry merged
   text = de-facto merge). `KEEP` = no-op; `MERGE`/`DISCARD` keep a `survivor_key` and delete the
   other `source_keys` (MERGE also rewrites the survivor). **Rewriting is pro-model / batch-only
   (`MERGE`).** The online per-extraction pipeline (weak models) does **`KEEP`/`DISCARD` only** — its
   model-visible decision schemas offer only those two
   ([deduplication/schemas.py:24-65](../../Agents/memory/deduplication/schemas.py#L24-L65)), and its
   `DedupAction` enum's `REPLACE`/`DIFFERENTIATE` members are **dead** (never offered to the model,
   never branched on; `DedupStats.replaced/differentiated` and `NamespaceStats.replaced/differentiated`
   are likewise vestigial). So **REPLACE and DIFFERENTIATE exist nowhere in use** — weak models can't
   rewrite reliably, so rewrites were confined to the pro batch pass and the rest dropped. "New
   replaces old" is not a verb anywhere; in batch it's a MERGE/DISCARD whose `survivor_key` is new.

## The two bugs

### A. Old entries are not frozen (the non-convergence)

A cluster is pulled in by a *new* neighbour, but the LLM is shown the **whole** cluster and may emit
operations that delete/rewrite **old** members (old-into-old, or an old survivor discarding another
old). Because LLM dedup is non-deterministic and the criteria are fuzzy, every re-exposure is a fresh
chance to erode already-settled old data. There is no stable fixed point under the streaming
workload.

### B. `created_at` is destroyed on merge

The merged survivor `value` is rebuilt **without** `created_at`
([operations.py:100-105](../../Agents/memory/batch_deduplication/operations.py#L100-L105)), and
`InMemoryStore._apply_put_ops` unconditionally sets envelope `created_at = now` on **every** put
(verified in the installed langgraph source). So a survivor's birth date is lost / marches forward on
each touch. Narrow idempotency survives only because the reset time is always earlier than the run's
end timestamp; **provenance/age does not** survive, and `created_at` cannot be trusted as a true
birth date after any merge (`updated_at` already exists for "last touched").

## Why "non-convergence", not "non-idempotent"

Strict idempotency `f(f(x)) = f(x)` holds for the no-new-data case: survivors end up with
`created_at ≤ .last_dedup_at` (written last), so a rerun finds no new keys and does nothing. The
defect is the absence of a stable fixed point under the *streaming* workload — old data keeps moving.

## Fix plan (both prompt-neutral; not yet built)

### Fix 1 — keep the old `created_at`

Carry the original `created_at` through a merge (store it in `value` so it survives the put + JSON
roundtrip, and read it in `_collect_new_keys`); `updated_at` already carries "last touched". Restores
provenance and keeps old/new classification honest across runs.

### Fix 2 — freeze old entries: forbid **old-vs-old** operations

**Invariant: old keys may not have dedup operations against one another.** For each operation, let
deleted = `source_keys − {survivor_key}`:

| survivor | deleted contains… | verdict |
|---|---|---|
| OLD | an OLD key | **strip** those old keys from the deleted set (protect); if nothing left to delete ⇒ **downgrade to KEEP** |
| OLD | only NEW keys | allowed (new absorbed into old — the canonical case) |
| NEW | anything | allowed (new may replace/absorb old) |

Allowed in a touched mixed cluster: new→old absorb, **new replaces old** (survivor = new), new kept
distinct, new-vs-new. **Forbidden: old ↔ old.**

**Enforce post-hoc in the apply layer** (`operations._apply_*` / a guard before apply), reusing the
`new_keys` set already in scope — **not** by changing the dedup prompt (Phase-B gold labels are
conditioned on it → prompt freeze). The LLM still *judges* old entries (they must stay in the prompt
as merge candidates for new entries — you cannot drop them to save tokens without a prompt change),
but old-vs-old verdicts are simply discarded. A prompt-side optimisation (mark old entries as
immutable reference-only candidates, so the model doesn't waste reasoning on them) is possible later
but is a prompt change → deferred.

**Note:** Fix 1 underpins Fix 2 — the old/new partition is only trustworthy if `created_at` is
preserved.

### Open sub-decision

Whether to also forbid **new-replaces-old** (survivor = new, deletes old). Stricter = pure
append / absorb-into-old only → maximal convergence, but loses the ability to freshen a superseded
old entry. Current intent: **allow** new→old replacement (consistent with the online pipeline's
REPLACE).

## Pointers

- [incremental.py](../../Agents/memory/batch_deduplication/incremental.py) — timestamp + new-key collection
- [orchestration.py:236](../../Agents/memory/batch_deduplication/orchestration.py#L236) — cluster-level new-key filter
- [operations.py:100-105](../../Agents/memory/batch_deduplication/operations.py#L100-L105) — survivor value rebuild (drops `created_at`)
- [schemas.py:22-71](../../Agents/memory/batch_deduplication/schemas.py#L22-L71) — batch operation vocabulary
- [deduplication/schemas.py:24-65](../../Agents/memory/deduplication/schemas.py#L24-L65) — online decision schemas: model offered KEEP/DISCARD only (REPLACE/DIFFERENTIATE enum members are dead)
