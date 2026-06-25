# Batch Dedup — How It Works

> **Freshness (2026-06-25):** v6 adds a deterministic **gate** (`Agents/memory/dedup_gate.py`) that
> partitions candidates by a `gate_key` + hard pair-checks *on top of* the
> `(memory_kind, role, action_phase)` namespace described below — so "dedup within a namespace" is now
> "within a namespace **and** a gate bucket," shared with the online pass. Current live state + the
> full gap list: [report.md](report.md).

The rest of `evidence/dedup/` documents the **why and the results** (retrieval impact,
golden-label prompt tuning, the "conservative beats aggressive" finding). This doc is the
**how** — the mechanics of `Agents/memory/batch_deduplication/`, so the design is
explainable end-to-end without re-reading the code.

Batch dedup is the **offline** pass: it sweeps the whole stored memory and collapses
redundant entries. (The per-game `Agents/memory/deduplication/` pipeline is the *online*
pass — it dedups each new entry one at a time as a game ends. Same goal, different scale.)

## The one idea: dedup happens **within a namespace**, never across

A namespace is `(memory_kind, role, action_phase)` — e.g. `(observations, villager,
day_vote)`. Two entries can only be duplicates if they share all three. A villager's
day-vote memory is never compared against a wolf's night memory. So the whole pass is a
triple loop over namespaces, and each namespace is deduped independently.

This is the scoping decision that makes everything else cheap and safe: clusters stay
small and on-topic, and a bad merge can't cross roles/phases.

## The flow (`orchestration.py`)

```
run_batch_memory_dedup(config):
    seed the in-memory store from JSON files on disk
    [incremental] read last-run timestamp, collect keys added since
    for memory_kind in {observations, strategy_points}:
      for role in roles:
        for action_phase in phases(role):
            dedup_namespace(...)          # cluster -> resolve -> apply
    [apply] dump the store back to JSON + stamp a new timestamp
```

`dedup_namespace` is three steps:

1. **cluster** — fetch every entry in the namespace, group near-duplicates into small
   clusters (`clustering.py`).
2. **resolve** — hand each cluster (≥2 entries) to the LLM (`cluster_agent.py`), which
   returns a list of **operations** (KEEP / DISCARD / MERGE, per entry).
3. **apply** — `_apply_cluster_operations` writes each operation to the store and tallies
   stats (`operations.py`).

**Why cluster at all?** You can't put 300 entries in one prompt, and comparing all pairs is
O(n²) LLM calls. Clustering batches likely-duplicates into groups of ≤ `max_cluster_size`
so the LLM resolves a handful at a time. **Clustering decides what gets compared; the LLM
decides what's actually a duplicate.**

## Clustering modes (`clustering.py`, `_build_clusters`)

Three ways to group; chosen by `config.cluster_mode`.

| Mode | How it groups | Trade-off |
|---|---|---|
| `connected` | builds a similarity **graph** (edge if vector-search score ≥ threshold), then takes connected components via BFS | **transitive**: A~B and B~C merge {A,B,C} even if A≁C → high recall but can over-merge / drift into large clusters |
| **`bounded`** (default) | greedy: take the highest-value **seed**, pull its top neighbours above threshold, cap the cluster at `max_cluster_size`, mark them consumed, repeat | bounded size, no transitive drift, each item in exactly one cluster → conservative and controllable |
| `agglomerative` | re-embed all situations, full cosine matrix, scipy hierarchical linkage, cut at `1 − threshold`, chunk by size cap | most principled, but re-embeds everything and needs scipy (heavy) |

Seeds and preferred neighbours are ranked by `_seed_sort_key` / `_neighbor_sort_key`:
**high `observation_count`, then most recently observed** — so the canonical (most-reinforced)
entry leads each cluster. Default is `bounded` because the evidence said to prefer
conservative dedup, and bounded is the mode that mechanically enforces it.

## Applying an operation (`operations.py`)

For DISCARD/MERGE the cluster collapses onto a **survivor**:

- **survivor** = the LLM's `survivor_key`, defaulting to the first source key; if it isn't a
  real key in the cluster, the operation **fails safely** (no deletion) rather than guessing.
- **metadata is merged onto the survivor** — `observation_count` and the usage counters
  (`retrieved_count`, `used_count`, `positive/neutral/negative_count`) are **summed** across
  the whole cluster, `last_observed` takes the latest, `game_id` stays the survivor's. So
  collapsing five entries into one preserves their combined weight.
- **content**: DISCARD keeps the survivor's own text; MERGE adopts the LLM's `merged_*`
  text. (Strategy points only DISCARD/KEEP; observations also MERGE.)
- **absorbed entries are deleted**; the count of deletions is returned for stats.
- **dry-run** (`apply=False`, the default): every decision is computed and counted, but the
  store is never written or deleted — this is what `--cluster-report-only` and any
  non-`--apply` run produce.

## Two knobs

- **two-pass** (`config.two_pass`, off by default): a second LLM pass over the survivors to
  catch duplicates the first pass missed across cluster boundaries.
- **incremental** (`config.incremental`, off by default): only process clusters that contain
  a key added since the last run — skip all-old clusters. This is the convergence-sensitive
  path: re-litigating old entries against new neighbours erodes the store non-deterministically
  past a point (see `incremental_convergence.md` for the diagnosis and the freeze-old fix).

## How it's verified

- **Decision quality** (does it merge the *right* things) → empirical, in this folder:
  golden-label accuracy on the cluster prompts (`batch_prompt_tuning/`) and downstream
  retrieval impact (`store_retrieval_impact/`). An LLM merge can only be judged by an eval,
  not a unit test.
- **Deterministic mechanics** (clustering construction, survivor selection, count merging,
  dry-run safety) → `tests/test_batch_dedup.py`. These are the bugs an eval can't isolate
  — a wrong graph edge or a mis-picked survivor is silent in aggregate metrics.

## Interview cheat-sheet (the probes that actually come)

- **Why dedup?** Redundant memories crowd retrieval; conservative dedup raised observation
  efficiency and unique-lessons without losing relevance (n=39).
- **Why per-namespace?** Duplicates only exist among same-role, same-phase entries; scoping
  keeps clusters small/on-topic and bounds the blast radius of a bad merge.
- **Why cluster instead of comparing all pairs?** Cost — batches likely-dups into small
  groups so the LLM sees a handful at a time instead of O(n²) calls.
- **What if the LLM over-merges two non-duplicates?** Bias conservative (bounded default +
  size cap contains it), and an invalid survivor fails safe rather than deleting blindly.
- **How do you avoid losing signal when collapsing entries?** Usage counters are summed onto
  the survivor, so combined weight is preserved.
- **Online vs batch?** Online = per-entry as each game ends (threshold prefilter → LLM,
  keep/discard only); batch = offline whole-store sweep with clustering + merge.
