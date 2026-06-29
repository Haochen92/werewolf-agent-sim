# evaluation/config/

Experiment configs (tracked), passed to runners via
`--config evaluation/config/<domain>/<name>.json`.

## What lives here

Reusable, forward-looking configs only: **templates** (`template/`, copy-from
starters) and **standing/live** configs you still run or tweak. A config here is a
*question template*, not the record of a run.

A config that was a one-shot for a now-concluded study does **not** belong here —
its frozen copy lives with the study at `evidence/<exp>/eval_configs/` (the
authoritative record; git history keeps the rest). Don't leave a second, drifting
copy here. The graduation step that moves a keeper run into `evidence/` is in
[`../eval_results/README.md`](../eval_results/README.md).

## Domains

`cross_encoder/ · dedup/ · e2e/ · extraction/ · reranking/ ·
retrieval_filtering/ · store_dedup/ · summary/` — plus `template/` (starters).
The same domain names mirror `evaluation/frozen_eval_sets/` and
`evaluation/eval_results/`. Code-level config (game/model/threshold knobs) stays in
the modules, not here.

## Describing a config

JSON has no comments, so every config may carry a `description` field — a free-text
note on what it is for:

```json
{ "description": "rerank vs filter+rerank on v4_deduped, n=5", "dataset": "...", "...": "..." }
```

It's optional and validated (`_DescribedConfig` in `src/core/config_schema.py`) and
ignored by the runners — but embedded verbatim into the lineage manifest at
graduation, so the recorded recipe self-documents (which a dropped-on-parse comment
would not).

See the **Data plane** section in [`../README.md`](../README.md).
