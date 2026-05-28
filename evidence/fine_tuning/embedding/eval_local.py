"""Evaluate fine-tuned embedding model against base model.

Compares cosine accuracy on the held-out eval triplets and similarity
distributions on the golden dedup cases.

Usage:
    poetry run python evidence/fine_tuning/embedding/eval_local.py \
        --model evidence/fine_tuning/embedding/gte_base_run4 \
        --base Alibaba-NLP/gte-modernbert-base
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

os.environ.setdefault("OMP_NUM_THREADS", "4")
os.environ.setdefault("MKL_NUM_THREADS", "4")

import numpy as np
from sentence_transformers import SentenceTransformer

DEFAULT_BATCH_SIZE = 256


def load_triplets(path: str) -> list[dict]:
    with open(path) as f:
        return [json.loads(line) for line in f if line.strip()]


def triplet_accuracy(model: SentenceTransformer, triplets: list[dict], batch_size: int) -> dict:
    anchors = [t["anchor"] for t in triplets]
    positives = [t["positive"] for t in triplets]
    negatives = [t["negative"] for t in triplets]

    print(f"    Encoding {len(anchors)} anchors...")
    a_emb = model.encode(anchors, normalize_embeddings=True, batch_size=batch_size, show_progress_bar=True)
    print(f"    Encoding {len(positives)} positives...")
    p_emb = model.encode(positives, normalize_embeddings=True, batch_size=batch_size, show_progress_bar=True)
    print(f"    Encoding {len(negatives)} negatives...")
    n_emb = model.encode(negatives, normalize_embeddings=True, batch_size=batch_size, show_progress_bar=True)

    pos_sims = np.sum(a_emb * p_emb, axis=1)
    neg_sims = np.sum(a_emb * n_emb, axis=1)

    correct = pos_sims > neg_sims
    margins = pos_sims - neg_sims

    return {
        "accuracy": float(correct.mean()),
        "mean_pos_sim": float(pos_sims.mean()),
        "mean_neg_sim": float(neg_sims.mean()),
        "mean_margin": float(margins.mean()),
        "min_margin": float(margins.min()),
        "correct": int(correct.sum()),
        "total": len(triplets),
    }


def golden_case_sims(model: SentenceTransformer, dataset_path: str, golden_path: str, batch_size: int) -> dict:
    """Compute situation similarity for golden-labeled cases."""
    import sys
    sys.path.insert(0, str(Path.cwd()))
    from evaluation.data.datasets import read_dedup_dataset

    records = read_dedup_dataset(Path(dataset_path))

    with open(golden_path) as f:
        golden = json.load(f)
    golden_map = {g["case_id"]: g["golden_label"] for g in golden["labels"]}

    new_sits = []
    top_sits = []
    labels = []

    for record in records:
        label = golden_map.get(record.case_id)
        if not label or label not in ("D", "K"):
            continue
        case = record.dedup_case
        new_sit = case.new_entry.get("situation", "")
        if not new_sit or not case.candidates:
            continue
        top_sit = case.candidates[0].situation
        if not top_sit:
            continue
        new_sits.append(new_sit)
        top_sits.append(top_sit)
        labels.append(label)

    print(f"    Encoding {len(new_sits)} situation pairs...")
    new_embs = model.encode(new_sits, normalize_embeddings=True, batch_size=batch_size, show_progress_bar=True)
    top_embs = model.encode(top_sits, normalize_embeddings=True, batch_size=batch_size, show_progress_bar=True)
    sims = np.sum(new_embs * top_embs, axis=1)

    d_sims = [float(sims[i]) for i in range(len(labels)) if labels[i] == "D"]
    k_sims = [float(sims[i]) for i in range(len(labels)) if labels[i] == "K"]

    return {
        "D_count": len(d_sims),
        "K_count": len(k_sims),
        "D_mean_sim": float(np.mean(d_sims)) if d_sims else 0,
        "K_mean_sim": float(np.mean(k_sims)) if k_sims else 0,
        "D_std": float(np.std(d_sims)) if d_sims else 0,
        "K_std": float(np.std(k_sims)) if k_sims else 0,
        "gap": float(np.mean(d_sims) - np.mean(k_sims)) if d_sims and k_sims else 0,
        "D_min": float(np.min(d_sims)) if d_sims else 0,
        "K_max": float(np.max(k_sims)) if k_sims else 0,
        "overlap": float(np.max(k_sims) - np.min(d_sims)) if d_sims and k_sims else 0,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True, help="Path to fine-tuned model")
    parser.add_argument("--base", default="Alibaba-NLP/gte-modernbert-base")
    parser.add_argument("--triplets", default="evidence/fine_tuning/embedding/triplets.jsonl")
    parser.add_argument("--dataset", default="eval_sets/dedup_v2_sampled.jsonl")
    parser.add_argument("--golden", default="eval_sets/dedup_v2_golden_labels.json")
    parser.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE)
    parser.add_argument("--skip-golden", action="store_true")
    args = parser.parse_args()

    triplets = load_triplets(args.triplets)
    split = int(len(triplets) * 0.9)
    eval_triplets = triplets[split:]
    print(f"Eval triplets: {len(eval_triplets)} (from {len(triplets)} total)")

    print(f"\n{'='*60}")
    print(f"Loading BASE model: {args.base}")
    base_model = SentenceTransformer(args.base)
    base_results = triplet_accuracy(base_model, eval_triplets, args.batch_size)
    print(f"  Triplet accuracy: {base_results['accuracy']:.4f} ({base_results['correct']}/{base_results['total']})")
    print(f"  Mean pos sim: {base_results['mean_pos_sim']:.4f}")
    print(f"  Mean neg sim: {base_results['mean_neg_sim']:.4f}")
    print(f"  Mean margin:  {base_results['mean_margin']:.4f}")

    print(f"\n{'='*60}")
    print(f"Loading FINE-TUNED model: {args.model}")
    ft_model = SentenceTransformer(args.model)
    ft_results = triplet_accuracy(ft_model, eval_triplets, args.batch_size)
    print(f"  Triplet accuracy: {ft_results['accuracy']:.4f} ({ft_results['correct']}/{ft_results['total']})")
    print(f"  Mean pos sim: {ft_results['mean_pos_sim']:.4f}")
    print(f"  Mean neg sim: {ft_results['mean_neg_sim']:.4f}")
    print(f"  Mean margin:  {ft_results['mean_margin']:.4f}")

    print(f"\n{'='*60}")
    print("COMPARISON")
    delta = ft_results['accuracy'] - base_results['accuracy']
    print(f"  Accuracy: {base_results['accuracy']:.4f} → {ft_results['accuracy']:.4f} ({delta:+.4f})")
    print(f"  Margin:   {base_results['mean_margin']:.4f} → {ft_results['mean_margin']:.4f}")

    if not args.skip_golden and Path(args.dataset).exists() and Path(args.golden).exists():
        print(f"\n{'='*60}")
        print("GOLDEN SET SIMILARITY DISTRIBUTIONS")

        print(f"\n  Base model ({args.base}):")
        base_golden = golden_case_sims(base_model, args.dataset, args.golden, args.batch_size)
        print(f"    D (duplicates):  mean={base_golden['D_mean_sim']:.4f} ± {base_golden['D_std']:.4f} (n={base_golden['D_count']})")
        print(f"    K (keep):        mean={base_golden['K_mean_sim']:.4f} ± {base_golden['K_std']:.4f} (n={base_golden['K_count']})")
        print(f"    Gap (D-K):       {base_golden['gap']:.4f}")
        print(f"    Overlap (K_max - D_min): {base_golden['overlap']:.4f}")

        print(f"\n  Fine-tuned model ({args.model}):")
        ft_golden = golden_case_sims(ft_model, args.dataset, args.golden, args.batch_size)
        print(f"    D (duplicates):  mean={ft_golden['D_mean_sim']:.4f} ± {ft_golden['D_std']:.4f} (n={ft_golden['D_count']})")
        print(f"    K (keep):        mean={ft_golden['K_mean_sim']:.4f} ± {ft_golden['K_std']:.4f} (n={ft_golden['K_count']})")
        print(f"    Gap (D-K):       {ft_golden['gap']:.4f}")
        print(f"    Overlap (K_max - D_min): {ft_golden['overlap']:.4f}")

        print(f"\n  Delta:")
        print(f"    Gap:     {base_golden['gap']:.4f} → {ft_golden['gap']:.4f} ({ft_golden['gap'] - base_golden['gap']:+.4f})")
        print(f"    Overlap: {base_golden['overlap']:.4f} → {ft_golden['overlap']:.4f} ({ft_golden['overlap'] - base_golden['overlap']:+.4f})")


if __name__ == "__main__":
    main()
