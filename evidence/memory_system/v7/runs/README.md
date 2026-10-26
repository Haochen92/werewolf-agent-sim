# `runs/` — the v7 run-output directories

The paired compounding runs, the smokes, and the synth A/Bs: game-record `.jsonl`, loop history, and
per-generation stores, plus the salvage/retest scripts colocated with the run they operate on
(`v2_full/v2_salvage.py`, `v2_full/tagger_skill_retest.py`, `v2_full/tagger_deleak_ablation.py`).

**Frozen as-is** — dated run outputs, not maintained code. The colocated scripts carry a FROZEN RECORD
stamp.

- Verdicts + run inventory → [`../README.md`](../README.md)
- Standing re-runnable apparatus → `evaluation/src/instrument_validation/`
