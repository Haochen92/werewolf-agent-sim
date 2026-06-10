# evaluation/eval_results/

Judge and gold-label scores written by the `eval-*` runners. **Gitignored**
(scratch output) — this README is the only tracked file; the results themselves
are local and safe to clean periodically.

- Domain subfolders mirror `evaluation/config/` / `evaluation/frozen_eval_sets/`; `legacy/` holds
  concluded relics. Lineage is embedded in each result object (it has a JSON
  envelope), not in a sidecar.

See the **Data plane** section in [`../README.md`](../README.md).
