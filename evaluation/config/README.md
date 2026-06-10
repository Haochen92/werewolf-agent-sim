# eval_configs/

The single home for experiment configs (tracked). Passed to runners via
`--config eval_configs/<domain>/<name>.json`. Grouped by domain:

`ablation/ · capacity/ · cross_encoder/ · dedup/ · e2e/ · extraction/ ·
reranking/ · retrieval_filtering/ · store_dedup/` — plus `template/` (starters).

The same domain names are mirrored in `eval_sets/` and `eval_results/`. Code-level
config (game/model/threshold knobs) stays in the modules, not here.

See the **Data plane** section in [`../evaluation/README.md`](../evaluation/README.md).
