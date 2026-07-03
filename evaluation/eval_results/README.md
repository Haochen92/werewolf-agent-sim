# evaluation/eval_results/

**Throwaway staging.** The landing zone where the `eval-*` runners dump every run
during iteration — tuning sweeps, partial or aborted runs, re-runs for more
samples. **Gitignored**; this README is the only tracked file, and the contents
are safe to delete at any time.

Nothing here is the record. When a run is a *keeper*, **graduate** it into
`evidence/<experiment>/`: copy the result under `eval_results/` there, copy the
exact config that produced it under `eval_configs/`, and narrate it in `report.md`.
The tracked, citable artifact is the evidence copy — this folder is only the
scratch it came from.

- Keep it flat scratch. Do **not** use it as a second archive (that is
  `evidence/`'s job). Any `legacy/` or domain subfolders here are residual and
  unversioned.
- Scratch results carry no guaranteed lineage. Lineage (git SHA, config hash,
  content-hashed inputs) is stamped **at graduation** so the evidence copy is
  reproducible even after stores/datasets drift — see `../src/core/manifest.py`.

Graduate with:

```bash
poetry run python -m evaluation.src.cli_runner.graduate_run \
  --result evaluation/eval_results/<run>.jsonl \
  --config evaluation/config/<domain>/<name>.json \
  --experiment retrieval/store_dedup        # evidence/<experiment>; --dry-run to preview
```

It copies the result + the exact config into `evidence/<experiment>/`, content-hashes
the inputs the config named, and writes a `<run>.manifest.json` sidecar. A referenced
input that is missing is **reported** (broken chain), not silently dropped. Once
graduated, **delete the source config from `evaluation/config/`** unless it is a
reusable template — git history and the evidence freeze both preserve it, and a
second copy only drifts. The `eval-graduate` console alias is registered in
`pyproject.toml` and resolves after the next `poetry install`.

See the **Data plane** section in [`../README.md`](../README.md).
