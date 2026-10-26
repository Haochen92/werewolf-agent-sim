# The bench runs behind `../README.md`

The full bench output, moved on 2026-10-23 from the git-ignored
`evaluation/eval_results/hallucination_bench/<run>/`. Each run keeps `summary.json` and the
`judged_<arm>.jsonl` files. A judged file carries every sample's output with its verdicts, so the
`generations_*.jsonl` files were not copied.

- `phase3_f02_rule/`, `phase3_f02_hierarchy/`, `phase3_f02_wording/`, `phase3_sentinel_before/` and
  `phase3_sentinel_after/` were graduated with `eval-graduate`. Each has its files under `eval_results/`,
  the tracked config under `eval_configs/`, and a `.manifest.json` lineage sidecar. Each run's embedded
  config matched the tracked one.
- `phase3_turns/` is a plain byte copy. Its tracked config
  (`evaluation/config/hallucination_bench_phase3_turns.json`) changed after the run: the first arm's
  worktree path, the note, and the `rejudge` flag set for the corrected-expectation pass are different.
  The config the run used is embedded in `summary.json` under `config`.
