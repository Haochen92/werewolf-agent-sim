# The bench runs for the deduction injection and the healer's silence

Graduated on 2026-10-23 with `eval-graduate` from the git-ignored
`evaluation/eval_results/hallucination_bench/`: `deduction_injection/` (config
`hallucination_bench_deduction_injection.json`, cases `../cases.jsonl`) and `healer_silence/`
(`hallucination_bench_healer_silence.json`, cases `../silence_cases.jsonl`). Record:
`../../../experiment_log.md` §4–§5. Each has `summary.json` and the `judged_<arm>.jsonl` files under
`eval_results/`, the tracked config under `eval_configs/`, and a `.manifest.json` lineage sidecar. A
judged file carries every sample's output with its verdicts, so the `generations_*.jsonl` files were
not copied.
