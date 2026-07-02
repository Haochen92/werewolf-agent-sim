"""Concluded one-shot study runners — the apparatus behind frozen design verdicts.

Each ran once to settle a specific design question; kept runnable/importable for provenance and
re-inspection, but NOT part of the live CLI surface (no console entry). Contrast ``audits/`` (meant
to be re-run as regression checks). Verdicts below are frozen; the evidence pointer is authoritative.

| module                    | question it answered                                              | verdict                                                      | evidence |
|---------------------------|------------------------------------------------------------------|-------------------------------------------------------------|----------|
| criticality_screen        | criticality-conditioned vs flat retrieval                        | within noise → v6 skipped query-time conditioning           | evidence/phase_b/criticality_screen/ |
| forced_schema_screen      | forced per-memory applicability reasoning                        | negative → not adopted                                      | evidence/phase_b/forced_schema_screen/ |
| dimension_gating_screen   | dimension-gated retrieval                                        | negative, shipped default-off; RE-OPENED 2026-07-02 by the dimension audit (queued re-screen runs this file) | evidence/v7_final/review_map.md + evidence/phase_b/dimension_accuracy_audit/ |
| decision_replay           | off-policy per-turn vote replay screen                           | validated memory framing + de-luck proxies                 | evidence/memory_system/effectiveness/decision_replay/ |
| reextract_villager_day    | build v6 store from historical games (extraction)               | (store build) → v6/v6_1                                     | evidence/phase_b/v6_full_store.md |
| reextract_cells           | build v6 store from historical games (full DAG)                 | (store build) → v6/v6_1                                     | evidence/phase_b/v6_full_store.md |
| synthesize_cell_sp        | build v6 store from historical games (SP synthesis)             | (store build) → v6/v6_1                                     | evidence/phase_b/v6_full_store.md |
| synth_deluck_ab           | credit-aware vs outcome-halo synthesis                          | credit-aware wins → v7 synthesis design                    | evidence/v7_final/synth_deluck_ab/ |
| consolidation_prune       | offline credit-prune apply trial                                | superseded by loop/consolidate.py                          | evidence/v7_final/review_map.md |
| investigator_transmission | do investigator finds reach the village?                        | finds don't reach → motivated cross-game synthesis; superseded by the 2026-07-02 scheduler access audit | evidence/memory_system/effectiveness/v6_sp_ab/ |
| extraction_model_comparison | extraction model choice (v5 era)                              | (model selection)                                          | — |
| batch_dedup_merge_eval    | batch-dedup merge quality                                       | batch dedup parked default-off                             | — |
| eval_auto_dedup           | embedding-prefilter threshold calibration                       | rerun only on embedding-model change                      | — |
| auto_dedup_dataset_builder | dataset builder for the embedding-prefilter calibration        | rerun only on embedding-model change                      | — |
"""
