# evaluation.training

A small, composable harness for fine-tuning cross-encoders, mirroring
`evaluation.labeling`. One shared engine + pluggable per-task adapters, so adding
a new model-training task means writing an adapter — not another bespoke script.

It replaces the per-experiment `train_*_modal.py` / `eval_*_modal.py` scripts
that used to live under `evidence/fine_tuning/cross_encoder/`.

## Philosophy

- **Training runs on Modal only** (L4 GPU). Heavy deps (`datasets`, `accelerate`)
  live in the Modal image, not in the local environment.
- **Local machines are inference-only.** Evaluating a saved model needs just
  `sentence-transformers` (already a project dep) — cross-encoder inference is
  cheap enough to run on CPU.

## Layout

| File | Responsibility |
|------|----------------|
| `config.py` | `TrainConfig` — hyperparameters + run identity (JSON-serializable) |
| `base.py` | `TrainingAdapter` ABC + `DatasetBundle` — the per-task contract |
| `engine.py` | the shared training loop (runs inside the Modal container) |
| `evaluator.py` | `RankingEvaluator`, `BinaryClassificationEvaluator` — standalone metrics |
| `manifest.py` | per-run reproducibility record (`manifest.json` next to the model) |
| `evaluate.py` | `python -m evaluation.training.evaluate` — CPU eval of a saved model |
| `runner/modal_runner.py` | the Modal GPU training backend |
| `adapters/reranker.py` | relevance-regression CE (retrieval reranker) |
| `adapters/dedup.py` | binary Keep/Discard CE (auto-dedup pre-filter) |

The data flow is split so the *same* adapter runs locally and in the container:

```
read_raw()        disk reads — runs locally, returns a JSON payload
   │              (shipped to the GPU container verbatim)
build_datasets()  pure transform — runs wherever training executes
```

## Train (Modal)

```bash
poetry run modal run evaluation/training/runner/modal_runner.py \
    --adapter reranker --run-name reranker_v5 --epochs 20

poetry run modal run evaluation/training/runner/modal_runner.py \
    --adapter dedup --run-name ce_minilm_dedup_v2 --epochs 10
```

Outputs land on the `cross-encoder-training-output` Modal volume with a
`manifest.json` (config + git SHA + data fingerprint + metrics). Download:

```bash
modal volume get cross-encoder-training-output reranker_v5/ ./models/cross_encoder/reranker_v5/
```

## Evaluate a saved model (CPU, no GPU)

```bash
poetry run python -m evaluation.training.evaluate \
    --adapter reranker --model models/cross_encoder/reranker_v4 --split test
# {"ndcg3": 0.885, "ndcg5": 0.882, "ndcg10": 0.866, "pearson_r": 0.570, ...}

poetry run python -m evaluation.training.evaluate \
    --adapter dedup --model models/cross_encoder/ce_minilm_dedup_run1
# {"average_precision": 0.839, "best_f1": 0.756, ...}
```

These numbers reproduce the published results in the experiment logs exactly —
the harness was validated against the saved `reranker_v4` and
`ce_minilm_dedup_run1` models before retiring the old eval scripts.

## Adding a new adapter

Subclass `TrainingAdapter`, implement three methods, and register it. Example
(an embedding-style task):

```python
# evaluation/training/adapters/mymodel.py
from ..base import DatasetBundle, TrainingAdapter
from ..evaluator import Evaluator, RankingEvaluator

class MyAdapter(TrainingAdapter):
    name = "mymodel"

    def read_raw(self) -> dict:
        # disk reads (runs locally) -> JSON-serializable payload
        return {"train": [...], "eval": [...]}

    def build_datasets(self, raw: dict) -> DatasetBundle:
        from datasets import Dataset
        ...  # raw -> HF Datasets (+ eval_raw for the evaluator)
        return DatasetBundle(train=train_ds, eval=eval_ds, eval_raw=raw["eval"])

    @property
    def evaluator(self) -> Evaluator:
        return RankingEvaluator()   # or BinaryClassificationEvaluator(), or your own
```

Override only when defaults don't fit:
- `load_model(base_model)` — defaults to `CrossEncoder`; override for a different class.
- `trainer_evaluator(bundle)` — an in-loop sentence-transformers evaluator
  (e.g. `CEBinaryClassificationEvaluator`); defaults to `None` (loss-based selection).
- `metric_for_best_model` — checkpoint-selection metric (defaults to `"eval_loss"`).
- `held_out_records(split)` — records for standalone eval (defaults to the eval split).

Then register it in `adapters/__init__.py`:

```python
from .mymodel import MyAdapter
REGISTRY = {..., MyAdapter.name: MyAdapter}
```

Now `--adapter mymodel` works for both training and `evaluate`. Write a custom
`Evaluator` subclass when your metric isn't ranking or binary classification.
