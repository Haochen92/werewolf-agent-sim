"""Fine-tune cross-encoder for retrieval reranking on Modal.

Trains a cross-encoder that scores (situation_query, memory_text) → relevance.
Used to replace the LLM reranking call in the retrieval pipeline.

Training data: reranker_pairs.jsonl from prep_reranker_data.py
Labels: 0.0 (irrelevant), 0.5 (partial), 1.0 (relevant)

Usage:
    poetry run modal run evidence/fine_tuning/cross_encoder/train_reranker_modal.py \
        --run-name reranker_v1

    poetry run modal run evidence/fine_tuning/cross_encoder/train_reranker_modal.py \
        --base-model BAAI/bge-reranker-base --run-name reranker_bge_v1
"""
from __future__ import annotations

import json
import modal

MINUTES = 60

app = modal.App("cross-encoder-reranker")

image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install(
        "sentence-transformers>=3.0",
        "datasets>=3.0",
        "accelerate>=1.1.0",
        "huggingface_hub",
    )
)

vol = modal.Volume.from_name("cross-encoder-reranker-output", create_if_missing=True)


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
    epochs: int = 20,
    batch_size: int = 16,
    lr: float = 2e-5,
    warmup_ratio: float = 0.1,
    eval_cases: str = "",
    run_name: str = "reranker_v1",
):
    from sentence_transformers.cross_encoder import CrossEncoder
    from sentence_transformers.cross_encoder.trainer import CrossEncoderTrainer
    from sentence_transformers.cross_encoder.training_args import CrossEncoderTrainingArguments
    from datasets import Dataset
    import os
    import random
    import numpy as np

    os.environ["WANDB_DISABLED"] = "true"

    print(f"Loading base model: {base_model}")
    model = CrossEncoder(base_model)

    raw = [json.loads(line) for line in data_jsonl.strip().split("\n") if line.strip()]
    print(f"Loaded {len(raw)} pairs")

    held_out = set(int(c) for c in eval_cases.split(",") if c.strip()) if eval_cases else set()

    if held_out:
        train_raw = [r for r in raw if r["case_index"] not in held_out]
        eval_raw = [r for r in raw if r["case_index"] in held_out]
        print(f"  Hold-out eval cases: {sorted(held_out)}")
    else:
        random.seed(42)
        random.shuffle(raw)
        split = int(len(raw) * 0.85)
        train_raw = raw[:split]
        eval_raw = raw[split:]

    print(f"  Train: {len(train_raw)}")
    print(f"  Eval:  {len(eval_raw)}")

    train_labels = [r["label"] for r in train_raw]
    eval_labels = [r["label"] for r in eval_raw]
    for lbl in [0.0, 0.5, 1.0]:
        tc = sum(1 for l in train_labels if l == lbl)
        ec = sum(1 for l in eval_labels if l == lbl)
        print(f"    label={lbl}: train={tc}, eval={ec}")

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

    output_dir = f"/output/{run_name}"

    print(f"\nTraining config:")
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
        metric_for_best_model="eval_loss",
        logging_steps=5,
        bf16=True,
        seed=42,
    )

    trainer = CrossEncoderTrainer(
        model=model,
        args=args,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
    )

    trainer.train()

    # Evaluate: score all eval pairs and compute ranking metrics
    eval_pairs = [(r["sentence1"], r["sentence2"]) for r in eval_raw]
    preds = model.predict(eval_pairs)

    # Per-case NDCG
    from collections import defaultdict
    import math

    def ndcg_at_k(rels, k):
        def dcg(r, k):
            return sum(r[i] / math.log2(i + 2) for i in range(min(k, len(r))))
        actual = dcg(rels, k)
        ideal = dcg(sorted(rels, reverse=True), k)
        return actual / ideal if ideal > 0 else 1.0

    case_preds = defaultdict(list)
    for r, pred in zip(eval_raw, preds):
        case_preds[r["case_index"]].append({
            "label": r["label"],
            "pred": float(pred),
        })

    ndcg5s = []
    for case_idx in sorted(case_preds):
        items = case_preds[case_idx]
        items.sort(key=lambda x: x["pred"], reverse=True)
        # Map 0.0/0.5/1.0 back to 0/1/2 for NDCG
        rels = [int(it["label"] * 2) for it in items]
        n5 = ndcg_at_k(rels, 5)
        ndcg5s.append(n5)
        print(f"  Case {case_idx}: NDCG@5={n5:.3f} (n={len(items)})")

    mean_ndcg5 = np.mean(ndcg5s) if ndcg5s else 0.0
    print(f"\n  Mean NDCG@5: {mean_ndcg5:.3f}")

    # MSE and correlation
    true_labels = np.array([r["label"] for r in eval_raw])
    pred_scores = np.array(preds)
    mse = np.mean((true_labels - pred_scores) ** 2)
    corr = np.corrcoef(true_labels, pred_scores)[0, 1]
    print(f"  MSE: {mse:.4f}")
    print(f"  Pearson r: {corr:.4f}")

    model.save_pretrained(output_dir)
    print(f"\nModel saved to: {output_dir}")

    vol.commit()
    print(f"\nDownload with:")
    print(f"  modal volume get cross-encoder-reranker-output {run_name}/ ./local_reranker/")

    return {
        "model": base_model,
        "mean_ndcg5": float(mean_ndcg5),
        "mse": float(mse),
        "pearson_r": float(corr),
        "train_examples": len(train_raw),
        "eval_examples": len(eval_raw),
        "epochs": epochs,
        "output_dir": output_dir,
    }


@app.local_entrypoint()
def main(
    base_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
    epochs: int = 20,
    batch_size: int = 16,
    lr: float = 2e-5,
    run_name: str = "reranker_v1",
    eval_cases: str = "",
    pairs_path: str = "evidence/fine_tuning/cross_encoder/reranker_pairs.jsonl",
):
    from pathlib import Path

    data_path = Path(pairs_path)
    if not data_path.exists():
        raise FileNotFoundError(f"Data not found: {data_path}")

    data_jsonl = data_path.read_text()
    n = len([l for l in data_jsonl.strip().split("\n") if l.strip()])

    print(f"Uploading {n} pairs from {data_path}")
    print(f"Config: model={base_model}, epochs={epochs}, batch_size={batch_size}, lr={lr}")
    if eval_cases:
        print(f"Hold-out eval cases: {eval_cases}")

    result = train.remote(
        data_jsonl=data_jsonl,
        base_model=base_model,
        epochs=epochs,
        batch_size=batch_size,
        lr=lr,
        eval_cases=eval_cases,
        run_name=run_name,
    )

    print(f"\n=== Results ===")
    for k, v in result.items():
        print(f"  {k}: {v}")
