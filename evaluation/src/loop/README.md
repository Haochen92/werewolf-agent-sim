# `loop/` — the v7 generational compounding loop

This package is the **v7 compounding-loop harness**: the on-policy experiment that asks whether an
agent that plays, extracts memory from its own games, credits that memory by realized outcome, and
consolidates it — gets **better across generations**. It is a generational A/B (memory-ON arm vs a
flat memory-OFF baseline), one harness, every lever toggleable via `LoopConfig` (config-flag policy:
variants coexist so they can be compared).

The loop "works" iff per-generation decision quality slopes UP against the flat baseline (`measure`);
that slope is the whole deliverable.

## The cycle (one generation)

```text
        ┌───────────────────────────────────────────────────────────────┐
        │                                                               │
        ▼                                                               │
  run games (driver → run_batch)      play N games on the run store,     │
        │                             extract obs + strategy points back │
        │                             (parallel games merged in via      │
        │                              freeze-old dedup: merge.py)        │
        ▼                                                                │
  credit_apply (credit.py)            join each FOLLOWED strategy point   │
        │                             to the de-luck outcome of the       │
        │                             decisions it drove → a ledger;      │
        │                             base rates come from the OFF arm;    │
        │                             counts RECOMPUTED over a rolling     │
        │                             window (stale credit ages out)       │
        ▼                                                                │
  consolidate (consolidate.py)        PRUNE stably-harmful SPs · EVICT     │
        │                             surfaced-but-never-followed SPs ·    │
        │                             credit-aware SYNTH new SPs for cells  │
        │                             with fresh observations               │
        ▼                                                                │
  generation_score (measure.py)       de-luck decision quality this        │
        │                             generation = the slope proxy         │
        └───────────────────────────────────────────────────────────────┘
                              next generation
```

`invariants.py` runs fail-loud guards at every step so a broken input crashes here (located) instead of
degrading into a plausible-wrong slope; `cost.py` polls realized spend post-hoc.

## Modules

| module | role |
|---|---|
| `driver.py` | the generational **driver** — wires extract (via `run_batch` subprocess) + credit + consolidate + measure into the on-policy loop; the store is run-specific (copied from a base or cold-empty) so canonical stores stay frozen. |
| `config.py` | `LoopConfig` — every lever (credit / synth / prune / decay / model / cadence / window) toggleable; one harness runs all arms. |
| `credit.py` | **(a) credit-apply** — writes realized de-luck credit onto each `StoredStrategyPoint`'s positive/neutral/negative counts over a rolling window; counts are RECOMPUTED (set, not accumulated) each tick, so stale credit ages out (the non-stationarity guard). |
| `credit_backfill.py` | the offline realized-outcome credit **backfill** over existing dumps — closes the `followed-SP × de-luck-decision-outcome` join that nothing joined live; SP-only by design; emits a ledger + validation read and STOPS (no store mutation) until the signal is shown to separate. `credit.py` reuses its scoring. |
| `decision_scoring.py` | mechanical, ground-truthed scoring of a frozen day-vote decision (no LLM, no I/O): vote correctness is a pure roles lookup, `allow_abstain` reconstructed exactly as the live router computes it. Also home of `query_criticality` / `score_vote` (the de-luck + pivotalness primitives credit and measure share). |
| `discussion_tagger.py` | **(d)** the omniscient per-day flash-lite **tagger** — discussion (framing / credibility / role_reveal → ONE coarse de-luck verdict) + night read-quality; the LLM de-luck for the channels the deterministic proxy can't see (discussion has no deterministic proxy; night's proxy is outcome-luck). |
| `consolidate.py` | **(b) consolidation** — on a credited store: PRUNE de-luck-negative SPs, EVICT surfaced-but-never-followed SPs, credit-aware SYNTH new SPs for cells with fresh obs (existing SPs persist so their credit accumulates); synth is followed by a freeze-old SP dedup so re-synthesis doesn't smear credit across duplicates. |
| `merge.py` | folds parallel games' NEW observations into the run store via **freeze-old dedup** — within a generation games run concurrently off a frozen gen-start snapshot and dump to temp stores; this collapses cross-game duplicates into reinforcement without a shared-store write race. |
| `measure.py` | per-generation de-luck decision quality — the **slope proxy**, overall + per-faction (so the deceiver cells the synthesis fix targets can be watched); pure read over a batch jsonl, no spend. |
| `memory_adherence.py` | the verdict-aware, **outcome-blind adherence judge** (the 3a/3b half of the decision-replay screen). Validation methodology, **NOT in the loop** — it complements the mechanical `decision_scoring` outcome score. |
| `invariants.py` | fail-loud **guards** run every generation — a window that should carry follows but credited nothing, an off-arm that produced no base rates, a generation that scored zero decisions all raise HERE (with context), instead of flowing silently into `loop_history.json`. |
| `cost.py` | post-hoc realized **USD** from Langfuse (`trace.total_cost`) — read-only, fail-soft (a hiccup yields null, never a crashed run), NO auto-abort; a human watches the spend. |

## The seam (what graduates at go-live)

This package deliberately holds **two halves**. The **memory-pipeline half** — `consolidate.py` (store
ops: prune / evict / synthesize), the **credit logic** (`credit.py` / `credit_backfill.py`, which write
realized-outcome counters onto stored strategy points), `merge.py` (folds new observations into the
store — also store-mutating, so the memory half is not one file), and `discussion_tagger.py` — is
planned to **graduate to `Agents/memory/`** when the loop goes live in production (it is production
memory behavior, not measurement). The **eval half — `driver` / `measure` / `invariants` / `cost`** is
the measurement harness that decides *whether* the loop compounds, and stays here.

## Records + forward plan

- **The record:** [`evidence/v7_final/`](../../../evidence/v7_final/) — the v7 campaign (the cheap-screen
  gates, the compounding runs, the tagger de-leak work). Start at its `review_map.md`.
- **The forward plan:** [`evidence/execution_plan/compounding_measurement_plan.md`](../../../evidence/execution_plan/compounding_measurement_plan.md)
  — the claim ladder + power/readout redesign that gate any paid compounding run.
