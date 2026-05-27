"""Re-generate day summaries using the updated prompt on raw transcripts.

Extracts raw discussion transcripts from the eval set, runs the current
DAY_SUMMARY_PROMPT on them, and saves old vs new summaries for comparison.

Usage:
    poetry run python evaluation/experiments/labeling/day_summary_regen.py [--pair PAIR_ID]
"""

import argparse
import json
from pathlib import Path

from Agents.formatters import format_day_channel
from Agents.prompts import DAY_SUMMARY_PROMPT, SITUATION_STANDARDS
from Agents.schemas import DaySummaryOutput
from Agents.schemas.game_events import DayChannel

EVAL_SETS = [
    Path("eval_sets/v4_filtering_eval.jsonl"),
    Path("eval_sets/v2_memory_wolfs_only_all_enabled_all_enabled.jsonl"),
]
OUTPUT = Path("evidence/extraction/day_summary/regen_comparison.json")


def _extract_pairs_from_file(path: Path) -> list[dict]:
    with open(path) as f:
        cases = [json.loads(line) for line in f]

    by_trace = {}
    for c in cases:
        ec = c.get("eval_case", c)
        tid = ec["trace_id"]
        if tid not in by_trace:
            by_trace[tid] = []
        by_trace[tid].append(ec)

    pairs = []
    for tid, trace_cases in by_trace.items():
        days_seen = set()
        for c in sorted(
            trace_cases,
            key=lambda x: (-len(x.get("visible_discussion", [])), x["day"]),
        ):
            vis = c.get("visible_discussion", [])
            if len(vis) >= 5 and c["day"] not in days_seen:
                days_seen.add(c["day"])
                old_summary = None
                for c2 in trace_cases:
                    if c2["day"] > c["day"]:
                        for s in c2["private_context"].get("day_summaries", []):
                            if s["day"] == c["day"] and s["summary"].startswith(
                                "Key accusations"
                            ):
                                old_summary = s["summary"]
                                break
                    if old_summary:
                        break
                pairs.append(
                    {
                        "pair_id": f"{tid[:8]}_day{c['day']}",
                        "trace_id": tid,
                        "day": c["day"],
                        "raw_discussion": vis,
                        "old_summary": old_summary,
                    }
                )
    return pairs


def load_pairs() -> list[dict]:
    all_pairs = []
    seen_ids = set()
    for path in EVAL_SETS:
        for p in _extract_pairs_from_file(path):
            if p["pair_id"] not in seen_ids:
                seen_ids.add(p["pair_id"])
                all_pairs.append(p)
    return sorted(all_pairs, key=lambda p: p["pair_id"])


def generate_summary(raw_discussion: list[dict], day: int) -> str:
    from Agents.agents import get_llm

    messages = [
        DayChannel(
            day=msg.get("day", day),
            round=msg.get("round", 1),
            player=msg["player"],
            message=msg["message"],
        )
        for msg in raw_discussion
    ]

    prompt = DAY_SUMMARY_PROMPT.format(
        current_day=day,
        day_channel=format_day_channel(messages),
        situation_standards=SITUATION_STANDARDS,
    )

    from Agents.nodes import _serialize_day_summary

    result = get_llm().with_structured_output(DaySummaryOutput).invoke(prompt)
    return _serialize_day_summary(result)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pair", help="Only regenerate this pair ID")
    args = parser.parse_args()

    pairs = load_pairs()
    if args.pair:
        pairs = [p for p in pairs if p["pair_id"] == args.pair]
        if not pairs:
            print(f"Pair '{args.pair}' not found.")
            return

    results = []
    for p in pairs:
        print(f"\nGenerating summary for {p['pair_id']} ({len(p['raw_discussion'])} messages)...")
        try:
            new_summary = generate_summary(p["raw_discussion"], p["day"])
        except Exception as exc:
            print(f"  ERROR: {exc}")
            new_summary = f"[ERROR: {exc}]"

        result = {
            "pair_id": p["pair_id"],
            "day": p["day"],
            "message_count": len(p["raw_discussion"]),
            "old_summary": p["old_summary"],
            "new_summary": new_summary,
        }
        results.append(result)

        print(f"\n{'=' * 80}")
        print(f"PAIR: {p['pair_id']}")
        print(f"{'=' * 80}")
        if p["old_summary"]:
            print(f"\n--- OLD SUMMARY ---\n{p['old_summary']}")
        else:
            print("\n--- OLD SUMMARY ---\n[not available]")
        print(f"\n--- NEW SUMMARY ---\n{new_summary}")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(results, indent=2) + "\n")
    print(f"\nResults saved to {OUTPUT}")


if __name__ == "__main__":
    main()
