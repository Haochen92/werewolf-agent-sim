"""Day summary quality evaluation experiment.

Re-generates day summaries with the current prompt on raw transcripts from
eval sets, then judges each summary using the day summary rubric judge.

Usage:
    poetry run python -m evaluation.experiments.day_summary_eval [--pair PAIR_ID] [--judge-model MODEL]
    poetry run python -m evaluation.experiments.day_summary_eval --gen-model gemini-3.5-flash
    poetry run python -m evaluation.experiments.day_summary_eval --gen-model gemini-3.1-flash-lite --thinking medium
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


def _output_suffix(gen_model: str | None, thinking_level: str | None) -> str:
    model = (gen_model or "flash-lite").replace("gemini-", "").replace(".", "")
    parts = [model]
    if thinking_level:
        parts.append(thinking_level)
    return "_".join(parts)


def run_eval(
    pairs: list[dict],
    judge_model: str,
    *,
    gen_model: str | None = None,
    thinking_level: str | None = None,
) -> list[dict]:
    results = []
    for i, p in enumerate(pairs, 1):
        print(f"\n[{i}/{len(pairs)}] {p['pair_id']} (day={p['day']}, {len(p['raw_discussion'])} msgs)")

        print("  Generating summary...", flush=True)
        try:
            new_summary = generate_summary(
                p["raw_discussion"], p["day"],
                model=gen_model, thinking_level=thinking_level,
            )
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
            "gen_model": gen_model or "gemini-3.1-flash-lite",
            "thinking_level": thinking_level or "minimal",
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


def write_results(results: list[dict], suffix: str):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    results_file = OUTPUT_DIR / f"eval_results_{suffix}.jsonl"
    summary_file = OUTPUT_DIR / f"eval_summary_{suffix}.txt"

    with open(results_file, "w") as f:
        for r in results:
            f.write(json.dumps(r) + "\n")

    scored = [r for r in results if r["scores"]]
    if not scored:
        print("\nNo scored results to summarize.")
        return

    dims = ["completeness", "accuracy", "evidence_type_clarity", "village_dynamics", "epistemic_correctness"]
    lines = []
    lines.append(f"Day Summary Eval — {len(scored)} pairs scored")
    lines.append(f"Gen model: {scored[0]['gen_model']} (thinking={scored[0]['thinking_level']})")
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
    summary_file.write_text(summary_text + "\n")
    print(f"\n{summary_text}")
    print(f"\nResults: {results_file}")
    print(f"Summary: {summary_file}")


def main():
    parser = argparse.ArgumentParser(description="Day summary quality evaluation")
    parser.add_argument("--pair", help="Only evaluate this pair ID")
    parser.add_argument(
        "--gen-model",
        default=None,
        help="Generation model (default: gemini-3.1-flash-lite via get_llm())",
    )
    parser.add_argument(
        "--thinking",
        default=None,
        help="Thinking level for generation model (minimal, low, medium, high)",
    )
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

    gen_label = args.gen_model or "gemini-3.1-flash-lite (default)"
    thinking_label = args.thinking or "minimal (default)"
    print(f"Running day summary eval on {len(pairs)} pairs")
    print(f"  gen={gen_label}, thinking={thinking_label}, judge={args.judge_model}")

    results = run_eval(
        pairs, args.judge_model,
        gen_model=args.gen_model, thinking_level=args.thinking,
    )
    suffix = _output_suffix(args.gen_model, args.thinking)
    write_results(results, suffix)


if __name__ == "__main__":
    main()
