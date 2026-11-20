"""Context-drift diagnostic: does giving the auto panel full context move its labels?

Precondition check for the context-based retrieval eval (see
``evidence/retrieval/context_eval/experiment_log.md``). Runs the SAME auto panel
(flashlite + mistral + nim) that produced the stored query-only labels, but with the
full game state injected into the prompt (condition B). Condition A (query-only) is
read directly from the stored ``expanded_labels_{model}.json`` — no re-run.

Because the model is held constant and the prompt is byte-identical apart from the
added ``## Full game state`` block, the per-model label delta isolates the effect of
seeing context (no capability confound, unlike manual-vs-auto).

Read the result via the decision criteria in the experiment log:
  - low flip + no directional bias  -> context adds nothing -> eval likely unnecessary
  - asymmetric 0 -> {1,2} promotion  -> summary is lossy      -> build the eval
  - symmetric / unstructured flips   -> labeler noise, NOT signal

Usage:
    poetry run python evidence/retrieval/context_eval/scripts/context_drift_diagnostic.py \
        [--sample 300] [--seed 42] [--resume]
"""
from __future__ import annotations

import argparse
import json
import random
from collections import defaultdict
from pathlib import Path

from evaluation.labeling.adapters.context_relevance import ContextRerankerAdapter
from evaluation.labeling.config import ModelSpec
from evaluation.labeling.engine import label_items

REPO_ROOT = Path(__file__).resolve().parents[4]
LABELS_DIR = (
    REPO_ROOT / "evidence" / "fine_tuning" / "cross_encoder" / "reranker"
    / "labels" / "round2_expanded"
)
CANDIDATES = LABELS_DIR / "expanded_candidates_for_labeling.json"
EVAL_DATASET = REPO_ROOT / "eval_sets" / "v4_reranker_expanded.jsonl"
OUT_DIR = REPO_ROOT / "evidence" / "retrieval" / "context_eval" / "labels"

# Same panel that produced the query-only baseline labels.
MODELS = [
    ModelSpec(name="gemini-3.1-flash-lite", thinking_level="low"),
    ModelSpec(name="mistral/mistral-small-2506", rpm_limit=300),
    ModelSpec(name="nim/meta/llama-3.1-8b-instruct", rpm_limit=150),
]
ITEM_WORKERS = 8

# context model_scores key -> (short name, baseline file)
MODEL_TO_BASELINE = {
    "gemini-3.1-flash-lite": ("flashlite", LABELS_DIR / "expanded_labels_flashlite.json"),
    "mistral/mistral-small-2506": ("mistral", LABELS_DIR / "expanded_labels_mistral.json"),
    "nim/meta/llama-3.1-8b-instruct": ("nim", LABELS_DIR / "expanded_labels_nim.json"),
}


