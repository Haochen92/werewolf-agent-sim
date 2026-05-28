"""Evaluate reranker cross-encoder on golden retrieval labels via Modal GPU.

Scores all golden set pairs with the cross-encoder and compares reranking
quality (NDCG@k) against bi-encoder cosine similarity baseline.

Usage:
    poetry run modal run evidence/fine_tuning/cross_encoder/eval_reranker_modal.py \
        --run-name reranker_v1

    # Also evaluate base (pre-trained) model for comparison
    poetry run modal run evidence/fine_tuning/cross_encoder/eval_reranker_modal.py \
        --run-name reranker_v1 --include-base
"""
from __future__ import annotations

import json
import modal

MINUTES = 60

app = modal.App("cross-encoder-reranker-eval")

image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install(
        "sentence-transformers>=3.0",
        "numpy",
    )
)

vol = modal.Volume.from_name("cross-encoder-reranker-output")


@app.function(
    image=image,
    gpu="L4",
    timeout=15 * MINUTES,
    volumes={"/output": vol},
)
def evaluate(
    pairs_jsonl: str,
    run_name: str,
    base_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
    include_base: bool = False,
):
    from sentence_transformers.cross_encoder import CrossEncoder
    from collections import defaultdict
    import math
    import numpy as np

    pairs = [json.loads(l) for l in pairs_jsonl.strip().split("\n") if l.strip()]
    print(f"Loaded {len(pairs)} pairs across {len(set(p['case_index'] for p in pairs))} cases")

    sentence_pairs = [(p["sentence1"], p["sentence2"]) for p in pairs]
    true_labels = [p["label"] for p in pairs]

    def ndcg_at_k(rels, k):
        def dcg(r, k):
            return sum(r[i] / math.log2(i + 2) for i in range(min(k, len(r))))
        actual = dcg(rels, k)
        ideal = dcg(sorted(rels, reverse=True), k)
        return actual / ideal if ideal > 0 else 1.0

    def eval_scores(scores, label):
        case_items = defaultdict(list)
        for p, score in zip(pairs, scores):
            case_items[p["case_index"]].append({
                "label": p["label"],
                "score": float(score),
            })

        print(f"\n{'='*60}")
        print(f"  {label}")
        print(f"{'='*60}")

        ndcg3s, ndcg5s, ndcg10s = [], [], []
        by_role = defaultdict(list)

        for case_idx in sorted(case_items):
            items = case_items[case_idx]
            items.sort(key=lambda x: x["score"], reverse=True)
            rels = [int(it["label"] * 2) for it in items]
            n3 = ndcg_at_k(rels, 3)
            n5 = ndcg_at_k(rels, 5)
            n10 = ndcg_at_k(rels, 10)
            ndcg3s.append(n3)
            ndcg5s.append(n5)
            ndcg10s.append(n10)

            role = next(
                (p["case_index"] for p in pairs if p["case_index"] == case_idx),
                "?",
            )
            print(f"  Case {case_idx:2d}: NDCG@3={n3:.3f}  @5={n5:.3f}  @10={n10:.3f}")

        print(f"\n  Mean NDCG@3:  {np.mean(ndcg3s):.3f}")
        print(f"  Mean NDCG@5:  {np.mean(ndcg5s):.3f}")
        print(f"  Mean NDCG@10: {np.mean(ndcg10s):.3f}")

        true_arr = np.array(true_labels)
        pred_arr = np.array(scores)
        mse = np.mean((true_arr - pred_arr) ** 2)
        corr = np.corrcoef(true_arr, pred_arr)[0, 1]
        print(f"  MSE: {mse:.4f}")
        print(f"  Pearson r: {corr:.4f}")

        return {
            "ndcg3": float(np.mean(ndcg3s)),
            "ndcg5": float(np.mean(ndcg5s)),
            "ndcg10": float(np.mean(ndcg10s)),
            "mse": float(mse),
            "pearson_r": float(corr),
        }

    results = {}

    # Fine-tuned model
    model_path = f"/output/{run_name}"
    print(f"\nLoading fine-tuned model from {model_path}")
    finetuned = CrossEncoder(model_path)
    ft_scores = finetuned.predict(sentence_pairs)
    results["finetuned"] = eval_scores(ft_scores, f"Fine-tuned ({run_name})")

    # Base model (pre-trained, no fine-tuning)
    if include_base:
        print(f"\nLoading base model: {base_model}")
        base = CrossEncoder(base_model)
        base_scores = base.predict(sentence_pairs)
        results["base"] = eval_scores(base_scores, f"Base ({base_model})")

    # Summary comparison
    print(f"\n{'='*60}")
    print("  SUMMARY")
    print(f"{'='*60}")
    for name, r in results.items():
        print(f"  {name:15s}: NDCG@5={r['ndcg5']:.3f}  r={r['pearson_r']:.3f}  MSE={r['mse']:.4f}")

    return results


@app.local_entrypoint()
def main(
    run_name: str = "reranker_v1",
    base_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
    include_base: bool = False,
    pairs_path: str = "evidence/fine_tuning/cross_encoder/reranker_pairs.jsonl",
):
    from pathlib import Path

    data_path = Path(pairs_path)
    if not data_path.exists():
        raise FileNotFoundError(f"Data not found: {data_path}")

    pairs_jsonl = data_path.read_text()
    n = len([l for l in pairs_jsonl.strip().split("\n") if l.strip()])
    print(f"Evaluating {n} pairs")

    results = evaluate.remote(
        pairs_jsonl=pairs_jsonl,
        run_name=run_name,
        base_model=base_model,
        include_base=include_base,
    )

    print(f"\n=== Final Results ===")
    for name, r in results.items():
        print(f"  {name}: NDCG@5={r['ndcg5']:.3f}  r={r['pearson_r']:.3f}")
