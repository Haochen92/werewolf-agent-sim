"""Cheap-first gate: does v4's observation ranking degrade under clean labels?

v4 was trained on the over-crediting merged labels. We hold v4's ranking fixed and score
it against two ground truths on its OWN held-out test cases (observations only — the
subset where the labelers saw the same text the reranker scores, so there's no input
mismatch):

    NDCG(v4 ranking | BIASED merged labels)   — what v4 was tuned toward
    NDCG(v4 ranking | CLEAN soft strong labels) — the stricter ChatGPT+Sonnet truth

If CLEAN << BIASED, v4's ranking is tuned to the inflated labels and disagrees with the
strict truth → the bias manifests → relabel could help. If CLEAN ≈ BIASED, the bias
washed out of the ranking → skip the relabel + human pass. Bi-encoder shown as reference.

No humans, no training. Observations only (SP excluded: input mismatch, see logs).

Usage: poetry run python evidence/retrieval/context_eval/scripts/reeval_v4_clean_obs.py
"""
from __future__ import annotations

import json
import math
import os
from pathlib import Path

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

REPO = Path(__file__).resolve().parents[4]
LABELS = REPO / "evidence/fine_tuning/cross_encoder/reranker/labels/round2_expanded"
MERGED = LABELS / "expanded_merged_labels.json"
CANDIDATES = LABELS / "expanded_candidates_for_labeling.json"
COMBINED_GOLDEN = REPO / "evidence/extraction/situation_summary/retrieval_golden_labels.json"
SPLIT = REPO / "evidence/fine_tuning/cross_encoder/reranker/training_data/reranker_split.json"
V4 = REPO / "models/cross_encoder/reranker_v4"

RELEVANCE_MAP = {0: 0.0, 1: 0.25, 2: 1.0}


def ndcg_at_k(scores, rels, k=5):
    """NDCG@k for one query: rank items by `scores`, grade by `rels` (graded gains)."""
    order = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
    def dcg(seq):
        return sum((2 ** seq[i] - 1) / math.log2(i + 2) for i in range(min(k, len(seq))))
    ranked = [rels[i] for i in order]
    ideal = sorted(rels, reverse=True)
    idcg = dcg(ideal)
    return dcg(ranked) / idcg if idcg > 0 else None


def main():
    import torch
    torch.set_num_threads(1)
    from sentence_transformers import CrossEncoder

    # v4 test cases (combined index) -> case_id -> expanded case_index
    test_combined = set(json.load(open(SPLIT))["test"])
    combined = json.load(open(COMBINED_GOLDEN))["labels"]
    combined_idx_to_caseid = {c["case_index"]: c["case_id"] for c in combined}
    cand = json.load(open(CANDIDATES))["cases"]
    caseid_to_expanded = {c["case_id"]: c for c in cand}

    # strong soft + biased labels per (expanded_case_index, key), observations only
    merged = json.load(open(MERGED))["results"]
    soft, biased = {}, {}
    for r in merged:
        if r["item_type"] != "observation":
            continue
        sc = r["labeling"]["scores"]
        k = (r["case_index"], r["key"])
        soft[k] = (RELEVANCE_MAP[sc["chatgpt"]] + RELEVANCE_MAP[sc["sonnet"]]) / 2
        biased[k] = RELEVANCE_MAP[r["relevance"]]

    # assemble per-case observation candidates for the round2 test cases
    cases = []
    skipped = 0
    for ci in sorted(test_combined):
        cid = combined_idx_to_caseid.get(ci)
        exp = caseid_to_expanded.get(cid)
        if exp is None:
            skipped += 1  # round1 case, no strong labels
            continue
        query = "\n".join(exp["golden_situations"])
        obs = exp["retrieved_observations"]
        docs, keys = [], []
        for o in obs:
            parts = [f"Situation: {o['situation']}"]
            if o.get("approach"):
                parts.append(f"Approach: {o['approach']}")
            if o.get("outcome"):
                parts.append(f"Outcome: {o['outcome']}")
            docs.append(" | ".join(parts))
            keys.append((exp["case_index"], o["key"]))
        cases.append({"case_index": exp["case_index"], "role": exp["player_role"],
                      "query": query, "docs": docs, "keys": keys,
                      "bi_scores": [o.get("score", 0.0) for o in obs]})

    print(f"Round2 test cases with strong coverage: {len(cases)} "
          f"(skipped {skipped} round1 cases without strong labels)")

    print("Loading v4 cross-encoder...")
    model = CrossEncoder(str(V4))

    rows = {"v4_vs_biased": [], "v4_vs_clean": [], "bi_vs_clean": [], "bi_vs_biased": []}
    per_case = []
    for c in cases:
        v4_scores = model.predict([[c["query"], d] for d in c["docs"]]).tolist()
        rel_b = [biased[k] for k in c["keys"]]
        rel_c = [soft[k] for k in c["keys"]]
        n_b = ndcg_at_k(v4_scores, rel_b); n_c = ndcg_at_k(v4_scores, rel_c)
        bn_c = ndcg_at_k(c["bi_scores"], rel_c); bn_b = ndcg_at_k(c["bi_scores"], rel_b)
        for name, v in (("v4_vs_biased", n_b), ("v4_vs_clean", n_c),
                        ("bi_vs_clean", bn_c), ("bi_vs_biased", bn_b)):
            if v is not None:
                rows[name].append(v)
        per_case.append({"case_index": c["case_index"], "role": c["role"], "n_obs": len(c["docs"]),
                         "v4_vs_biased": n_b, "v4_vs_clean": n_c})

    def mean(xs):
        return round(sum(xs) / len(xs), 4) if xs else None

    print(f"\n{'='*64}\nv4 OBSERVATION ranking NDCG@5, scored against two truths\n{'='*64}")
    print(f"  v4 ranking | BIASED merged labels : {mean(rows['v4_vs_biased'])}  (n={len(rows['v4_vs_biased'])})")
    print(f"  v4 ranking | CLEAN strong labels  : {mean(rows['v4_vs_clean'])}")
    print(f"  --- reference ---")
    print(f"  bi-encoder | BIASED               : {mean(rows['bi_vs_biased'])}")
    print(f"  bi-encoder | CLEAN                : {mean(rows['bi_vs_clean'])}")
    drop = (mean(rows['v4_vs_biased']) or 0) - (mean(rows['v4_vs_clean']) or 0)
    print(f"\n  v4 drop (biased -> clean): {drop:+.4f}")
    print("  Read: small drop => bias washed out of v4's ranking => skip relabel.")
    print("        large drop => v4 tuned to inflated labels => relabel may help.")

    out = REPO / "evidence/retrieval/context_eval/labels/reeval_v4_clean_obs.json"
    out.write_text(json.dumps({
        "n_cases": len(cases), "skipped_round1": skipped,
        "means": {k: mean(v) for k, v in rows.items()},
        "v4_drop_biased_to_clean": round(drop, 4),
        "per_case": per_case,
    }, indent=2) + "\n")
    print(f"\nWrote {out}")


if __name__ == "__main__":
    main()
