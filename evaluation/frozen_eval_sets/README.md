# evaluation/frozen_eval_sets/

Frozen replay datasets and gold labels (tracked). Built by the `eval-build-*`
CLIs from Langfuse traces; consumed by the `eval-*` runners.

- Grouped by domain subfolder once a domain has ≥2 artifacts; shared datasets stay
  at root. New artifacts: `<purpose>_vN.jsonl` + a `<id>.manifest.json` sidecar.
- `legacy/` holds concluded-era relics (names untouched, still citable).

See the **Data plane** section in [`../README.md`](../README.md)
for the full convention (taxonomy, manifest/lineage, naming, legacy policy).
