"""Evaluate reranker cross-encoder on golden retrieval labels via Modal GPU.

Scores pairs with the cross-encoder and compares reranking quality (NDCG@k)
against bi-encoder cosine similarity baseline. Defaults to test split only.

Usage:
    poetry run modal run evidence/fine_tuning/cross_encoder/reranker/scripts/eval_reranker_modal.py \
        --run-name reranker_v3

    # Evaluate on validation set
    poetry run modal run evidence/fine_tuning/cross_encoder/reranker/scripts/eval_reranker_modal.py \
        --run-name reranker_v3 --split val

    # Also evaluate base (pre-trained) model for comparison
    poetry run modal run evidence/fine_tuning/cross_encoder/reranker/scripts/eval_reranker_modal.py \
        --run-name reranker_v3 --include-base
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
            return sum((2 ** r[i] - 1) / math.log2(i + 2) for i in range(min(k, len(r))))
        actual = dcg(rels, k)
        ideal = dcg(sorted(rels, reverse=True), k)
        return actual / ideal if ideal > 0 else 1.0

    def bootstrap_ci(values, n_boot=10000, ci=0.95):
        rng = np.random.RandomState(42)
        arr = np.array(values)
        means = np.array([arr[rng.randint(0, len(arr), len(arr))].mean() for _ in range(n_boot)])
        lo = np.percentile(means, (1 - ci) / 2 * 100)
        hi = np.percentile(means, (1 + ci) / 2 * 100)
        return float(lo), float(hi)

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

        for case_idx in sorted(case_items):
            items = case_items[case_idx]
            items.sort(key=lambda x: x["score"], reverse=True)
            label_to_rel = {0.0: 0, 0.25: 1, 1.0: 2}
            rels = [label_to_rel.get(it["label"], round(it["label"] * 2)) for it in items]
            n3 = ndcg_at_k(rels, 3)
            n5 = ndcg_at_k(rels, 5)
            n10 = ndcg_at_k(rels, 10)
            ndcg3s.append(n3)
            ndcg5s.append(n5)
            ndcg10s.append(n10)

            print(f"  Case {case_idx:2d}: NDCG@3={n3:.3f}  @5={n5:.3f}  @10={n10:.3f}")

        ci3 = bootstrap_ci(ndcg3s)
        ci5 = bootstrap_ci(ndcg5s)
        ci10 = bootstrap_ci(ndcg10s)
        print(f"\n  Mean NDCG@3:  {np.mean(ndcg3s):.3f}  95% CI [{ci3[0]:.3f}, {ci3[1]:.3f}]")
        print(f"  Mean NDCG@5:  {np.mean(ndcg5s):.3f}  95% CI [{ci5[0]:.3f}, {ci5[1]:.3f}]")
        print(f"  Mean NDCG@10: {np.mean(ndcg10s):.3f}  95% CI [{ci10[0]:.3f}, {ci10[1]:.3f}]")

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
            "ndcg5_ci95": ci5,
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
    split: str = "test",
):
    from pathlib import Path

    base_dir = Path("evidence/fine_tuning/cross_encoder/reranker/training_data")

    if split == "all":
        print("WARNING: Evaluating on ALL data including training set — "
              "metrics are NOT comparable to held-out evaluation")
        parts = []
        for name in ["train", "val", "test"]:
            p = base_dir / f"reranker_{name}.jsonl"
            if p.exists():
                parts.append(p.read_text().strip())
        pairs_jsonl = "\n".join(parts)
    else:
        data_path = base_dir / f"reranker_{split}.jsonl"
        if not data_path.exists():
            raise FileNotFoundError(
                f"Data not found: {data_path}. Run prep_reranker_data.py first."
            )
        pairs_jsonl = data_path.read_text()

    n = len([l for l in pairs_jsonl.strip().split("\n") if l.strip()])
    print(f"Evaluating {n} pairs (split={split})")

    results = evaluate.remote(
        pairs_jsonl=pairs_jsonl,
        run_name=run_name,
        base_model=base_model,
        include_base=include_base,
    )

    print(f"\n=== Final Results (split={split}) ===")
    for name, r in results.items():
        ci = r.get("ndcg5_ci95")
        ci_str = f"  95% CI [{ci[0]:.3f}, {ci[1]:.3f}]" if ci else ""
        print(f"  {name}: NDCG@5={r['ndcg5']:.3f}{ci_str}  r={r['pearson_r']:.3f}")
