# Admission records and admission bench arms

Graduated on 2026-10-23 from the git-ignored `evaluation/eval_results/` with `eval-graduate`
(`evaluation/src/cli_runner/graduate_run.py`), so the numbers in `../report.md` can be re-checked.
Each folder is one run, named by its label. `eval_results/` holds the files byte for byte,
`eval_configs/` the tracked config that produced them, and each `<name>.manifest.json` the lineage
stamped at graduation: the graduating commit, a config hash and a hash of the frozen cases the config
names. The commit in a manifest is the graduation commit. The run's own commit is in the record's
`runtime_fingerprint` (admission) or in `summary.json` (`run_at`, embedded `config`).

**Admission runs** (`eval-model-admission`; one JSON per model). Eleven labels, 20 records, from
2026-10-04, 10-11 and 10-13. Four configs share the label `admission_2026_10_04`. Each model's record
was matched to its config by the model the config names: DeepSeek V4 Pro from
`admission_2026_10_04.json`, flash-lite from `_flashlite`, Qwen from `_candidates`, GLM and MiniMax
from the `_glm_minimax` rerun, and Luna from the `_luna` rerun. These records do not embed their config, so
the match rests on the label and the model. The configs have not been edited since the runs (git log).

**Admission bench arms** (`eval-hallucination-bench`): `admission_bench_2026_10_04`,
`admission_bench_glm_2026_10_04`, `phase3_luna`, `phase3_haiku`, `phase3_haiku_low`,
`phase3_luna_haiku`, `phase3_haiku_summary` and `shared_prefix_luna_2026_10_13`. Each has
`summary.json` and the `judged_<arm>.jsonl` files. A judged file carries every sample's output with
its verdicts, so the `generations_*.jsonl` files were not copied. Each run's `summary.json` config was
checked to be identical to the tracked config graduated beside it.
