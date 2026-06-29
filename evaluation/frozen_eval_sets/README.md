# evaluation/frozen_eval_sets/

Frozen replay datasets and gold labels (tracked). Built by the `eval-build-*`
CLIs from Langfuse traces; consumed by the `eval-*` runners.

## Scope: this folder holds SHARED sets only

A set lives here only if it is **reusable** — consumed by ≥2 configs/experiments,
or built as a standing benchmark (e.g. `v4_filtering_eval`, used across
reranking / filtering / store_dedup). A set built for **one** study is
experiment-specific and belongs in `evidence/<experiment>/eval_sets/`, frozen with
that study — not here.

Each set declares its scope in its `<id>.manifest.json` sidecar:

- `"scope": "shared"` — reusable; this is the correct home.
- `"scope": "experiment:<name>"` — built for one study; its home is
  `evidence/<name>/eval_sets/`. A copy sitting here is a temporary resident
  awaiting migration.
- optional `"consumers": [...]` — the configs/experiments that read it; ≥2 is the
  objective test for "shared".

The `scope` field is the forward standard; existing manifests get it during the
frozen-set review. A set with **no** manifest is presumed legacy.

## Layout

- Grouped by domain subfolder once a domain has ≥2 artifacts; shared datasets stay
  at root. New artifacts: `<purpose>_vN.jsonl` + a `<id>.manifest.json` sidecar.
- `legacy/` holds concluded-era relics (names untouched, still citable).

See the **Data plane** section in [`../README.md`](../README.md)
for the full convention (taxonomy, manifest/lineage, naming, legacy policy).
