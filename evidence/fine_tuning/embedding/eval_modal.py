"""Evaluate fine-tuned embedding model on Modal GPU.

Compares base vs fine-tuned model on triplet accuracy and golden
set similarity distributions.

Usage:
    poetry run modal run evidence/fine_tuning/embedding/eval_modal.py
    poetry run modal run evidence/fine_tuning/embedding/eval_modal.py \
        --run-name gte_base_run4 --base Alibaba-NLP/gte-modernbert-base
"""

from __future__ import annotations

import json
import modal

MINUTES = 60

app = modal.App("embedding-eval")

image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install(
        "sentence-transformers>=3.0",
        "accelerate>=1.1.0",
        "numpy",
    )
)

vol = modal.Volume.from_name("embedding-finetune-output")


@app.function(
    image=image,
    gpu="T4",
    timeout=10 * MINUTES,
    secrets=[modal.Secret.from_name("huggingface")],
    volumes={"/output": vol},
)
def run_eval(
    triplets_jsonl: str,
    golden_cases_json: str,
    base_model_name: str = "Alibaba-NLP/gte-modernbert-base",
    run_name: str = "gte_base_run4",
) -> str:
    from sentence_transformers import SentenceTransformer
    import numpy as np
    import os

    triplets = [json.loads(line) for line in triplets_jsonl.strip().split("\n") if line.strip()]
    split = int(len(triplets) * 0.9)
    eval_triplets = triplets[split:]
    print(f"Eval triplets: {len(eval_triplets)}")

    def triplet_accuracy(model, trips):
        anchors = [t["anchor"] for t in trips]
        positives = [t["positive"] for t in trips]
        negatives = [t["negative"] for t in trips]

        a_emb = model.encode(anchors, normalize_embeddings=True, batch_size=256)
        p_emb = model.encode(positives, normalize_embeddings=True, batch_size=256)
        n_emb = model.encode(negatives, normalize_embeddings=True, batch_size=256)

        pos_sims = np.sum(a_emb * p_emb, axis=1)
        neg_sims = np.sum(a_emb * n_emb, axis=1)
        correct = pos_sims > neg_sims
        margins = pos_sims - neg_sims

        return {
            "accuracy": float(correct.mean()),
            "mean_pos_sim": float(pos_sims.mean()),
            "mean_neg_sim": float(neg_sims.mean()),
            "mean_margin": float(margins.mean()),
            "correct": int(correct.sum()),
            "total": len(trips),
        }

    def golden_sims(model, cases):
        new_sits = [c["new_sit"] for c in cases]
        top_sits = [c["top_sit"] for c in cases]
        labels = [c["label"] for c in cases]

        new_embs = model.encode(new_sits, normalize_embeddings=True, batch_size=256)
        top_embs = model.encode(top_sits, normalize_embeddings=True, batch_size=256)
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

    golden_cases = json.loads(golden_cases_json) if golden_cases_json else []

    # Base model
    print(f"\nLoading BASE model: {base_model_name}")
    base_model = SentenceTransformer(base_model_name)
    print(f"  Embedding dim: {base_model.get_embedding_dimension()}")
    base_triplet = triplet_accuracy(base_model, eval_triplets)
    print(f"  Triplet accuracy: {base_triplet['accuracy']:.4f} ({base_triplet['correct']}/{base_triplet['total']})")
    base_golden = golden_sims(base_model, golden_cases) if golden_cases else {}
    del base_model

    # Fine-tuned model
    ft_path = f"/output/{run_name}"
    if not os.path.exists(ft_path):
        available = os.listdir("/output")
        raise FileNotFoundError(f"Model not found at {ft_path}. Available: {available}")

    print(f"\nLoading FINE-TUNED model: {ft_path}")
    ft_model = SentenceTransformer(ft_path)
    print(f"  Embedding dim: {ft_model.get_embedding_dimension()}")
    ft_triplet = triplet_accuracy(ft_model, eval_triplets)
    print(f"  Triplet accuracy: {ft_triplet['accuracy']:.4f} ({ft_triplet['correct']}/{ft_triplet['total']})")
    ft_golden = golden_sims(ft_model, golden_cases) if golden_cases else {}
    del ft_model

    results = {
        "base_model": base_model_name,
        "fine_tuned": run_name,
        "base_triplet": base_triplet,
        "ft_triplet": ft_triplet,
        "base_golden": base_golden,
        "ft_golden": ft_golden,
    }
    return json.dumps(results)


