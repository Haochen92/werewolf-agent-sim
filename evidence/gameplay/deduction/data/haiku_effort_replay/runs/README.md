# The bench runs for the thinking-budget replay

`haiku_effort_turns/` and `haiku_effort_votes/` were copied byte for byte on 2026-10-23, at commit
`1a5c0da1`, from the git-ignored `evaluation/eval_results/hallucination_bench/`. Record:
`../../../experiment_log.md` §2. Each keeps `summary.json` and the `judged_<arm>.jsonl` files. A judged
file carries every sample's output with its verdicts, so the `generations_*.jsonl` files were not copied.

**A plain copy, not `eval-graduate`.** The tracked configs
(`evaluation/config/hallucination_bench_haiku_effort_{turns,votes}.json`) were edited after the runs.
Their `dataset` path moved from `evidence/gameplay/data/haiku_effort_replay/` to this
folder's parent, and the note changed. The config each run used is embedded in its `summary.json` under
`config`.
