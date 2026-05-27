"""Day summary quality evaluation experiment.

Re-generates day summaries with the current prompt on raw transcripts from
eval sets, then judges each summary using the day summary rubric judge.

Usage:
    poetry run python -m evaluation.experiments.day_summary_eval [--pair PAIR_ID] [--judge-model MODEL]
"""

import argparse
import json
import time
from pathlib import Path

from evaluation.experiments.labeling.day_summary_regen import (
    generate_summary,
    load_pairs,
)
from evaluation.judges.day_summary import (
    DEFAULT_DAY_SUMMARY_JUDGE_MODEL,
    run_day_summary_judge,
)

OUTPUT_DIR = Path("evidence/extraction/day_summary")
RESULTS_FILE = OUTPUT_DIR / "eval_results.jsonl"
SUMMARY_FILE = OUTPUT_DIR / "eval_summary.txt"


def run_eval(pairs: list[dict], judge_model: str) -> list[dict]:
    results = []
    for i, p in enumerate(pairs, 1):
        print(f"\n[{i}/{len(pairs)}] {p['pair_id']} (day={p['day']}, {len(p['raw_discussion'])} msgs)")

        print("  Generating summary...", flush=True)
        try:
            new_summary = generate_summary(p["raw_discussion"], p["day"])
        except Exception as exc:
            print(f"  ERROR generating summary: {exc}")
            continue

        print("  Judging...", flush=True)
        scores = run_day_summary_judge(
            p["raw_discussion"],
            new_summary,
            p["day"],
            model=judge_model,
        )

        result = {
            "pair_id": p["pair_id"],
            "day": p["day"],
            "message_count": len(p["raw_discussion"]),
            "new_summary": new_summary,
            "old_summary": p.get("old_summary"),
            "judge_model": judge_model,
            "scores": scores.model_dump() if scores else None,
        }
        results.append(result)

        if scores:
            print(
                f"  completeness={scores.completeness} "
                f"accuracy={scores.accuracy} "
                f"evidence_type={scores.evidence_type_clarity} "
                f"dynamics={scores.village_dynamics} "
                f"epistemic={scores.epistemic_correctness}"
            )
            if scores.brief_reasoning:
                print(f"  reasoning: {scores.brief_reasoning}")
        else:
            print("  Judge returned no scores")

        time.sleep(1)

    return results


def write_results(results: list[dict]):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with open(RESULTS_FILE, "w") as f:
        for r in results:
            f.write(json.dumps(r) + "\n")

    scored = [r for r in results if r["scores"]]
    if not scored:
        print("\nNo scored results to summarize.")
        return

    dims = ["completeness", "accuracy", "evidence_type_clarity", "village_dynamics", "epistemic_correctness"]
    lines = []
    lines.append(f"Day Summary Eval — {len(scored)} pairs scored")
    lines.append(f"Judge model: {scored[0]['judge_model']}")
    lines.append("")
    lines.append(f"{'Dimension':<25s}  {'Avg':>5s}  {'Min':>3s}  {'Max':>3s}")
    lines.append("-" * 42)
    for dim in dims:
        vals = [r["scores"][dim] for r in scored]
        avg = sum(vals) / len(vals)
        lines.append(f"{dim:<25s}  {avg:5.2f}  {min(vals):3d}  {max(vals):3d}")

    lines.append("")
    lines.append("Per-pair scores:")
    lines.append(f"{'pair_id':<22s}  {'comp':>4s}  {'acc':>4s}  {'evid':>4s}  {'dyn':>4s}  {'epis':>4s}")
    lines.append("-" * 52)
    for r in scored:
        s = r["scores"]
        lines.append(
            f"{r['pair_id']:<22s}  {s['completeness']:4d}  {s['accuracy']:4d}  "
            f"{s['evidence_type_clarity']:4d}  {s['village_dynamics']:4d}  "
            f"{s['epistemic_correctness']:4d}"
        )

    lines.append("")
    lines.append("Reasoning:")
    for r in scored:
        s = r["scores"]
        if s.get("brief_reasoning"):
            lines.append(f"  {r['pair_id']}: {s['brief_reasoning']}")

    summary_text = "\n".join(lines)
    SUMMARY_FILE.write_text(summary_text + "\n")
    print(f"\n{summary_text}")
    print(f"\nResults: {RESULTS_FILE}")
    print(f"Summary: {SUMMARY_FILE}")


def main():
    parser = argparse.ArgumentParser(description="Day summary quality evaluation")
    parser.add_argument("--pair", help="Only evaluate this pair ID")
    parser.add_argument(
        "--judge-model",
        default=DEFAULT_DAY_SUMMARY_JUDGE_MODEL,
        help=f"Judge model (default: {DEFAULT_DAY_SUMMARY_JUDGE_MODEL})",
    )
    args = parser.parse_args()

    pairs = load_pairs()
    if args.pair:
        pairs = [p for p in pairs if p["pair_id"] == args.pair]
        if not pairs:
            print(f"Pair '{args.pair}' not found.")
            return

    print(f"Running day summary eval on {len(pairs)} pairs with judge={args.judge_model}")
    results = run_eval(pairs, args.judge_model)
    write_results(results)


if __name__ == "__main__":
    main()
