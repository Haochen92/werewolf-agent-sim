"""Build hard-negative triplets using Modal GPU for embedding computation.

Computes cross-case similarity to find the hardest negative for each
anchor, producing higher-quality training triplets.

Usage:
    poetry run modal run evidence/fine_tuning/embedding/build_pairs_modal.py
    poetry run modal run evidence/fine_tuning/embedding/build_pairs_modal.py \
        --model Alibaba-NLP/gte-modernbert-base
"""

from __future__ import annotations

import json
import modal

MINUTES = 60

app = modal.App("embedding-build-pairs")

image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install(
        "sentence-transformers>=3.0",
        "accelerate>=1.1.0",
        "numpy",
    )
)


@app.function(
    image=image,
    gpu="T4",
    timeout=10 * MINUTES,
    secrets=[modal.Secret.from_name("huggingface")],
)
def compute_hard_triplets(
    positives_json: str,
    negatives_json: str,
    model_name: str = "Alibaba-NLP/gte-modernbert-base",
) -> str:
    from sentence_transformers import SentenceTransformer
    import numpy as np

    positives = json.loads(positives_json)
    negatives = json.loads(negatives_json)

    all_texts = list(set(
        [p["anchor"] for p in positives]
        + [p["positive"] for p in positives]
        + [n["anchor"] for n in negatives]
        + [n["negative"] for n in negatives]
    ))
    print(f"Computing embeddings for {len(all_texts)} unique texts with {model_name}...")

    model = SentenceTransformer(model_name)
    embs_array = model.encode(all_texts, normalize_embeddings=True, batch_size=256, show_progress_bar=True)
    embeddings = {text: embs_array[i] for i, text in enumerate(all_texts)}

    neg_texts = [n["negative"] for n in negatives]
    neg_embs = np.array([embeddings[t] for t in neg_texts])

    pos_texts = [p["positive"] for p in positives]
    pos_embs = np.array([embeddings[t] for t in pos_texts])

    triplets = []

    print("Mining hard negatives for D cases...")
    for pos in positives:
        anchor_emb = embeddings[pos["anchor"]]
        sims = neg_embs @ anchor_emb
        best_idx = int(np.argmax(sims))
        triplets.append({
            "anchor": pos["anchor"],
            "positive": pos["positive"],
            "negative": neg_texts[best_idx],
            "case_index": pos["case_index"],
            "item_type": pos["item_type"],
            "neg_sim": float(sims[best_idx]),
        })

    print("Mining hard positives for K cases...")
    for neg in negatives:
        anchor_emb = embeddings[neg["anchor"]]
        sims = pos_embs @ anchor_emb
        best_idx = int(np.argmax(sims))
        triplets.append({
            "anchor": neg["anchor"],
            "positive": pos_texts[best_idx],
            "negative": neg["negative"],
            "case_index": neg["case_index"],
            "item_type": neg["item_type"],
            "pos_sim": float(sims[best_idx]),
        })

    import random
    random.seed(42)
    random.shuffle(triplets)

    neg_sims = [t["neg_sim"] for t in triplets if "neg_sim" in t]
    pos_sims = [t["pos_sim"] for t in triplets if "pos_sim" in t]
    print(f"\nHard negative stats (D cases): mean_sim={np.mean(neg_sims):.4f}, min={np.min(neg_sims):.4f}, max={np.max(neg_sims):.4f}")
    print(f"Hard positive stats (K cases): mean_sim={np.mean(pos_sims):.4f}, min={np.min(pos_sims):.4f}, max={np.max(pos_sims):.4f}")

    return json.dumps(triplets)


@app.local_entrypoint()
def main(
    model: str = "Alibaba-NLP/gte-modernbert-base",
):
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path.cwd()))
    from evidence.fine_tuning.embedding.build_pairs import load_labeled_cases

    all_cases, labels = load_labeled_cases()

    positives = []
    negatives = []

    for idx, label in labels.items():
        case = all_cases.get(idx)
        if not case:
            continue

        anchor = case["new_entry"]["situation"]
        top_candidate_sit = case["candidates"][0]["situation"]

        if label == "D":
            positives.append({
                "anchor": anchor,
                "positive": top_candidate_sit,
                "case_index": idx,
                "item_type": case["item_type"],
                "similarity": case["candidates"][0]["similarity"],
            })
        else:
            negatives.append({
                "anchor": anchor,
                "negative": top_candidate_sit,
                "case_index": idx,
                "item_type": case["item_type"],
                "similarity": case["candidates"][0]["similarity"],
            })

    print(f"Loaded {len(positives)} D cases, {len(negatives)} K cases")
    print(f"Using model: {model}")

    triplets_json = compute_hard_triplets.remote(
        positives_json=json.dumps(positives),
        negatives_json=json.dumps(negatives),
        model_name=model,
    )

    triplets = json.loads(triplets_json)

    out_path = Path("evidence/fine_tuning/embedding/triplets_hard.jsonl")
    with open(out_path, "w") as f:
        for t in triplets:
            f.write(json.dumps(t) + "\n")

    print(f"\nBuilt {len(triplets)} hard-negative triplets → {out_path}")
