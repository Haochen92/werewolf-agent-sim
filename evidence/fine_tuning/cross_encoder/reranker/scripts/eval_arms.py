"""Compare reranker arms on the held-out test set, broken out by memory type.

Generic over arms: each arm is a trained model evaluated on ITS OWN matching
test split (a model must see the sentence2 format it was trained on), against
the identical cases/labels. Per-case NDCG@k is reported overall and per memory
type, with deltas against the first (baseline) arm.

Each --arm is ``label:model_path:test_jsonl``. The first arm is the baseline;
deltas are (arm - baseline). The memory type that is byte-identical across the
arms acts as the control and should show ~0 movement.

Examples:
    # SP ablation (action): observations are the control
    poetry run python .../eval_arms.py \
      --arm sitonly:models/cross_encoder/reranker_v5_sitonly:.../training_data_sitonly/reranker_test.jsonl \
      --arm sitact:models/cross_encoder/reranker_v5_sitact:.../training_data_sitact/reranker_test.jsonl

    # Observation ablation (strip approach+outcome): strategy points are the control
    poetry run python .../eval_arms.py \
      --arm obs_full:models/cross_encoder/reranker_v5_sitonly:.../training_data_sitonly/reranker_test.jsonl \
      --arm obs_sitonly:models/cross_encoder/reranker_v5_allsitonly:.../training_data_allsitonly/reranker_test.jsonl
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from evaluation.training.evaluator import RankingEvaluator

SUBSETS = ["overall", "strategy_point", "observation"]


def _read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]


def _eval_arm(model_path: str, test_path: str) -> dict[str, dict]:
    from sentence_transformers.cross_encoder import CrossEncoder

    model = CrossEncoder(model_path)
    rows = _read_jsonl(test_path)
    ev = RankingEvaluator()
    out = {}
    for subset in SUBSETS:
        sub = rows if subset == "overall" else [r for r in rows if r["mem_type"] == subset]
        out[subset] = ev.evaluate(model, sub)
    return out


def _fmt_ci(ci) -> str:
    return f"[{ci[0]:.3f}, {ci[1]:.3f}]" if ci else "—"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--arm", action="append", required=True,
                        help="label:model_path:test_jsonl (repeatable; first is baseline)")
    args = parser.parse_args()

    arms = []
    for spec in args.arm:
        label, model_path, test_path = spec.split(":", 2)
        print(f"Evaluating {label} ...")
        arms.append((label, _eval_arm(model_path, test_path)))

    base_label, base = arms[0]
    print("\n" + "=" * 88)
    print(f"Reranker arm comparison (baseline = {base_label}; deltas are arm - baseline)")
    print("=" * 88)

    for subset in SUBSETS:
        print(f"\n--- {subset} (n_cases={base[subset]['n_cases']}, "
              f"n_pairs={base[subset]['n_pairs']}) ---")
        cols = "".join(f"{lbl:>14}" for lbl, _ in arms)
        print(f"{'metric':<12}{cols}{'Δ vs base':>12}")
        for m in ["ndcg3", "ndcg5", "ndcg10", "pearson_r", "mse"]:
            vals = "".join(f"{res[subset][m]:>14.4f}" for _, res in arms)
            delta = arms[-1][1][subset][m] - base[subset][m]
            print(f"{m:<12}{vals}{delta:>+12.4f}")
        cis = "".join(f"{_fmt_ci(res[subset]['ndcg5_ci95']):>14}" for _, res in arms)
        print(f"{'ndcg5_ci95':<12}{cis}")

    print("\n" + "=" * 88)
    print("Reminder: the control memory type (byte-identical text across arms) should be ~flat.")
    print("=" * 88)


if __name__ == "__main__":
    main()
