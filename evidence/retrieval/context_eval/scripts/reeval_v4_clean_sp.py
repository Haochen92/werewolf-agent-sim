"""SP companion to reeval_v4_clean_obs.py: does v4's strategy-point ranking degrade
under the strict strong-judge labels?

Mirrors the observation gate, but on strategy points: doc = situation-only (matches the
reranker's SP input), labels = soft ChatGPT+Sonnet. These SP labels were formed
action-visible (the untested residual), but since v4's SP ranking is scored against them
and holds up, the action question is moot for the ranking. No humans, no training.

Usage: poetry run python evidence/retrieval/context_eval/scripts/reeval_v4_clean_sp.py
"""
from __future__ import annotations

import json
import math
import os
import statistics as st
from pathlib import Path

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

REPO = Path(__file__).resolve().parents[4]
L = REPO / "evidence/fine_tuning/cross_encoder/reranker/labels/round2_expanded"
MERGED = L / "expanded_merged_labels.json"
CAND = L / "expanded_candidates_for_labeling.json"
COMB = REPO / "evidence/extraction/situation_summary/retrieval_golden_labels.json"
SPLIT = REPO / "evidence/fine_tuning/cross_encoder/reranker/training_data/reranker_split.json"
V4 = REPO / "models/cross_encoder/reranker_v4"
RMAP = {0: 0.0, 1: 0.25, 2: 1.0}


def ndcg(scores, rels, k=5):
    order = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
    dcg = lambda seq: sum((2 ** seq[i] - 1) / math.log2(i + 2) for i in range(min(k, len(seq))))
    idcg = dcg(sorted(rels, reverse=True))
    return dcg([rels[i] for i in order]) / idcg if idcg > 0 else None


def main():
    import torch
    torch.set_num_threads(1)
    from sentence_transformers import CrossEncoder

    test = set(json.load(open(SPLIT))["test"])
    comb = {c["case_index"]: c["case_id"] for c in json.load(open(COMB))["labels"]}
    cand = {c["case_id"]: c for c in json.load(open(CAND))["cases"]}
    soft, biased = {}, {}
    for r in json.load(open(MERGED))["results"]:
        if r["item_type"] != "strategy_point":
            continue
        sc = r["labeling"]["scores"]
        k = (r["case_index"], r["key"])
        soft[k] = (RMAP[sc["chatgpt"]] + RMAP[sc["sonnet"]]) / 2
        biased[k] = RMAP[r["relevance"]]

    model = CrossEncoder(str(V4))
    vb, vc, skipped, pc = [], [], 0, []
    for ci in sorted(test):
        exp = cand.get(comb.get(ci))
        if exp is None:
            skipped += 1
            continue
        q = "\n".join(exp["golden_situations"])
        sp = exp["retrieved_strategy_points"]
        docs = [s["situation"] for s in sp]  # SP = situation-only (matches reranker input)
        keys = [(exp["case_index"], s["key"]) for s in sp]
        scores = model.predict([[q, d] for d in docs]).tolist()
        nb = ndcg(scores, [biased[k] for k in keys])
        nc = ndcg(scores, [soft[k] for k in keys])
        if nb is not None:
            vb.append(nb)
        if nc is not None:
            vc.append(nc)
        pc.append({"case_index": exp["case_index"], "role": exp["player_role"],
                   "v4_vs_biased": nb, "v4_vs_clean": nc})

    mean = lambda x: round(sum(x) / len(x), 4) if x else None
    diffs = [c["v4_vs_biased"] - c["v4_vs_clean"] for c in pc
             if c["v4_vs_biased"] is not None and c["v4_vs_clean"] is not None]
    n = len(diffs)
    m = st.mean(diffs)
    se = st.pstdev(diffs) / n ** 0.5
    print(f"SP cases with strong coverage: {len(vb)} (skipped {skipped} round1)")
    print(f"v4 SP ranking | BIASED labels: {mean(vb)}")
    print(f"v4 SP ranking | CLEAN  labels: {mean(vc)}")
    print(f"drop biased->clean: {m:+.4f}  95% CI [{m-2.179*se:+.4f}, {m+2.179*se:+.4f}] (n={n})")
    out = REPO / "evidence/retrieval/context_eval/labels/reeval_v4_clean_sp.json"
    out.write_text(json.dumps({
        "n_cases": len(vb), "skipped_round1": skipped,
        "means": {"v4_vs_biased": mean(vb), "v4_vs_clean": mean(vc)},
        "drop_mean": round(m, 4), "drop_ci95": [round(m - 2.179 * se, 4), round(m + 2.179 * se, 4)],
        "per_case": pc,
    }, indent=2) + "\n")
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
