# The July loop run and its endpoint A/B: the run files

The small top-level files of the two runs recorded in `../report.md` §4–5, copied byte for byte on
2026-10-23, at commit `1a5c0da1`, from the git-ignored `batch_results/`. These are generation-run outputs,
not `eval-*` results, so `eval-graduate` does not fit. Each run's `config.json` is the config it ran
under, and its `runtime_fingerprint` holds the run's commit and backend.

- `v7_compound_town5/` (the four-generation build run, 2026-07-17 to 19): `config.json`,
  `loop_history.json` (the per-generation scores and arms), `cost_report.json`, `summary.json` and
  `run_meta.json` (runtime fingerprint).
- `v7_endpoint_ab/` (30 boards × 2 arms, from 2026-07-20): `config.json`, `PREREG_AMENDMENT.md`,
  `endpoint_result.json` (the pooled per-decision scores), `summary.json`, `run_meta.json`,
  `tell_book_final.json` and the run log `v7_endpoint_ab.log`.

Not copied: the per-game records (`gen*_{on,off}.jsonl`, `ep_*.jsonl`), the eval-case sidecars, the game logs,
the store snapshots and the two quarantine folders. They come to 190 MB and 123 MB and stay in
`batch_results/`.
