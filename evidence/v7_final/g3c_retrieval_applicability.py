"""v7 Gate G3c — retrieval applicability/precision (plan §5-G3, §10b). Zero spend, no LLM, no re-judge.

G3a showed not_relevant DOMINATES retrieval (30–69%) → retrieval precision is the #1 v7 lever, and the
credit telemetry is mostly noise until it's fixed (§10d). G3c asks the cheap precursor: is that fixable
by a retrieval KNOB, or is it a hard (semantic) problem?

The agent already labeled each RETRIEVED SP follow / override / not_relevant, and each retrieved SP
carries its similarity SCORE + RANK (strategy_index aligns to retrieved order, verified). So without any
re-retrieval or re-judging we can ask:

  Does the embedding SCORE (and rank) separate not_relevant from applicable?
    - YES (not_relevant scores lower / sits at worse ranks) → a score threshold / rerank-to-top
      mechanically cuts the waste → retrieval fix is a KNOB (cheap win).
    - NO (score flat across verdicts) → similarity ≠ applicability (the v6 "text-embedding ≠
      precondition-match" finding) → a threshold won't help; need STRUCTURED gating / a precondition
      matcher / better reranker → harder problem.

This bounds the cheapest-available retrieval fix; it does NOT re-run retrieval with gating (that needs
spend). It tells us whether the dominant waste is rank-separable at all.
"""

import glob
import json
import sys

sys.path.insert(0, "evaluation/src")
sys.path.insert(0, ".")
from core.stats import point_biserial  # noqa: E402

SESSIONS = sorted({p.split("/")[-2] for p in glob.glob("batch_results/eval_cases/v6ab_*/*.jsonl")})


def eval_cases(path):
    for line in open(path):
        if not line.strip():
            continue
        o = json.loads(line).get("output") or {}
        e = o.get("eval_case") if isinstance(o, dict) else None
        if e:
            yield e


def main():
    # rows: (score, rank, is_not_relevant, is_applicable)
    rows = []
    for s in SESSIONS:
        for f in glob.glob(f"batch_results/eval_cases/{s}/*.jsonl"):
            for e in eval_cases(f):
                verds = e.get("strategy_verdicts") or []
                rsp = e.get("retrieved_strategy_points") or []
                if not verds or not rsp:
                    continue
                for v in verds:
                    idx = v.get("strategy_index")
                    verdict = v.get("verdict")
                    if not isinstance(idx, int) or not (1 <= idx <= len(rsp)):
                        continue
                    score = rsp[idx - 1].get("score")
                    if score is None:
                        continue
                    rows.append((float(score), idx, int(verdict == "not_relevant"),
                                 int(verdict in ("follow", "override"))))

    n = len(rows)
    print(f"joined (score,rank,verdict) rows: {n}")
    nr_rate = sum(r[2] for r in rows) / n
    print(f"overall not_relevant rate: {nr_rate:.0%}\n")

    # 1. does SCORE separate not_relevant from the rest?
    nr = [r[0] for r in rows if r[2]]
    appl = [r[0] for r in rows if r[3]]
    r_sc, p_sc = point_biserial([r[2] for r in rows], [r[0] for r in rows])
    print("=== 1. SCORE vs not_relevant ===")
    print(f"  mean score: not_relevant={sum(nr)/len(nr):.3f} (n={len(nr)})  "
          f"applicable={sum(appl)/len(appl):.3f} (n={len(appl)})")
    print(f"  point-biserial(not_relevant ~ score) r={r_sc:+.3f} p={p_sc:.2e}")

    # 2. not_relevant rate by RANK
    print("\n=== 2. not_relevant rate by RANK (does waste concentrate in the tail?) ===")
    by_rank = {}
    for sc, rank, isnr, _ in rows:
        by_rank.setdefault(rank, [0, 0])
        by_rank[rank][0] += isnr
        by_rank[rank][1] += 1
    for rank in sorted(by_rank)[:8]:
        nrc, tot = by_rank[rank]
        print(f"  rank {rank}: not_relevant {nrc}/{tot} = {nrc/tot:.0%}")

    # 3. precision @ keeping only top-k vs all  (mechanical effect of a rank cut)
    print("\n=== 3. mechanical effect of a top-k cut on not_relevant share ===")
    for k in (1, 2, 3, 5):
        kept = [r for r in rows if r[1] <= k]
        if kept:
            share = sum(r[2] for r in kept) / len(kept)
            print(f"  keep top-{k}: not_relevant share {share:.0%} (n={len(kept)})")

    print("\n=== verdict ===")
    if abs(r_sc) >= 0.1 and p_sc < 0.01:
        print("  SCORE separates → retrieval precision is partly a KNOB (threshold/rerank cuts waste).")
    else:
        print("  SCORE does NOT separate → similarity ≠ applicability → retrieval precision needs "
              "STRUCTURED gating / better rerank, not a threshold (harder, but the #1 lever).")


if __name__ == "__main__":
    main()
