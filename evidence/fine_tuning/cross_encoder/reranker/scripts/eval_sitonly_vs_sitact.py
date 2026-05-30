"""v5 input-parity ablation: situation-only vs situation+action cross-encoder.

Both arms were trained through the same pipeline (evaluation.training) with the
same labels, split, seed, and hyperparameters; the ONLY difference is the
strategy-point document text (sentence2):

    sitonly:  sentence2 = situation                 (matches production)
    sitact:   sentence2 = situation | Action: ...    (what the labelers saw)

Each model is evaluated on ITS OWN matching test split (a model must see the SP
format it was trained on), against the identical cases/labels. We report
per-case NDCG@k overall and broken out by memory type. The strategy-point NDCG
is the primary readout — it is the only thing the action can move; observations
are byte-identical across arms and act as a control.

This tests one thing only: given labels created with the action visible, does a
CE that also sees the action rank strategy points better than the situation-only
CE? It does NOT test whether the labels were "contaminated" — that needs a
situation-only relabel.

Usage:
    poetry run python evidence/fine_tuning/cross_encoder/reranker/scripts/eval_sitonly_vs_sitact.py \
        --sitonly models/cross_encoder/reranker_v5_sitonly \
        --sitact  models/cross_encoder/reranker_v5_sitact
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from evaluation.training.evaluator import RankingEvaluator

REPO_ROOT = Path(__file__).resolve().parents[5]
DATA_ROOT = REPO_ROOT / "evidence" / "fine_tuning" / "cross_encoder" / "reranker"
SITONLY_TEST = DATA_ROOT / "training_data_sitonly" / "reranker_test.jsonl"
SITACT_TEST = DATA_ROOT / "training_data_sitact" / "reranker_test.jsonl"


def _read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def _subset(rows: list[dict], mem_type: str | None) -> list[dict]:
    return rows if mem_type is None else [r for r in rows if r["mem_type"] == mem_type]


def _eval_arm(model_path: str, test_path: Path) -> dict[str, dict]:
    from sentence_transformers.cross_encoder import CrossEncoder

    model = CrossEncoder(model_path)
    rows = _read_jsonl(test_path)
    ev = RankingEvaluator()
    out = {}
    for label, mem_type in [("overall", None),
                            ("strategy_point", "strategy_point"),
                            ("observation", "observation")]:
        sub = _subset(rows, mem_type)
        out[label] = ev.evaluate(model, sub)
    return out


def _fmt_ci(ci) -> str:
    return f"[{ci[0]:.3f}, {ci[1]:.3f}]" if ci else "—"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sitonly", required=True, help="path to situation-only model")
    parser.add_argument("--sitact", required=True, help="path to situation+action model")
    args = parser.parse_args()

    print("Evaluating situation-only arm...")
    a = _eval_arm(args.sitonly, SITONLY_TEST)
    print("Evaluating situation+action arm...")
    b = _eval_arm(args.sitact, SITACT_TEST)

    print("\n" + "=" * 78)
    print("v5 ablation: situation-only vs situation+action (same labels/split/seed)")
    print("=" * 78)
    header = f"{'Subset':<16}{'metric':<12}{'sitonly':>12}{'sitact':>12}{'delta':>10}"
    for subset in ["overall", "strategy_point", "observation"]:
        print(f"\n--- {subset} (n_cases={a[subset]['n_cases']}, "
              f"n_pairs={a[subset]['n_pairs']}) ---")
        print(header)
        for m in ["ndcg3", "ndcg5", "ndcg10", "pearson_r", "mse"]:
            av, bv = a[subset][m], b[subset][m]
            print(f"{'':<16}{m:<12}{av:>12.4f}{bv:>12.4f}{bv - av:>+10.4f}")
        print(f"{'':<16}{'ndcg5_ci95':<12}{_fmt_ci(a[subset]['ndcg5_ci95']):>24}"
              f"{_fmt_ci(b[subset]['ndcg5_ci95']):>14}")

    sp_delta = b["strategy_point"]["ndcg5"] - a["strategy_point"]["ndcg5"]
    print("\n" + "=" * 78)
    print(f"PRIMARY READOUT — strategy_point NDCG@5 delta (sitact - sitonly): "
          f"{sp_delta:+.4f}")
    print("  >0 material : action carries ranking signal the situation-only CE lacks")
    print("  ~0          : action redundant for ranking; keep production situation-only")
    print("  <0          : action adds noise / overfit")
    print("=" * 78)

    out_path = DATA_ROOT / "eval_sitonly_vs_sitact_results.json"
    out_path.write_text(json.dumps({"sitonly": a, "sitact": b}, indent=2))
    print(f"\nWrote {out_path}")


if __name__ == "__main__":
    main()
