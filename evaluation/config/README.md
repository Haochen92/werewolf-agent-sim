# evaluation/config/

The single home for experiment configs (tracked). Passed to runners via
`--config evaluation/config/<domain>/<name>.json`. Grouped by domain:

`ablation/ · capacity/ · cross_encoder/ · dedup/ · e2e/ · extraction/ ·
reranking/ · retrieval_filtering/ · store_dedup/` — plus `template/` (starters).

The same domain names are mirrored in `evaluation/frozen_eval_sets/` and `evaluation/eval_results/`. Code-level
config (game/model/threshold knobs) stays in the modules, not here.

See the **Data plane** section in [`../README.md`](../README.md).
