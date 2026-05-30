"""SP label-drift diagnostic: does seeing the strategy *action* move the labels?

Cheap, automated read on the Q1 question (label contamination) that we set aside.
Runs the SAME auto panel (flash-lite + mistral + NIM-8B) twice over the SAME
sampled strategy-point pairs:

    condition A (action):  candidate = "Situation: … | Action: …"   (production labeling format)
    condition B (sit-only): candidate = "Situation: …"             (what the situation-only CE input is)

The prompt wording is byte-identical between conditions — only the candidate
text toggles — so the per-model label difference isolates the action's effect.

Decision:
    small per-model flip rate  -> action barely moves labels; leak negligible -> keep as-is (Option 1)
    large per-model flip rate  -> labels encode action usefulness -> full situation-only relabel justified (Option 2)

This is a measurement, NOT the production relabel: auto panel only, no manual
labelers, a sample of pairs.

Usage:
    poetry run python evidence/fine_tuning/cross_encoder/reranker/scripts/sp_label_drift_diagnostic.py \
        [--sample 240] [--seed 42] [--resume]
"""
from __future__ import annotations

import argparse
import json
import random
from collections import defaultdict
from pathlib import Path

from evaluation.labeling.adapters.reranker import RerankerAdapter
from evaluation.labeling.config import ModelSpec
from evaluation.labeling.engine import label_items

REPO_ROOT = Path(__file__).resolve().parents[5]
CANDIDATES = (
    REPO_ROOT / "evidence" / "fine_tuning" / "cross_encoder" / "reranker"
    / "labels" / "round2_expanded" / "expanded_candidates_for_labeling.json"
)
OUT_DIR = (
    REPO_ROOT / "evidence" / "fine_tuning" / "cross_encoder" / "reranker"
    / "labels" / "diagnostic_sp_drift"
)

MODELS = [
    ModelSpec(name="gemini-3.1-flash-lite", thinking_level="low"),
    ModelSpec(name="mistral/mistral-small-2506", rpm_limit=300),
    ModelSpec(name="nim/meta/llama-3.1-8b-instruct", rpm_limit=150),
]
# Item-level concurrency: flash-lite (thinking) is ~3.7s/call and uncapped, so
# overlapping items is what removes it as the throughput bottleneck.
ITEM_WORKERS = 8


def _label_map(results: list[dict]) -> dict[tuple, dict[str, int | None]]:
    """(case_index, key) -> {model_name: label}."""
    out = {}
    for r in results:
        out[(r["case_index"], r["key"])] = r["model_scores"]
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--sample", type=int, default=240,
                    help="number of SP pairs to sample (0 = all)")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--resume", action="store_true")
    args = ap.parse_args()

    # Both adapters load the SAME SP pairs in the same order; only the candidate
    # text (action shown vs hidden) differs, so index i lines up across them.
    adapter_action = RerankerAdapter(show_action=True, sp_only=True)
    adapter_sit = RerankerAdapter(show_action=False, sp_only=True)
    items_action = adapter_action.load_items(CANDIDATES)
    items_sit = adapter_sit.load_items(CANDIDATES)
    assert [it.key for it in items_action] == [it.key for it in items_sit], "ordering mismatch"

    n = len(items_action)
    if args.sample and args.sample < n:
        idx = sorted(random.Random(args.seed).sample(range(n), args.sample))
        items_action = [items_action[i] for i in idx]
        items_sit = [items_sit[i] for i in idx]
    print(f"Diagnosing {len(items_action)} SP pairs x {len(MODELS)} models x 2 conditions")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    res_action = label_items(items_action, MODELS, adapter_action,
                             OUT_DIR / "action_labels.json", resume=args.resume,
                             max_item_workers=ITEM_WORKERS)
    res_sit = label_items(items_sit, MODELS, adapter_sit,
                          OUT_DIR / "situation_labels.json", resume=args.resume,
                          max_item_workers=ITEM_WORKERS)

    a, b = _label_map(res_action), _label_map(res_sit)
    keys = sorted(set(a) & set(b))

    report: dict = {"n_pairs": len(keys), "models": {}, "consensus": {}}
    print(f"\n{'='*70}\nSP LABEL DRIFT: action-visible vs situation-only ({len(keys)} pairs)\n{'='*70}")

    for ms in MODELS:
        m = ms.name
        deltas, flips, signed = 0, 0, 0
        pairs = 0
        dist = defaultdict(int)
        for k in keys:
            la, lb = a[k].get(m), b[k].get(m)
            if la is None or lb is None:
                continue
            pairs += 1
            d = la - lb            # action - situation_only
            dist[d] += 1
            if d != 0:
                flips += 1
            deltas += abs(d)
            signed += d
        if pairs:
            report["models"][m] = {
                "pairs": pairs,
                "flip_rate": round(flips / pairs, 4),
                "mean_abs_delta": round(deltas / pairs, 4),
                "mean_signed_delta": round(signed / pairs, 4),
                "delta_distribution": {str(k): v for k, v in sorted(dist.items())},
            }
            print(f"\n{m}")
            print(f"  flip rate (label changed when action hidden): {flips}/{pairs} = {flips/pairs:.1%}")
            print(f"  mean |Δ|: {deltas/pairs:.3f}   mean signed Δ (action−sitonly): {signed/pairs:+.3f}")
            print(f"  Δ distribution (action−sitonly): {dict(sorted(dist.items()))}")

    # Consensus: rounded mean label across available models per condition.
    def _consensus(scores: dict[str, int | None]) -> float | None:
        vals = [v for v in scores.values() if v is not None]
        return sum(vals) / len(vals) if vals else None

    cflips = cpairs = 0
    for k in keys:
        ca, cb = _consensus(a[k]), _consensus(b[k])
        if ca is None or cb is None:
            continue
        cpairs += 1
        if round(ca) != round(cb):
            cflips += 1
    if cpairs:
        report["consensus"] = {"pairs": cpairs, "rounded_mean_flip_rate": round(cflips / cpairs, 4)}
        print(f"\nconsensus (rounded mean) flip rate: {cflips}/{cpairs} = {cflips/cpairs:.1%}")

    (OUT_DIR / "drift_report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(f"\nWrote {OUT_DIR / 'drift_report.json'}")
    print(f"{'='*70}")
    print("Read: per-model flip rate <~15% => leak small, keep as-is (Option 1).")
    print("      flip rate >~25% or strong +signed Δ (action inflates) => relabel SP (Option 2).")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()
