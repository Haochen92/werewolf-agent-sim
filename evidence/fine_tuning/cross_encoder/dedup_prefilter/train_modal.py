"""Fine-tune cross-encoder for dedup similarity scoring on Modal.

Trains a cross-encoder that scores (situation_A, situation_B) → relevance.
Used to replace cosine similarity in auto-dedup threshold decisions.

Usage:
    poetry run modal run evidence/fine_tuning/cross_encoder/dedup_prefilter/train_modal.py \
        --run-name ce_minilm_run1

    poetry run modal run evidence/fine_tuning/cross_encoder/dedup_prefilter/train_modal.py \
        --base-model BAAI/bge-reranker-base --run-name ce_bge_run1
"""

from __future__ import annotations

import json
import modal

MINUTES = 60

app = modal.App("cross-encoder-finetune")

image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install(
        "sentence-transformers>=3.0",
        "datasets>=3.0",
        "accelerate>=1.1.0",
        "huggingface_hub",
    )
)

vol = modal.Volume.from_name("cross-encoder-finetune-output", create_if_missing=True)


@app.function(
    image=image,
    gpu="L4",
    timeout=30 * MINUTES,
    secrets=[modal.Secret.from_name("huggingface")],
    volumes={"/output": vol},
)
def train(
    data_jsonl: str,
    base_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
    epochs: int = 10,
    batch_size: int = 16,
    lr: float = 2e-5,
    warmup_ratio: float = 0.1,
    run_name: str = "ce_run1",
):
    from sentence_transformers.cross_encoder import CrossEncoder
    from sentence_transformers.cross_encoder.trainer import CrossEncoderTrainer
    from sentence_transformers.cross_encoder.training_args import CrossEncoderTrainingArguments
    from sentence_transformers.cross_encoder.evaluation import CEBinaryClassificationEvaluator
    from datasets import Dataset
    import os
    import random

    os.environ["WANDB_DISABLED"] = "true"

    print(f"Loading base model: {base_model}")
    model = CrossEncoder(base_model)

    raw = [json.loads(line) for line in data_jsonl.strip().split("\n") if line.strip()]
    print(f"Loaded {len(raw)} pairs")

    random.seed(42)
    pos = [r for r in raw if float(r["label"]) == 1.0]
    neg = [r for r in raw if float(r["label"]) == 0.0]
    random.shuffle(pos)
    random.shuffle(neg)
    pos_split = int(len(pos) * 0.9)
    neg_split = int(len(neg) * 0.9)
    train_raw = pos[:pos_split] + neg[:neg_split]
    eval_raw = pos[pos_split:] + neg[neg_split:]
    random.shuffle(train_raw)
    random.shuffle(eval_raw)

    n_pos_eval = sum(1 for r in eval_raw if float(r["label"]) == 1.0)
    n_neg_eval = sum(1 for r in eval_raw if float(r["label"]) == 0.0)
    print(f"  Train: {len(train_raw)} ({len(train_raw) - (len(neg) - neg_split)}+ / {len(neg) - neg_split}-)")
    print(f"  Eval:  {len(eval_raw)} ({n_pos_eval}+ / {n_neg_eval}-) [stratified]")

    train_dataset = Dataset.from_dict({
        "sentence1": [r["sentence1"] for r in train_raw],
        "sentence2": [r["sentence2"] for r in train_raw],
        "label": [float(r["label"]) for r in train_raw],
    })
    eval_dataset = Dataset.from_dict({
        "sentence1": [r["sentence1"] for r in eval_raw],
        "sentence2": [r["sentence2"] for r in eval_raw],
        "label": [float(r["label"]) for r in eval_raw],
    })

    evaluator = CEBinaryClassificationEvaluator(
        sentence_pairs=[(r["sentence1"], r["sentence2"]) for r in eval_raw],
        labels=[int(r["label"]) for r in eval_raw],
        name="val",
    )

    output_dir = f"/output/{run_name}"

    print(f"Training config:")
    print(f"  Model: {base_model}")
    print(f"  Epochs: {epochs}")
    print(f"  Batch size: {batch_size}")
    print(f"  LR: {lr}")

    args = CrossEncoderTrainingArguments(
        output_dir=output_dir,
        num_train_epochs=epochs,
        per_device_train_batch_size=batch_size,
        per_device_eval_batch_size=batch_size,
        learning_rate=lr,
        warmup_ratio=warmup_ratio,
        eval_strategy="epoch",
        save_strategy="epoch",
        save_total_limit=2,
        load_best_model_at_end=True,
        metric_for_best_model="val_average_precision",
        logging_steps=5,
        bf16=True,
        seed=42,
    )

    trainer = CrossEncoderTrainer(
        model=model,
        args=args,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        evaluator=evaluator,
    )

    trainer.train()

    eval_result = evaluator(model, output_path=output_dir)
    print(f"\nTraining complete!")
    if isinstance(eval_result, dict):
        for k, v in sorted(eval_result.items()):
            print(f"  {k}: {v}")
    else:
        print(f"  Final eval score: {eval_result:.4f}")

    model.save_pretrained(output_dir)
    print(f"  Model saved to: {output_dir}")

    vol.commit()
    print(f"\nDownload with:")
    print(f"  modal volume get cross-encoder-finetune-output {run_name}/ ./models/cross_encoder/{run_name}/")

    return {
        "model": base_model,
        "eval_result": eval_result,
        "train_examples": len(train_raw),
        "eval_examples": len(eval_raw),
        "epochs": epochs,
        "output_dir": output_dir,
    }


@app.local_entrypoint()
def main(
    base_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
    epochs: int = 10,
    batch_size: int = 16,
    lr: float = 2e-5,
    run_name: str = "ce_minilm_run1",
    pairs_path: str = "evidence/fine_tuning/embedding/pairs.jsonl",
):
    from pathlib import Path

    data_path = Path(pairs_path)
    if not data_path.exists():
        raise FileNotFoundError(f"Data not found: {data_path}")

    data_jsonl = data_path.read_text()
    n = len([l for l in data_jsonl.strip().split("\n") if l.strip()])

    print(f"Uploading {n} pairs from {data_path}")
    print(f"Config: model={base_model}, epochs={epochs}, batch_size={batch_size}, lr={lr}")

    result = train.remote(
        data_jsonl=data_jsonl,
        base_model=base_model,
        epochs=epochs,
        batch_size=batch_size,
        lr=lr,
        run_name=run_name,
    )

    print(f"\n=== Results ===")
    for k, v in result.items():
        print(f"  {k}: {v}")
