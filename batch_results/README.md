# batch_results/

Per-game run logs written by `scripts/run_batch.py` — one JSONL record per game,
self-stamped with `runtime_fingerprint` + configs. The filename
(`<session_prefix>.jsonl`) doubles as the Langfuse session link, so files are
**never renamed**. **Gitignored** — this README is the only tracked file.

- Stays **flat** (games are domain-agnostic inputs). `legacy/` holds concluded
  smoke/superseded runs and non-game strays (cluster/analysis dumps).

See the **Data plane** section in [`../evaluation/README.md`](../evaluation/README.md).
