# Deduplication — how it works today

**Orientation.** A memory entry (an observation or a strategy point) is deduplicated by up to three
layers, in this order: a **deterministic gate** narrows candidates to a homogeneous bucket → an
**embedding pre-filter** disposes of the obvious keep/discard cases with no LLM → an **LLM** judges
only the ambiguous remainder. That stack runs in two places: **online** (per new entry, as a game
ends) and **batch** (the whole store swept in clusters, offline). This doc is the current truth of how
those run; the path that got here is [experiment_log.md](experiment_log.md).

```
new entry ─▶ cosine candidate gather ─▶ GATE (role/phase + gate_key + pair-checks)
                                          ─▶ embedding PRE-FILTER (auto-keep / auto-discard)
                                             ─▶ LLM (middle band only)
online:  KEEP / DISCARD               batch: KEEP / DISCARD / MERGE
```

## Guarantee / contract (present-tense)

- **The gate is hard, retrieval is soft.** Two entries are *never* merged across different roles,
  phases, `gate_key` buckets, or incompatible pair-checks — a wrong merge destroys a distinct lesson,
  so the partition that feeds dedup is deterministic and conservative. (The same dimensions are only
  *soft* rerank signals at retrieval time — the hard gate is dedup-path only.) Enforced in
  `Agents/memory/dedup_gate.py`, applied online in `Agents/memory/deduplication/pipeline.py` and in
  batch clustering in `Agents/memory/batch_deduplication/clustering.py` (`gate_enabled=True` default).
- **Online dedup is KEEP/DISCARD only.** The per-game model is offered exactly two actions; MERGE
  (rewriting) lives only in the offline batch pass (`Agents/memory/deduplication/schemas.py:84-91`).
- **Old lessons are only absorbed *into*, never away.** In incremental batch mode an operation that
  would delete or rewrite an already-settled old entry is rejected at the apply layer, so re-runs
  converge instead of eroding the store (`operations.py` freeze guard, below).
- **Counts are preserved on collapse.** When entries collapse onto a survivor, `observation_count` and
  the usage counters are summed, so combined weight is never lost (`batch_deduplication/operations.py`).
- **Defaults are conservative.** Online dedup is on during store-build; batch dedup is built but
  **off by default**; clustering defaults to the bounded (non-transitive) mode. See the config table.

## The online pipeline (`Agents/memory/deduplication/`)

Runs in `post_game_analysis` (`Agents/nodes/orchestrator.py`) after each game when
`dump_enabled=True` (default; `Agents/memory/persistence/config.py:89`) — i.e. during store-build /
seeding, not in the middle of live play. Per newly extracted entry (`_dedup_single_memory`,
`pipeline.py`):

1. **Cosine candidate gather** — `store.search` on the situation embedding pulls neighbours above the
   0.55 candidate floor.
2. **Gate filter** (`pipeline.py:279`) — narrows those candidates to the same `gate_key` bucket and
   compatible pair-checks (see *The gate*). The LLM only ever sees within-bucket candidates, with the
   gated dimensions stripped from its view (`situation_for_dedup`).
3. **Embedding pre-filter** (`pipeline.py:287`) — auto-discard if similarity ≥ the discard threshold,
   auto-keep if below the keep threshold; otherwise fall through (see *The embedding pre-filter*).
4. **LLM** — judges the ambiguous middle band: DISCARD (bump the survivor's count) or KEEP (store as
   new). Prompts are a stabilized "v6.1" generation in `Agents/prompts/dedup.py`, carrying the v9d
   action-before-situation field ordering for strategy points.

## The batch pipeline (`Agents/memory/batch_deduplication/`)

The offline whole-store sweep. `orchestration.py` runs `cluster → resolve → apply` per gate partition
per namespace `(memory_kind, role, action_phase)`:

- **Cluster** (`clustering.py`) — within each gate partition, group near-duplicates. Default
  `cluster_mode="bounded"` (`config.py:86`): greedy, size-capped, non-transitive — the conservative
  mode the retrieval-impact study argued for. `connected` (transitive) and `agglomerative` (re-embed +
  scipy linkage) also exist.
