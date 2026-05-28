"""Fine-tune embedding model for werewolf memory retrieval on Modal.

Supports two loss modes:
  --loss triplet  : TripletLoss on triplets.jsonl (anchor/positive/negative)
  --loss cosine   : CosineSimilarityLoss on pairs.jsonl (sentence1/sentence2/label)

Usage:
    # CosineSimilarityLoss (recommended):
    modal run evidence/fine_tuning/embedding/train_modal.py \
        --loss cosine --run-name gte_cosine_run1

    # TripletLoss:
    modal run evidence/fine_tuning/embedding/train_modal.py \
        --loss triplet --run-name gte_triplet_run1
"""

from __future__ import annotations

import json
import modal

MINUTES = 60

app = modal.App("embedding-finetune")

image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install(
        "sentence-transformers>=3.0",
        "datasets>=3.0",
        "accelerate>=1.1.0",
        "huggingface_hub",
    )
)

vol = modal.Volume.from_name("embedding-finetune-output", create_if_missing=True)


@app.function(
    image=image,
    gpu="L4",
    timeout=30 * MINUTES,
    secrets=[modal.Secret.from_name("huggingface")],
    volumes={"/output": vol},
)
def train(
    data_jsonl: str,
    loss_type: str = "cosine",
    base_model: str = "Alibaba-NLP/gte-modernbert-base",
    epochs: int = 5,
    batch_size: int = 16,
    lr: float = 2e-5,
    warmup_ratio: float = 0.1,
    run_name: str = "gte_base_run1",
):
    from sentence_transformers import SentenceTransformer, losses
    from sentence_transformers.training_args import SentenceTransformerTrainingArguments
    from sentence_transformers.trainer import SentenceTransformerTrainer
    from sentence_transformers.evaluation import TripletEvaluator, EmbeddingSimilarityEvaluator
    from datasets import Dataset
    import os

    os.environ["WANDB_DISABLED"] = "true"

    print(f"Loading base model: {base_model}")
    model = SentenceTransformer(base_model)
    print(f"  Embedding dim: {model.get_embedding_dimension()}")

    raw = [json.loads(line) for line in data_jsonl.strip().split("\n") if line.strip()]
    print(f"Loaded {len(raw)} examples (loss={loss_type})")

    import random as _rand
    _rand.seed(42)

    if loss_type == "cosine":
        pos = [r for r in raw if float(r["label"]) == 1.0]
        neg = [r for r in raw if float(r["label"]) == 0.0]
        _rand.shuffle(pos)
        _rand.shuffle(neg)
        pos_split = int(len(pos) * 0.9)
        neg_split = int(len(neg) * 0.9)
        train_raw = pos[:pos_split] + neg[:neg_split]
        eval_raw = pos[pos_split:] + neg[neg_split:]
        _rand.shuffle(train_raw)
        _rand.shuffle(eval_raw)
    else:
        split = int(len(raw) * 0.9)
        train_raw = raw[:split]
        eval_raw = raw[split:]

    if loss_type == "cosine":
        n_pos_eval = sum(1 for r in eval_raw if float(r["label"]) == 1.0)
        n_neg_eval = sum(1 for r in eval_raw if float(r["label"]) == 0.0)
        print(f"  Eval split: {n_pos_eval} positive, {n_neg_eval} negative (stratified)")

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
        train_loss = losses.CosineSimilarityLoss(model=model)
        evaluator = EmbeddingSimilarityEvaluator(
            sentences1=[r["sentence1"] for r in eval_raw],
            sentences2=[r["sentence2"] for r in eval_raw],
            scores=[float(r["label"]) for r in eval_raw],
            name="val",
        )
        best_metric = "eval_loss"
    else:
        train_dataset = Dataset.from_dict({
            "anchor": [t["anchor"] for t in train_raw],
            "positive": [t["positive"] for t in train_raw],
            "negative": [t["negative"] for t in train_raw],
        })
        eval_dataset = Dataset.from_dict({
            "anchor": [t["anchor"] for t in eval_raw],
            "positive": [t["positive"] for t in eval_raw],
            "negative": [t["negative"] for t in eval_raw],
        })
        train_loss = losses.TripletLoss(model=model)
        evaluator = TripletEvaluator(
            anchors=[t["anchor"] for t in eval_raw],
            positives=[t["positive"] for t in eval_raw],
            negatives=[t["negative"] for t in eval_raw],
            name="val",
        )
        best_metric = "val_cosine_accuracy"

    output_dir = f"/output/{run_name}"

    print(f"Training config:")
    print(f"  Loss: {loss_type}")
    print(f"  Train examples: {len(train_raw)}")
    print(f"  Eval examples: {len(eval_raw)}")
    print(f"  Batch size: {batch_size}")
    print(f"  Epochs: {epochs}")
    print(f"  LR: {lr}")
    print(f"  Best metric: {best_metric}")

    args = SentenceTransformerTrainingArguments(
        output_dir=output_dir,
        num_train_epochs=epochs,
        per_device_train_batch_size=batch_size,
        per_device_eval_batch_size=batch_size,
        gradient_accumulation_steps=2,
        learning_rate=lr,
        warmup_ratio=warmup_ratio,
        eval_strategy="epoch",
        save_strategy="epoch",
        save_total_limit=2,
        load_best_model_at_end=True,
        metric_for_best_model=best_metric,
        greater_is_better=(best_metric != "eval_loss"),
        logging_steps=5,
        bf16=True,
        seed=42,
    )

    trainer = SentenceTransformerTrainer(
        model=model,
        args=args,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        loss=train_loss,
        evaluator=evaluator,
    )

    trainer.train()

    eval_result = evaluator(model, output_path=output_dir)
    if isinstance(eval_result, dict):
        print(f"\nTraining complete!")
        for k, v in sorted(eval_result.items()):
            print(f"  {k}: {v}")
    else:
        print(f"\nTraining complete!")
        print(f"  Final eval score: {eval_result:.4f}")

    model.save_pretrained(output_dir)
    print(f"  Model saved to: {output_dir}")

    vol.commit()
    print(f"\nDownload with:")
    print(f"  modal volume get embedding-finetune-output {run_name}/ ./local_embedding/")

    return {
        "model": base_model,
        "loss_type": loss_type,
        "eval_result": eval_result,
        "train_examples": len(train_raw),
        "eval_examples": len(eval_raw),
        "epochs": epochs,
        "output_dir": output_dir,
    }


