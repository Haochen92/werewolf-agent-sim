# `studies/` — concluded one-shot study runners

The apparatus behind frozen design verdicts. Each module ran **once** to settle a specific design
question; kept runnable/importable for provenance and re-inspection, but **NOT** part of the live CLI
surface (no console entry). Contrast:

- `audits/` — meant to be **re-run** as regression checks (is the SYSTEM behaving as recorded?).
- `instrument_validation/` — **standing** re-certification of the measurement rulers.
- **`studies/`** — a settled question; the verdict below is **frozen** and the evidence pointer is
  authoritative.

Grouped by era. Verdicts and evidence pointers are carried verbatim from the retired `__init__.py` table.

## v5-era store builds

| module | question it answered | verdict | evidence |
|---|---|---|---|
| `extraction_model_comparison` | extraction model choice (v5 era) | (model selection) | — |

## v6 dimension screens & store builds

| module | question it answered | verdict | evidence |
|---|---|---|---|
| `criticality_screen` | criticality-conditioned vs flat retrieval | within noise → v6 skipped query-time conditioning | evidence/extraction/situation_dimensions/criticality_screen/ |
| `forced_schema_screen` | forced per-memory applicability reasoning | harmful on v5, safe on v6; prompt-body delivery adopted | evidence/memory_system/strategy_adoption/forced_schema_screen/ |
| `dimension_gating_screen` | dimension-gated retrieval | negative, shipped default-off (frozen verdict); RE-OPENED 2026-07-02 by the dimension audit → standing-again, MOVED 2026-07-04 to `evaluation/src/instrument_validation/dimensions/dimension_gating_screen.py` | evidence/v7_final/review_map.md + evidence/extraction/situation_dimensions/dimension_accuracy_audit/ |
| `reextract_villager_day` | build v6 store from historical games (extraction) | (store build) → v6/v6_1 | evidence/extraction/situation_dimensions/v6_full_store.md |
| `reextract_cells` | build v6 store from historical games (full DAG) | (store build) → v6/v6_1 | evidence/extraction/situation_dimensions/v6_full_store.md |
| `synthesize_cell_sp` | build v6 store from historical games (SP synthesis) | (store build) → v6/v6_1 | evidence/extraction/situation_dimensions/v6_full_store.md |

## v7 credit-loop trials

| module | question it answered | verdict | evidence |
|---|---|---|---|
| `decision_replay` | off-policy per-turn vote replay screen | validated memory framing + de-luck proxies | evidence/memory_system/effectiveness/decision_replay/ |
| `synth_deluck_ab` | credit-aware vs outcome-halo synthesis | credit-aware wins → v7 synthesis design | evidence/v7_final/synth_deluck_ab/ |
| `consolidation_prune` | offline credit-prune apply trial | superseded by loop/consolidate.py | evidence/v7_final/review_map.md |
| `investigator_transmission` | do investigator finds reach the village? | finds don't reach → motivated cross-game synthesis; superseded by the 2026-07-02 scheduler access audit | evidence/memory_system/effectiveness/v6_sp_ab/ |

## Dedup calibration

| module | question it answered | verdict | evidence |
|---|---|---|---|
| `batch_dedup_merge_eval` | batch-dedup merge quality | batch dedup parked default-off | — |
| `eval_auto_dedup` | embedding-prefilter threshold calibration | rerun only on embedding-model change | — |
| `auto_dedup_dataset_builder` | dataset builder for the embedding-prefilter calibration | rerun only on embedding-model change | — |

## How to run

Each is a package module, run from the repo root, e.g.:

```bash
poetry run python -m evaluation.src.studies.criticality_screen
```

They are off the CLI surface by design (no `eval-*` console entry); nothing live imports them, but the
frozen `evidence/v7_final/` scripts and two held re-screens (dimension-gating, wolf) do.