@app.local_entrypoint()
def main(
    run_name: str = "gte_base_run4",
    base: str = "Alibaba-NLP/gte-modernbert-base",
    triplets_path: str = "evidence/fine_tuning/embedding/triplets.jsonl",
    dataset_path: str = "eval_sets/dedup_v2_sampled.jsonl",
    golden_path: str = "eval_sets/dedup_v2_golden_labels.json",
):
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path.cwd()))

    # Load triplets
    triplets_jsonl = Path(triplets_path).read_text()
    n = len([l for l in triplets_jsonl.strip().split("\n") if l.strip()])
    print(f"Loaded {n} triplets from {triplets_path}")

    # Prepare golden cases (extract situation pairs locally to avoid
    # sending the full eval infrastructure to Modal)
    golden_cases_json = ""
    if Path(dataset_path).exists() and Path(golden_path).exists():
        from evaluation.data.datasets import read_dedup_dataset

        records = read_dedup_dataset(Path(dataset_path))
        with open(golden_path) as f:
            golden = json.load(f)
        golden_map = {g["case_id"]: g["golden_label"] for g in golden["labels"]}

        cases = []
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
            cases.append({"new_sit": new_sit, "top_sit": top_sit, "label": label})

        golden_cases_json = json.dumps(cases)
        print(f"Prepared {len(cases)} golden cases")
    else:
        print("Skipping golden set (files not found)")

    print(f"\nSending to Modal for GPU evaluation...")
    results_json = run_eval.remote(
        triplets_jsonl=triplets_jsonl,
        golden_cases_json=golden_cases_json,
        base_model_name=base,
        run_name=run_name,
    )

    results = json.loads(results_json)

    print(f"\n{'='*60}")
    print("TRIPLET ACCURACY")
    bt = results["base_triplet"]
    ft = results["ft_triplet"]
    print(f"  Base:       {bt['accuracy']:.4f} ({bt['correct']}/{bt['total']})")
    print(f"  Fine-tuned: {ft['accuracy']:.4f} ({ft['correct']}/{ft['total']})")
    delta = ft['accuracy'] - bt['accuracy']
    print(f"  Delta:      {delta:+.4f}")
    print(f"  Margin:     {bt['mean_margin']:.4f} → {ft['mean_margin']:.4f}")

    if results.get("base_golden") and results.get("ft_golden"):
        bg = results["base_golden"]
        fg = results["ft_golden"]
        print(f"\n{'='*60}")
        print("GOLDEN SET SIMILARITY DISTRIBUTIONS")
        print(f"\n  Base model:")
        print(f"    D (duplicates):  mean={bg['D_mean_sim']:.4f} ± {bg['D_std']:.4f} (n={bg['D_count']})")
        print(f"    K (keep):        mean={bg['K_mean_sim']:.4f} ± {bg['K_std']:.4f} (n={bg['K_count']})")
        print(f"    Gap (D-K):       {bg['gap']:.4f}")
        print(f"    Overlap (K_max - D_min): {bg['overlap']:.4f}")
        print(f"\n  Fine-tuned model:")
        print(f"    D (duplicates):  mean={fg['D_mean_sim']:.4f} ± {fg['D_std']:.4f} (n={fg['D_count']})")
        print(f"    K (keep):        mean={fg['K_mean_sim']:.4f} ± {fg['K_std']:.4f} (n={fg['K_count']})")
        print(f"    Gap (D-K):       {fg['gap']:.4f}")
        print(f"    Overlap (K_max - D_min): {fg['overlap']:.4f}")
        print(f"\n  Delta:")
        print(f"    Gap:     {bg['gap']:.4f} → {fg['gap']:.4f} ({fg['gap'] - bg['gap']:+.4f})")
        print(f"    Overlap: {bg['overlap']:.4f} → {fg['overlap']:.4f} ({fg['overlap'] - bg['overlap']:+.4f})")
