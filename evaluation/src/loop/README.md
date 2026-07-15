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

The credit layer's **design rationale** — the facts/valence boundary, each valence rule's justification,
baselines, shrinkage, and the open judgment calls — lives in
[`evidence/credit/report.md`](../../../evidence/credit/report.md); this README stays a module map.

## Modules

| module | role |
|---|---|
| `driver.py` | the generational **driver** — wires extract (via `run_batch` subprocess) + credit + consolidate + measure into the on-policy loop; the store is run-specific (copied from a base or cold-empty) so canonical stores stay frozen. |
| `config.py` | `LoopConfig` — every lever (credit / synth / prune / decay / model / cadence / window) toggleable; one harness runs all arms. |
| `credit.py` | **(a) credit-apply** — writes realized de-luck credit onto each `StoredStrategyPoint`'s positive/neutral/negative counts over a rolling window; counts are RECOMPUTED (set, not accumulated) each tick, so stale credit ages out (the non-stationarity guard). |
| `credit_backfill.py` | the offline realized-outcome credit **backfill** over existing dumps — closes the `followed-SP × de-luck-decision-outcome` join that nothing joined live; emits a ledger + validation read and STOPS (no store mutation). `credit.py` reuses its scoring. v1 (2026-07-13): healer night credit (the `night_resolutions` attack-join) + the read-partition (a negative reached through a stated-and-wrong threat-read is excluded, `read_excluded`). |
| `decision_scoring.py` | mechanical, ground-truthed scoring of a frozen day-vote decision (no LLM, no I/O): vote correctness is a pure roles lookup, `allow_abstain` reconstructed exactly as the live router computes it. Also home of `query_criticality` / `score_vote` (the de-luck + pivotalness primitives credit and measure share). |
| `discussion_tagger.py` | the omniscient per-day flash-lite **tagger** — now a standalone DIAGNOSTIC (run post-hoc on stored games). **Retired from credit 2026-07-13** (owner ruling): its night read-quality override is gone and no credit mode invokes it; its validated wolf/SK discussion readout stays a watch instrument. |
| `read_ledger.py` | the **Brier meter** on agent read skill — knowledge-masked (wolf packmates, investigator checks), 'unclear' makes no claim; measures the AGENT, never a memory item; its mem-on/off split is the free book-vs-no-book readout. |
| `first_link.py` | the **first-link diagnostic** — momentum-adjusted read-deltas for targeted day pushes (driver-vs-rider); pre-registered DIAGNOSTIC, never feeds prune/protect/synthesis; graduation goes through the ablation replay. |
| `tells.py` | tell **mining** (omniscient, discovery-only) + the role-blind k=2 **detector** (det_v1 full-view ∪ det_v2 split-view, cached, thinking=low — the golden-parity measurement config). Graduated 2026-07-13 from `evidence/extraction/tell_extraction/` (the probes stay frozen records); prompts verbatim in `tell_prompts/`. |
| `tell_credit.py` | tell-ledger **arithmetic** (pure): exhibitor-grain lift over the cast prior (K=5 shrinkage, pinned to the held-out convention), the §6.5 positive-lift-only eligibility, the role-grain book builder (per-subject-role concentration, every unrevealed role — NO role-revealing exclusion, ruled 2026-07-14) + `build_book_file` (the artifact `Agents/memory/tell_book.py` injects live via `WW_TELL_BOOK`). |
| `tell_fold.py` | the tell **epoch fold** — curatorial, never generative (freeze-old: canonical text never rewritten): exact-match + LLM drop-or-keep wording dedup into canon, the probation clock (K=12 scanned games), fat-null archive with split-check, publishes the frozen `checklist_v{k+1}`. |
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
store — also store-mutating, so the memory half is not one file), and the tell pipeline
(`tells.py` / `tell_credit.py` / `tell_fold.py`, whose live half already sits in
`Agents/memory/tell_book.py`) — is
planned to **graduate to `Agents/memory/`** when the loop goes live in production (it is production
memory behavior, not measurement). The **eval half — `driver` / `measure` / `invariants` / `cost`** is
the measurement harness that decides *whether* the loop compounds, and stays here.

## Records + forward plan

- **The record:** [`evidence/v7_final/`](../../../evidence/v7_final/) — the v7 campaign (the cheap-screen
  gates, the compounding runs, the tagger de-leak work). Start at its `review_map.md`.
- **The forward plan:** [`evidence/execution_plan/compounding_measurement_plan.md`](../../../evidence/execution_plan/compounding_measurement_plan.md)
  — the claim ladder + power/readout redesign that gate any paid compounding run.
