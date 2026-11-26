# The bench runs behind `../README.md`

Graduated on 2026-10-23 with `eval-graduate` from the git-ignored
`evaluation/eval_results/hallucination_bench/`: `haiku_game_403f/` (config
`hallucination_bench_haiku_game.json`) and `haiku_game_403f_vote_v2/` (`..._vote_v2.json`). Each has
`summary.json` and the `judged_<arm>.jsonl` files under `eval_results/`, the tracked config under
`eval_configs/`, and a `.manifest.json` lineage sidecar. A judged file carries every sample's output
with its verdicts, so the `generations_*.jsonl` files were not copied.

`haiku_game_403f_read_compare` was not graduated. Its config,
`evaluation/config/hallucination_bench_haiku_game_compare.json`, is untracked and belongs to another
workstream.
