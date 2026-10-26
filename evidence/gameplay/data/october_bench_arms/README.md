# The October bench arms (2026-10-03 and 04, nine-seat)

Five hallucination-bench runs on `evaluation/frozen_eval_sets/hallucination_bench_v2.jsonl`, with
gemini-3.5-flash-lite seats. They are recorded in `../../discussion_evidence.md` §6.5 (the fidelity pass),
§6.6 (day summary v4, the per-player vote history, record citation) and §6.7 (the thinking budget):

| Folder | Record |
|---|---|
| `fidelity_pass_flashlite35/` | §6.5 |
| `summary_v4_flashlite35/` | §6.6 |
| `summary_v4_vote_history_flashlite35/` | §6.6 |
| `summary_v4_cite_flashlite35/` | §6.6 |
| `thinking_flashlite35/` | §6.7 (also the reasoning-token scope probe's bench run) |

These were copied byte for byte from the git-ignored `evaluation/eval_results/hallucination_bench/<folder>/`
on 2026-10-23, at commit `1a5c0da1`. The copy keeps `summary.json`, the `judged_<arm>.jsonl` files and
`unit_comparison.json` where it exists. A judged file carries every sample's output with its verdicts, so
the `generations_*.jsonl` files were not copied. The `summaries_*.json` files were not copied either: they
are the day summaries the arms regenerated as inputs.

**A plain copy, not `eval-graduate`.** The tracked templates for these runs
(`evaluation/config/template/hallucination_bench_{fidelity_pass,summary_v4,vote_history,record_citation,thinking}.json`)
were edited after the runs. Commit `e70f1627` (2026-10-12) moved their judges to Claude Haiku 5.5. Graduating
against them would record the wrong judges. Instead, the config each run actually used is embedded in its
`summary.json` under `config`, with `run_at`. The judges were gemini-3.1-flash-lite for recall and the
expectations, and gemini-3.5-flash for precision.
