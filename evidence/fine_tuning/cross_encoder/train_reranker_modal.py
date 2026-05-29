"""Fine-tune cross-encoder for retrieval reranking on Modal.

Trains a cross-encoder that scores (situation_query, memory_text) → relevance.
Used to replace the LLM reranking call in the retrieval pipeline.

Training data: reranker_train.jsonl / reranker_val.jsonl from prep_reranker_data.py
(stratified split from reranker_split.json, 24 train / 8 val / 8 test)
Labels: 0.0 (irrelevant), 0.25 (partial), 1.0 (relevant)

Usage:
    poetry run modal run evidence/fine_tuning/cross_encoder/train_reranker_modal.py \
        --run-name reranker_v3

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
    train_jsonl: str,
    eval_jsonl: str,
    split_manifest_json: str | None = None,
    base_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
    epochs: int = 20,
    batch_size: int = 16,
    lr: float = 2e-5,
    warmup_ratio: float = 0.1,
    run_name: str = "reranker_v1",
):
    from sentence_transformers.cross_encoder import CrossEncoder
    from sentence_transformers.cross_encoder.trainer import CrossEncoderTrainer
    from sentence_transformers.cross_encoder.training_args import CrossEncoderTrainingArguments
    from datasets import Dataset
    import os
    import numpy as np

    os.environ["WANDB_DISABLED"] = "true"

    print(f"Loading base model: {base_model}")
    model = CrossEncoder(base_model)

    train_raw = [json.loads(line) for line in train_jsonl.strip().split("\n") if line.strip()]
    eval_raw = [json.loads(line) for line in eval_jsonl.strip().split("\n") if line.strip()]

    if split_manifest_json:
        manifest = json.loads(split_manifest_json)
        train_cases = set(p["case_index"] for p in train_raw)
        eval_cases = set(p["case_index"] for p in eval_raw)
        expected_train = set(manifest["train"])
        expected_val = set(manifest["val"])
        if train_cases != expected_train:
            print(f"WARNING: train data cases {sorted(train_cases)} don't match "
                  f"manifest train {sorted(expected_train)}")
        if eval_cases != expected_val:
            print(f"WARNING: eval data cases {sorted(eval_cases)} don't match "
                  f"manifest val {sorted(expected_val)}")
        overlap = train_cases & eval_cases
        if overlap:
            print(f"ERROR: train/eval overlap on cases {sorted(overlap)}")

    print(f"  Train: {len(train_raw)}")
    print(f"  Eval:  {len(eval_raw)}")
    print(f"  Eval cases: {sorted(set(r['case_index'] for r in eval_raw))}")

    train_labels = [r["label"] for r in train_raw]
    eval_labels = [r["label"] for r in eval_raw]
    for lbl in [0.0, 0.25, 1.0]:
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

    loss_curve = {
        "train_loss": [],
        "eval_loss": [],
        "epochs": [],
    }
    for entry in trainer.state.log_history:
        if "loss" in entry and "epoch" in entry:
            loss_curve["train_loss"].append({
                "step": entry.get("step"), "epoch": entry["epoch"], "loss": entry["loss"],
            })
        if "eval_loss" in entry and "epoch" in entry:
            loss_curve["eval_loss"].append({
                "step": entry.get("step"), "epoch": entry["epoch"], "loss": entry["eval_loss"],
            })
            loss_curve["epochs"].append(entry["epoch"])

    curve_path = f"/output/{run_name}_loss_curve.json"
    with open(curve_path, "w") as f:
        json.dump(loss_curve, f, indent=2)
    print(f"Loss curve saved to {curve_path}")

    # Evaluate: score all eval pairs and compute ranking metrics
    eval_pairs = [(r["sentence1"], r["sentence2"]) for r in eval_raw]
    preds = model.predict(eval_pairs)

    # Per-case NDCG
    from collections import defaultdict
    import math

    def ndcg_at_k(rels, k):
        def dcg(r, k):
            return sum((2 ** r[i] - 1) / math.log2(i + 2) for i in range(min(k, len(r))))
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
        # Map training labels back to graded relevance for NDCG
        label_to_rel = {0.0: 0, 0.25: 1, 1.0: 2}
        rels = [label_to_rel.get(it["label"], round(it["label"] * 2)) for it in items]
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
    train_path: str = "evidence/fine_tuning/cross_encoder/reranker_train.jsonl",
    eval_path: str = "evidence/fine_tuning/cross_encoder/reranker_val.jsonl",
):
    from pathlib import Path

    train_data = Path(train_path)
    eval_data = Path(eval_path)
    if not train_data.exists():
        raise FileNotFoundError(f"Train data not found: {train_data}. Run prep_reranker_data.py first.")
    if not eval_data.exists():
        raise FileNotFoundError(f"Eval data not found: {eval_data}. Run prep_reranker_data.py first.")

    split_path = Path("evidence/fine_tuning/cross_encoder/reranker_split.json")
    split_manifest_json = split_path.read_text() if split_path.exists() else None
    if not split_manifest_json:
        print("WARNING: split manifest not found — skipping validation")

    train_jsonl = train_data.read_text()
    eval_jsonl = eval_data.read_text()
    n_train = len([l for l in train_jsonl.strip().split("\n") if l.strip()])
    n_eval = len([l for l in eval_jsonl.strip().split("\n") if l.strip()])

    print(f"Uploading {n_train} train + {n_eval} eval pairs")
    print(f"Config: model={base_model}, epochs={epochs}, batch_size={batch_size}, lr={lr}")

    result = train.remote(
        train_jsonl=train_jsonl,
        eval_jsonl=eval_jsonl,
        split_manifest_json=split_manifest_json,
        base_model=base_model,
        epochs=epochs,
        batch_size=batch_size,
        lr=lr,
        run_name=run_name,
    )

    print(f"\n=== Results ===")
    for k, v in result.items():
        print(f"  {k}: {v}")
