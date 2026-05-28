"""Build training pairs for embedding fine-tuning from dedup labels.

Converts the 863 labeled dedup cases into (anchor, positive, negative) triplets
for contrastive learning with sentence-transformers.

Anchor: new_entry.situation
Positive: candidate situation from a DISCARD case (true duplicate)
Negative: candidate situation from a KEEP case (hard negative)

Supports two negative mining strategies:
  --mode random   : random negative from KEEP pool (original, weak)
  --mode hard     : closest KEEP case by embedding similarity (recommended)

Usage:
    poetry run python evidence/fine_tuning/embedding/build_pairs.py --mode hard
"""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

import numpy as np

DEDUP_DIR = Path(__file__).parent.parent / "dedup_classifier"
OUT_DIR = Path(__file__).parent


def format_entry_text(entry: dict, item_type: str, mode: str = "full") -> str:
    """Format a memory entry text.

    Modes:
      full:  labeled fields (Situation: X\nAction: Y)
      dedup: matches production auto-dedup input exactly
             SP: action only, Obs: space-concatenated situation+approach+outcome
    """
    if mode == "dedup":
        if item_type == "strategy_point":
            return entry.get("action", "")
        else:
            return f"{entry.get('situation', '')} {entry.get('approach', '')} {entry.get('outcome', '')}"
    else:
        if item_type == "strategy_point":
            return f"Situation: {entry.get('situation', '')}\nAction: {entry.get('action', '')}"
        else:
            return (
                f"Situation: {entry.get('situation', '')}\n"
                f"Approach: {entry.get('approach', '')}\n"
                f"Outcome: {entry.get('outcome', '')}"
            )


def load_labeled_cases():
    agreed = [json.loads(l) for l in (DEDUP_DIR / "agreed_labels.jsonl").read_text().splitlines() if l.strip()]
    disagreed = [json.loads(l) for l in (DEDUP_DIR / "disagreed_labels.jsonl").read_text().splitlines() if l.strip()]
    colab = [json.loads(l) for l in (DEDUP_DIR / "colabeling_log.jsonl").read_text().splitlines() if l.strip()]

    all_cases = {a["case_index"]: a for a in agreed}
    all_cases.update({d["case_index"]: d for d in disagreed})

    labels = {r["case_index"]: r["label"] for r in colab}
    for a in agreed:
        if a["case_index"] not in labels and a["agreement"] == "unanimous" and a["label"] == "K":
            labels[a["case_index"]] = "K"

    return all_cases, labels


def find_closest_negative(anchor: str, neg_pool: list[dict], embeddings: dict[str, np.ndarray]) -> str:
    """Find the negative text most similar to anchor by cosine similarity."""
    anchor_emb = embeddings[anchor]
    best_sim = -1.0
    best_text = neg_pool[0]["negative"]

    for neg in neg_pool:
        neg_text = neg["negative"]
        if neg_text == anchor:
            continue
        neg_emb = embeddings[neg_text]
        sim = float(np.dot(anchor_emb, neg_emb) / (np.linalg.norm(anchor_emb) * np.linalg.norm(neg_emb) + 1e-8))
        if sim > best_sim:
            best_sim = sim
            best_text = neg_text

    return best_text


def find_closest_positive(anchor: str, pos_pool: list[dict], embeddings: dict[str, np.ndarray]) -> str:
    """Find the positive text most similar to anchor by cosine similarity."""
    anchor_emb = embeddings[anchor]
    best_sim = -1.0
    best_text = pos_pool[0]["positive"]

    for pos in pos_pool:
        pos_text = pos["positive"]
        if pos_text == anchor:
            continue
        pos_emb = embeddings[pos_text]
        sim = float(np.dot(anchor_emb, pos_emb) / (np.linalg.norm(anchor_emb) * np.linalg.norm(pos_emb) + 1e-8))
        if sim > best_sim:
            best_sim = sim
            best_text = pos_text

    return best_text


def compute_embeddings(texts: list[str], model_name: str) -> dict[str, np.ndarray]:
    """Compute embeddings for all unique texts using the base model."""
    from sentence_transformers import SentenceTransformer

    unique_texts = list(set(texts))
    print(f"  Computing embeddings for {len(unique_texts)} unique texts with {model_name}...")
    model = SentenceTransformer(model_name)
    embs = model.encode(unique_texts, normalize_embeddings=True, batch_size=256, show_progress_bar=True)
    return {text: emb for text, emb in zip(unique_texts, embs)}


