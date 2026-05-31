"""Power re-check for the v4 clean-label gate: test vs val vs test+val.

The test-only gate (n=13) is underpowered (~0.10 NDCG detectable). This folds in the
held-out val cases (also not trained on directly, though used for model selection) to
roughly double n and tighten the CI on the biased→clean NDCG drop, for both memory types.
SP doc = situation-only; OBS doc = situation|approach|outcome (matches reranker input).

Usage: poetry run python evidence/retrieval/context_eval/scripts/reeval_v4_power.py
"""
from __future__ import annotations

import json
import math
import os
import statistics as st
from pathlib import Path

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

R = Path(__file__).resolve().parents[4]
L = R / "evidence/fine_tuning/cross_encoder/reranker/labels/round2_expanded"
COMB = R / "evidence/extraction/situation_summary/retrieval_golden_labels.json"
SPLIT = R / "evidence/fine_tuning/cross_encoder/reranker/training_data/reranker_split.json"
RMAP = {0: 0.0, 1: 0.25, 2: 1.0}


def ndcg(s, r, k=5):
    o = sorted(range(len(s)), key=lambda i: s[i], reverse=True)
    d = lambda q: sum((2 ** q[i] - 1) / math.log2(i + 2) for i in range(min(k, len(q))))
    idcg = d(sorted(r, reverse=True))
    return d([r[i] for i in o]) / idcg if idcg > 0 else None


def main():
    import torch
    torch.set_num_threads(1)
    from sentence_transformers import CrossEncoder

    sp = json.load(open(SPLIT))
    comb = {c["case_index"]: c["case_id"] for c in json.load(open(COMB))["labels"]}
    cand = {c["case_id"]: c for c in json.load(open(L / "expanded_candidates_for_labeling.json"))["cases"]}
    merged = json.load(open(L / "expanded_merged_labels.json"))["results"]

    def labels(mt):
        soft, bi = {}, {}
        for r in merged:
            if r["item_type"] != mt:
                continue
            sc = r["labeling"]["scores"]
            k = (r["case_index"], r["key"])
            soft[k] = (RMAP[sc["chatgpt"]] + RMAP[sc["sonnet"]]) / 2
            bi[k] = RMAP[r["relevance"]]
        return soft, bi

    model = CrossEncoder(str(R / "models/cross_encoder/reranker_v4"))

    def run(idxs, mt):
        soft, bi = labels(mt)
        vb, vc, diffs = [], [], []
        for ci in idxs:
            exp = cand.get(comb.get(ci))
            if exp is None:
                continue
            q = "\n".join(exp["golden_situations"])
            items = exp["retrieved_observations"] if mt == "observation" else exp["retrieved_strategy_points"]
            if mt == "observation":
                docs = [" | ".join(["Situation: " + o["situation"]
                                    + ("" if not o.get("approach") else "")]
                                   + (["Approach: " + o["approach"]] if o.get("approach") else [])
                                   + (["Outcome: " + o["outcome"]] if o.get("outcome") else []))
                        for o in items]
            else:
                docs = [o["situation"] for o in items]
            keys = [(exp["case_index"], o["key"]) for o in items]
            scr = model.predict([[q, d] for d in docs]).tolist()
            nb = ndcg(scr, [bi[k] for k in keys])
            nc = ndcg(scr, [soft[k] for k in keys])
            if nb is not None and nc is not None:
                vb.append(nb); vc.append(nc); diffs.append(nb - nc)
        n = len(diffs); m = st.mean(diffs); se = st.pstdev(diffs) / n ** 0.5 if n > 1 else 0
        return n, round(sum(vb) / n, 3), round(sum(vc) / n, 3), round(m, 4), \
            round(m - 2.179 * se, 4), round(m + 2.179 * se, 4)

    for mt in ["observation", "strategy_point"]:
        print(f"\n=== {mt} ===  n | biased | clean | drop | 95% CI")
        for name, idxs in [("test", sp["test"]), ("val", sp["val"]), ("test+val", sp["test"] + sp["val"])]:
            n, b, c, d, lo, hi = run(idxs, mt)
            print(f"  {name:9s}: n={n:2d} | {b} | {c} | {d:+.4f} | [{lo:+.4f},{hi:+.4f}] "
                  f"{'SIG' if lo > 0 else 'ns'}")


if __name__ == "__main__":
    main()