def _load_baseline(path: Path) -> dict[tuple[int, str], int]:
    """(case_index, key) -> query-only relevance from a per-model label file."""
    data = json.load(open(path))
    out: dict[tuple[int, str], int] = {}
    for case in data["cases"]:
        ci = case["case_index"]
        for lbl in case.get("observation_labels", []) + case.get("strategy_labels", []):
            out[(ci, lbl["key"])] = lbl["relevance"]
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--sample", type=int, default=300,
                    help="number of items to sample (0 = all 1848)")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--resume", action="store_true")
    args = ap.parse_args()

    adapter = ContextRerankerAdapter(eval_dataset_path=EVAL_DATASET)
    items = adapter.load_items(CANDIDATES)
    n = len(items)
    if args.sample and args.sample < n:
        idx = sorted(random.Random(args.seed).sample(range(n), args.sample))
        items = [items[i] for i in idx]
    print(f"Context-labeling {len(items)}/{n} items x {len(MODELS)} models")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    results = label_items(
        items, MODELS, adapter, OUT_DIR / "context_labels.json",
        resume=args.resume, max_item_workers=ITEM_WORKERS,
    )

    # context: (case_index, key) -> {model_name: label}
    ctx = {(r["case_index"], r["key"]): r["model_scores"] for r in results}
    item_types = {(r["case_index"], r["key"]): r["item_type"] for r in results}

    report: dict = {
        "n_items": len(ctx), "sample": args.sample, "seed": args.seed,
        "design": "condition B (query+context) vs stored condition A (query-only); "
                  "same panel, prompt byte-identical apart from added game-state block",
        "models": {},
    }
    print(f"\n{'='*72}\nCONTEXT DRIFT: query+context vs query-only ({len(ctx)} items)\n{'='*72}")

    for model_key, (short, base_path) in MODEL_TO_BASELINE.items():
        base = _load_baseline(base_path)
        flips = pairs = abs_delta = signed = 0
        promote_0 = base_0 = 0      # 0 -> {1,2}: summary-missed-tension direction
        demote_to_0 = base_nonzero = 0
        dist: dict[int, int] = defaultdict(int)
        by_type: dict[str, dict[str, int]] = defaultdict(lambda: {"pairs": 0, "flips": 0})
        for k, scores in ctx.items():
            cb = scores.get(model_key)
            ca = base.get(k)
            if cb is None or ca is None:
                continue
            pairs += 1
            d = cb - ca            # context - query_only
            dist[d] += 1
            abs_delta += abs(d)
            signed += d
            if d != 0:
                flips += 1
            t = item_types.get(k, "?")
            by_type[t]["pairs"] += 1
            by_type[t]["flips"] += 1 if d != 0 else 0
            if ca == 0:
                base_0 += 1
                if cb >= 1:
                    promote_0 += 1
            else:
                base_nonzero += 1
                if cb == 0:
                    demote_to_0 += 1
        if pairs:
            report["models"][short] = {
                "pairs": pairs,
                "flip_rate": round(flips / pairs, 4),
                "mean_abs_delta": round(abs_delta / pairs, 4),
                "mean_signed_delta": round(signed / pairs, 4),
                "promotion_0_to_useful_rate": round(promote_0 / base_0, 4) if base_0 else None,
                "demotion_useful_to_0_rate": round(demote_to_0 / base_nonzero, 4) if base_nonzero else None,
                "delta_distribution": {str(k): v for k, v in sorted(dist.items())},
                "by_item_type": {t: {**v, "flip_rate": round(v["flips"]/v["pairs"], 4)}
                                 for t, v in by_type.items() if v["pairs"]},
            }
            print(f"\n{short} ({model_key})")
            print(f"  flip rate:        {flips}/{pairs} = {flips/pairs:.1%}")
            print(f"  mean |Δ|:         {abs_delta/pairs:.3f}    mean signed Δ (ctx-query): {signed/pairs:+.3f}")
            print(f"  0 -> useful:      {promote_0}/{base_0} = "
                  f"{(promote_0/base_0 if base_0 else 0):.1%}  (summary-missed-tension direction)")
            print(f"  useful -> 0:      {demote_to_0}/{base_nonzero} = "
                  f"{(demote_to_0/base_nonzero if base_nonzero else 0):.1%}")
            print(f"  Δ dist (ctx-query): {dict(sorted(dist.items()))}")

    # consensus: rounded mean across available models per condition
    def _consensus(scores: dict) -> float | None:
        vals = [v for v in scores.values() if v is not None]
        return sum(vals) / len(vals) if vals else None

    bases = {short: _load_baseline(p) for _, (short, p) in MODEL_TO_BASELINE.items()}
    short_for = {mk: s for mk, (s, _) in MODEL_TO_BASELINE.items()}
    cflips = cpairs = csigned = 0
    for k, scores in ctx.items():
        cb = _consensus(scores)
        a_scores = {s: bases[s].get(k) for s in bases}
        ca = _consensus(a_scores)
        if cb is None or ca is None:
            continue
        cpairs += 1
        if round(cb) != round(ca):
            cflips += 1
        csigned += (cb - ca)
    if cpairs:
        report["consensus"] = {
            "pairs": cpairs,
            "rounded_mean_flip_rate": round(cflips / cpairs, 4),
            "mean_signed_delta": round(csigned / cpairs, 4),
        }
        print(f"\nconsensus (rounded mean) flip rate: {cflips}/{cpairs} = {cflips/cpairs:.1%}"
              f"   mean signed Δ: {csigned/cpairs:+.3f}")

    (OUT_DIR / "drift_report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(f"\nWrote {OUT_DIR / 'drift_report.json'}")
    print(f"{'='*72}")
    print("Read: low flip + ~0 signed Δ => context adds nothing => eval likely unneeded.")
    print("      high '0 -> useful' rate => summary lossy => build the eval.")
    print("      symmetric flips, ~0 signed Δ, but high flip => labeler noise, NOT signal.")
    print(f"{'='*72}")


if __name__ == "__main__":
    main()