def build_pairs(mode: str = "random", model_name: str = "Alibaba-NLP/gte-modernbert-base",
                 text_mode: str = "situation"):
    all_cases, labels = load_labeled_cases()

    positives = []
    negatives = []

    for idx, label in labels.items():
        case = all_cases.get(idx)
        if not case:
            continue

        item_type = case["item_type"]
        if text_mode in ("full", "dedup"):
            anchor = format_entry_text(case["new_entry"], item_type, mode=text_mode)
            candidate_text = format_entry_text(case["candidates"][0], item_type, mode=text_mode)
        else:
            anchor = case["new_entry"]["situation"]
            candidate_text = case["candidates"][0]["situation"]

        if label == "D":
            positives.append({
                "anchor": anchor,
                "positive": candidate_text,
                "case_index": idx,
                "item_type": item_type,
                "similarity": case["candidates"][0]["similarity"],
            })
        else:
            negatives.append({
                "anchor": anchor,
                "negative": candidate_text,
                "case_index": idx,
                "item_type": item_type,
                "similarity": case["candidates"][0]["similarity"],
            })

    random.seed(42)

    embeddings = {}
    if mode == "hard":
        all_texts = (
            [p["anchor"] for p in positives]
            + [p["positive"] for p in positives]
            + [n["anchor"] for n in negatives]
            + [n["negative"] for n in negatives]
        )
        embeddings = compute_embeddings(all_texts, model_name)

    triplets = []

    for pos in positives:
        if mode == "hard":
            neg_text = find_closest_negative(pos["anchor"], negatives, embeddings)
        else:
            neg_text = random.choice([n["negative"] for n in negatives])
        triplets.append({
            "anchor": pos["anchor"],
            "positive": pos["positive"],
            "negative": neg_text,
            "case_index": pos["case_index"],
            "item_type": pos["item_type"],
        })

    for neg in negatives:
        if mode == "hard":
            pos_text = find_closest_positive(neg["anchor"], positives, embeddings)
        else:
            pos_text = random.choice([p["positive"] for p in positives])
        triplets.append({
            "anchor": neg["anchor"],
            "positive": pos_text,
            "negative": neg["negative"],
            "case_index": neg["case_index"],
            "item_type": neg["item_type"],
        })

    random.shuffle(triplets)

    text_suffix = f"_{text_mode}" if text_mode != "situation" else ""
    mode_suffix = f"_{mode}" if mode != "random" else ""
    out_path = OUT_DIR / f"triplets{mode_suffix}{text_suffix}.jsonl"
    with open(out_path, "w") as f:
        for t in triplets:
            f.write(json.dumps(t) + "\n")

    print(f"Built {len(triplets)} triplets ({mode} negatives, {text_mode} text) → {out_path}")
    print(f"  From {len(positives)} D cases (positive pairs)")
    print(f"  From {len(negatives)} K cases (hard negatives)")

    pairs = []
    for pos in positives:
        pairs.append({
            "sentence1": pos["anchor"],
            "sentence2": pos["positive"],
            "label": 1.0,
        })
    for neg in negatives:
        pairs.append({
            "sentence1": neg["anchor"],
            "sentence2": neg["negative"],
            "label": 0.0,
        })
    random.shuffle(pairs)

    pairs_path = OUT_DIR / f"pairs{text_suffix}.jsonl"
    with open(pairs_path, "w") as f:
        for p in pairs:
            f.write(json.dumps(p) + "\n")
    print(f"Built {len(pairs)} pairs → {pairs_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["random", "hard"], default="hard")
    parser.add_argument("--text", choices=["situation", "full", "dedup"], default="situation",
                        help="Text mode: 'situation' (situation only), 'full' (labeled fields), 'dedup' (matches production auto-dedup)")
    parser.add_argument("--model", default="Alibaba-NLP/gte-modernbert-base",
                        help="Model for computing embeddings in hard mode")
    args = parser.parse_args()
    build_pairs(mode=args.mode, model_name=args.model, text_mode=args.text)