- **Resolve** (`cluster_agent.py`) — the LLM returns KEEP / DISCARD / **MERGE** operations per cluster.
  The recommended config is **two-pass**: flash-lite triages cheaply, 2.5-pro verifies and writes the
  merge text (`TwoPassConfig`; `two_pass=True` within the incremental config).
- **Apply** (`operations.py`) — collapse onto a survivor, summing counts; an invalid survivor key fails
  safe (no deletion). Dry-run by default unless `apply=True`.

Two modes share this machinery, differing only at the apply layer:

| Mode | Trigger | Freeze guard | Convergence |
|---|---|---|---|
| **#2 Incremental / scheduled** | post-game when enabled; processes only clusters touching a new key | **ON** — `new_keys` set is threaded through; old-vs-old ops rejected | converges (old frozen) |
| **#3 System-wide** | manual full sweep (CLI) | OFF — `new_keys=None`; full re-litigation allowed | not idempotent (re-runs erode) |

**The freeze-old guard (mode #2)** is the fix the [incremental_convergence.md](incremental_convergence.md)
diagnosis called for, and it is **live** (commit `6704202`, 2026-06-16): `_frozen_old_conflict`
(`operations.py:137-150`) rejects any operation with ≥2 old keys (status `"frozen"`, 0 deletions);
`_resolve_survivor(new_keys=…)` (`operations.py:112-134`) forces an old entry as the survivor when one
is present, so new is absorbed into old and never the reverse; threaded via
`orchestration._apply_cluster_operations(new_keys=…)` (`orchestration.py:227`) and counted in
`NamespaceStats.frozen` (`schemas.py:95`). Covered by `tests/test_batch_dedup.py`.

## The gate (`Agents/memory/dedup_gate.py`)

The deterministic partition shared by both pipelines. With v6's many structured dimensions, "is this a
duplicate?" is not a reliable high-dimensional LLM/cosine call — so the hard fields gate
**deterministically** (gate-then-embed), collapsing the LLM's job to the free-text residual within an
already-homogeneous bucket.

- **`gate_key` (partition).** Observations: `(is_swing, alive_bucket, consensus_direction)` where
  `alive_bucket` ∈ {early 8-9 alive, mid 5-7, late ≤4}. Strategy points: `(direction, honesty)`. Kept
  minimal — more partition dimensions → singleton buckets.
- **Pair-checks (hard compatibility within a bucket).** `net_verdict`, `info_landscape_class`,
  `exposure_class` must all agree; differ → never a duplicate. These are playbook-invalidating, added
  as pair-checks (not partition keys) to avoid over-fragmenting.
- **Backward-compatible.** Returns `None` for pre-v6 (v5) entries → the gate is a no-op on old stores
  (legacy un-gated clustering still available behind `gate_enabled`).

## The embedding pre-filter (`Agents/memory/deduplication/`)

Zero-error similarity thresholds, calibrated on a 65-case golden set + 232-case cross-game set
(`Agents/memory/deduplication/config.py`):

| Constant | Value | Decision |
|---|---|---|
| `SP_ACTION_DISCARD_THRESHOLD` | 0.93 | action_sim ≥ → auto-discard |
| `SP_ACTION_KEEP_THRESHOLD` | 0.81 | action_sim < → auto-keep |
| `OBS_CONTENT_DISCARD_THRESHOLD` | 0.96 | content_sim ≥ → auto-discard |
| `OBS_CONTENT_KEEP_THRESHOLD` | 0.935 | content_sim < → auto-keep |

Auto-decision coverage plateaus at ~15-30% and that is a **ceiling, not a tuning shortfall**:
embeddings capture topic, not stance, so two contradictory lessons on the same topic embed nearly
identically and only the LLM can separate them (3072-dim and `SEMANTIC_SIMILARITY` ablations both came
back negative — see [embedding_prefilter/](embedding_prefilter/experiment_log.md)).

## Config / defaults

| Flag | Default | Where | Effect |
|---|---|---|---|
| `dump_enabled` | **True** | persistence/config.py:89 | gates online dedup (runs post-game) |
| `IncrementalDedupConfig.enabled` | **False** | persistence/config.py:51 | post-game batch pass dormant unless enabled |
| `two_pass` (incremental) | True | persistence/config.py:52 | flash-lite triage → 2.5-pro verify |
| `cluster_mode` | `bounded` | batch_deduplication/config.py:86 | conservative, non-transitive clustering |
| `gate_enabled` | True | batch_deduplication/config.py | gate-partition clustering (no-op on v5 stores) |

## Verification

**Verdict.** Each layer is validated by the evidence that built it, and the conservative-by-default
posture is the deliberate outcome of the one result that got overturned. Specifically: store dedup
improves retrieval *when conservative* (n=39, [store_retrieval_impact/](store_retrieval_impact/experiment_log.md));
the online prompt reaches ~80%/83% strict golden accuracy with MERGE removed
([per_extraction/](per_extraction/experiment_log.md)); the batch two-pass reaches 89.2% on the 111-key
golden set ([batch_prompt_tuning/](batch_prompt_tuning/experiment_log.md)); the pre-filter thresholds
are zero-error on golden + cross-game ([embedding_prefilter/](embedding_prefilter/experiment_log.md)).

**Split of concerns.** *Decision quality* (does it merge the right things) is empirical — golden-label
accuracy + downstream retrieval impact, in the sub-logs; an LLM merge can only be judged by an eval.
*Deterministic mechanics* (gate partitioning, survivor selection, count summing, the freeze-old guard,
dry-run safety) are unit-tested in `tests/test_batch_dedup.py` — these are the bugs an aggregate metric
can't isolate.

## Current-vs-documented gaps (freshness: 2026-06-25)

The sub-logs are dated records of the v4/v5 era; this table is the audit trail of where the live v6
code has since moved, ordered by how misleading the stale doc is to a reader.

| # | Gap | What the doc says | What the code does | Severity |
|---|---|---|---|---|
| 1 | **Freeze-old guard** | [incremental_convergence.md](incremental_convergence.md): Fix 2 "not yet built" | **Built & live** (commit `6704202`, 2026-06-16; `operations.py:137-150`, tests) | High — doc reads as an open risk that is actually closed; corrected via that doc's banner |
| 2 | **`created_at` on merge (Fix 1)** | proposed alongside Fix 2 | **Still NOT built** — `created_at` lives only on the envelope and resets on re-put (`operations.py:99-105`, `incremental.py:42`) | Medium — Fix 1 underpins Fix 2's old/new partition across runs; genuinely open |
| 3 | **The deterministic gate** | absent from every evidence doc | **Live** online + batch (`dedup_gate.py`, `gate_enabled=True`) | Medium — the most important current mechanism, undocumented before this report |
| 4 | **Namespace scoping** | [batch_architecture.md](batch_architecture.md): "dedup within a namespace" | namespace **+ gate bucket** (`clustering.partition_key_for`) | Low — additive; banner added to that doc |
| 5 | **Online MERGE** | per_extraction journeys MERGE v1→v11 | **removed** — KEEP/DISCARD only (`schemas.py:84-91`) | Low — the log's own endpoint; stated as live in its close |
| 6 | **Prompt version** | logs cite v9d / v11b | live = stabilized "v6.1" in `Agents/prompts/dedup.py` (same v9d ordering) | Low — naming only |
| 7 | **Run defaults** | scattered across logs | online on (`dump_enabled`); incremental off; bounded; gate on | Low — consolidated in the config table above |

**Open work (not just stale docs):** gap #2 (`created_at` preservation) is the one genuine
not-yet-built item — without it, the old/new partition that the freeze-old guard relies on is only
trustworthy within a single run, so unbounded repeated incremental runs could still drift. It is a
prompt-neutral apply-layer change; tracked in [incremental_convergence.md](incremental_convergence.md).