@app.local_entrypoint()
def main(
    base_model: str = "Alibaba-NLP/gte-modernbert-base",
    epochs: int = 5,
    batch_size: int = 16,
    lr: float = 2e-5,
    loss: str = "cosine",
    run_name: str = "gte_base_run1",
    triplets_path: str = "",
):
    from pathlib import Path

    if not triplets_path:
        if loss == "cosine":
            triplets_path = "evidence/fine_tuning/embedding/pairs.jsonl"
        else:
            triplets_path = "evidence/fine_tuning/embedding/triplets.jsonl"

    data_path = Path(triplets_path)
    if not data_path.exists():
        raise FileNotFoundError(f"Data not found: {data_path}")

    data_jsonl = data_path.read_text()
    n = len([l for l in data_jsonl.strip().split("\n") if l.strip()])

    print(f"Uploading {n} examples from {data_path}")
    print(f"Config: model={base_model}, loss={loss}, epochs={epochs}, batch_size={batch_size}, lr={lr}")

    result = train.remote(
        data_jsonl=data_jsonl,
        loss_type=loss,
        base_model=base_model,
        epochs=epochs,
        batch_size=batch_size,
        lr=lr,
        run_name=run_name,
    )

    print(f"\n=== Results ===")
    for k, v in result.items():
        print(f"  {k}: {v}")
