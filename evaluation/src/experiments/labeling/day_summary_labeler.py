"""Day summary quality labeler.

Pairs raw day discussion transcripts with their generated summaries from
the eval set, then supports qualitative labeling against the SITUATION_STANDARDS
dimensions and downstream consumer needs.

Usage:
    poetry run python evaluation/experiments/labeling/day_summary_labeler.py pairs
    poetry run python evaluation/experiments/labeling/day_summary_labeler.py show <pair_id>
    poetry run python evaluation/experiments/labeling/day_summary_labeler.py label <pair_id>
    poetry run python evaluation/experiments/labeling/day_summary_labeler.py progress
"""

import argparse
import json
import sys
from pathlib import Path
from textwrap import dedent

EVAL_SET = Path("eval_sets/v4_filtering_eval.jsonl")
LABELS_OUTPUT = Path("evidence/extraction/day_summary/quality_labels.json")

INFORMATION_CATEGORIES = [
    "accusations_and_reasoning",
    "defenses",
    "role_claims_and_evidence",
    "alliances_and_blocs",
    "tone_shifts_and_pressure_dynamics",
    "information_landscape_signals",
    "consensus_texture_signals",
    "agent_exposure_signals",
    "voting_pattern_references",
    "multi_day_causal_chains",
]

CATEGORY_DESCRIPTIONS = {
    "accusations_and_reasoning": "Who accused whom and the specific reasoning (covered by current prompt)",
    "defenses": "How accused players responded (covered by current prompt)",
    "role_claims_and_evidence": "Role reveals and their substantiation (covered by current prompt)",
    "alliances_and_blocs": "Alliances or voting blocs that formed (covered by current prompt)",
    "tone_shifts_and_pressure_dynamics": "Shifts in aggression, sudden piling-on, suspicion escalation/de-escalation",
    "information_landscape_signals": "What TYPE of evidence is driving suspicion — voting records, communication style, behavioral patterns, or concrete claims",
    "consensus_texture_signals": "Village alignment — unified/fragile/split, evidence-driven vs social momentum",
    "agent_exposure_signals": "Who is under scrutiny, who is driving accusations, who is staying quiet",
    "voting_pattern_references": "References to past votes, voting consistency/inconsistency",
    "multi_day_causal_chains": "Links to prior day events that shape current dynamics",
}


def load_eval_cases():
    with open(EVAL_SET) as f:
        return [json.loads(line) for line in f]


def build_pairs(cases):
    """Build (raw_discussion, summary) pairs from cross-day eval cases.

    For each game trace, find days where:
    - A late-round case has the raw visible_discussion for day N
    - A day N+1 case carries the day N summary in day_summaries
    """
    by_trace = {}
    for i, case in enumerate(cases):
        ec = case["eval_case"]
        tid = ec["trace_id"]
        if tid not in by_trace:
            by_trace[tid] = []
        by_trace[tid].append({"idx": i, **ec})

    pairs = []
    for tid, trace_cases in by_trace.items():
        days_with_discussion = {}
        for c in trace_cases:
            vis = c.get("visible_discussion", [])
            if len(vis) >= 5:
                day = c["day"]
                if day not in days_with_discussion or len(vis) > len(
                    days_with_discussion[day]["visible_discussion"]
                ):
                    days_with_discussion[day] = c

        for c in trace_cases:
            summaries = c.get("private_context", {}).get("day_summaries", [])
            for s in summaries:
                sday = s["day"]
                summary_text = s["summary"].strip()
                if not summary_text.startswith("Key accusations"):
                    continue
                if sday in days_with_discussion:
                    raw = days_with_discussion[sday]
                    pair_id = f"{tid[:8]}_day{sday}"
                    if any(p["pair_id"] == pair_id for p in pairs):
                        continue
                    pairs.append(
                        {
                            "pair_id": pair_id,
                            "trace_id": tid,
                            "day": sday,
                            "raw_message_count": len(raw["visible_discussion"]),
                            "raw_discussion": raw["visible_discussion"],
                            "generated_summary": summary_text,
                        }
                    )

    return sorted(pairs, key=lambda p: p["pair_id"])


def load_labels():
    if LABELS_OUTPUT.exists():
        return json.loads(LABELS_OUTPUT.read_text())
    return {}


def save_labels(labels):
    LABELS_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    LABELS_OUTPUT.write_text(json.dumps(labels, indent=2) + "\n")


def cmd_pairs(args):
    cases = load_eval_cases()
    pairs = build_pairs(cases)
    labels = load_labels()

    print(f"Found {len(pairs)} transcript/summary pairs:\n")
    for p in pairs:
        status = "LABELED" if p["pair_id"] in labels else "unlabeled"
        print(
            f"  {p['pair_id']:20s}  day {p['day']}  "
            f"{p['raw_message_count']:2d} msgs  [{status}]"
        )


def cmd_show(args):
    cases = load_eval_cases()
    pairs = build_pairs(cases)
    pair = next((p for p in pairs if p["pair_id"] == args.pair_id), None)
    if not pair:
        print(f"Pair '{args.pair_id}' not found. Run 'pairs' to list available pairs.")
        sys.exit(1)

    print(f"{'=' * 80}")
    print(f"PAIR: {pair['pair_id']}  |  Trace: {pair['trace_id'][:12]}...  |  Day {pair['day']}")
    print(f"{'=' * 80}")

    print(f"\n--- RAW DISCUSSION ({pair['raw_message_count']} messages) ---\n")
    for msg in pair["raw_discussion"]:
        player = msg.get("player", "unknown")
        rnd = msg.get("round", "?")
        text = msg.get("message", "")
        print(f"  [Round {rnd}] {player}: {text}\n")

    print(f"\n--- GENERATED SUMMARY ---\n")
    print(f"  {pair['generated_summary']}\n")

    print(f"\n--- SITUATION STANDARDS DIMENSIONS (for reference) ---\n")
    print(
        dedent("""\
        Information landscape: Is the village information-rich or information-starved?
                               What TYPE of evidence is driving suspicion?
        Consensus texture:     How aligned is the village? Unified, fragile, split, or none?
                               Evidence-driven or social momentum?
        Agent exposure:        Who is driving the push, aligned with consensus, under scrutiny,
                               or the primary target? What is the basis?
        Game phase:            Early, mid, or endgame? What changed most recently?
    """)
    )

    print(f"--- DOWNSTREAM CONSUMERS ---\n")
    print(
        dedent("""\
        1. Agent decision prompts (all roles) — need to understand prior dynamics
           to make informed discussion/vote/night decisions
        2. Situation summary (query generation) — needs to characterize current game
           dynamics along SITUATION_STANDARDS dimensions for retrieval
        3. Post-game extraction — needs to reconstruct causal chains across days
    """)
    )


def cmd_label(args):
    cases = load_eval_cases()
    pairs = build_pairs(cases)
    pair = next((p for p in pairs if p["pair_id"] == args.pair_id), None)
    if not pair:
        print(f"Pair '{args.pair_id}' not found.")
        sys.exit(1)

    labels = load_labels()

    cmd_show(args)

    print(f"\n{'=' * 80}")
    print("LABELING")
    print(f"{'=' * 80}\n")

    print("For each information category, rate whether the summary captures it:")
    print("  2 = fully captured (all relevant instances present and accurate)")
    print("  1 = partially captured (some instances present, or imprecise)")
    print("  0 = missing (relevant information exists in transcript but not in summary)")
    print("  n/a = not applicable (this category has no relevant content in the transcript)")
    print()

    label_data = {"pair_id": args.pair_id, "categories": {}, "notes": {}}

    for cat in INFORMATION_CATEGORIES:
        desc = CATEGORY_DESCRIPTIONS[cat]
        while True:
            score = input(f"  {cat}\n    ({desc})\n    Score [2/1/0/n]: ").strip().lower()
            if score in ("2", "1", "0", "n", "na", "n/a"):
                label_data["categories"][cat] = None if score.startswith("n") else int(score)
                break
            print("    Invalid input. Enter 2, 1, 0, or n.")

        note = input("    Note (optional, press Enter to skip): ").strip()
        if note:
            label_data["notes"][cat] = note
        print()

    print("\nOverall assessment:")
    overall = input(
        "  Would downstream consumers (agent decisions, situation summary, post-game extraction)\n"
        "  have enough information from this summary? [yes/partial/no]: "
    ).strip().lower()
    label_data["overall_sufficiency"] = overall

    missing = input(
        "\n  What's the most important missing information? (press Enter to skip): "
    ).strip()
    if missing:
        label_data["critical_gap"] = missing

    labels[args.pair_id] = label_data
    save_labels(labels)
    print(f"\nLabel saved to {LABELS_OUTPUT}")


def cmd_progress(args):
    cases = load_eval_cases()
    pairs = build_pairs(cases)
    labels = load_labels()

    total = len(pairs)
    labeled = sum(1 for p in pairs if p["pair_id"] in labels)

    print(f"Progress: {labeled}/{total} pairs labeled\n")

    if labels:
        cat_scores = {cat: [] for cat in INFORMATION_CATEGORIES}
        for label in labels.values():
            for cat, score in label.get("categories", {}).items():
                if score is not None:
                    cat_scores[cat].append(score)

        print("Category averages (across labeled pairs):\n")
        for cat in INFORMATION_CATEGORIES:
            scores = cat_scores.get(cat, [])
            if scores:
                avg = sum(scores) / len(scores)
                print(f"  {cat:40s}  avg={avg:.1f}  n={len(scores)}")
            else:
                print(f"  {cat:40s}  (no scores)")

        print()
        sufficiency = [l.get("overall_sufficiency", "") for l in labels.values()]
        for val in ["yes", "partial", "no"]:
            count = sufficiency.count(val)
            if count:
                print(f"  Overall sufficiency '{val}': {count}")

        gaps = [l["critical_gap"] for l in labels.values() if l.get("critical_gap")]
        if gaps:
            print("\n  Critical gaps identified:")
            for g in gaps:
                print(f"    - {g}")


def main():
    parser = argparse.ArgumentParser(description="Day summary quality labeler")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("pairs", help="List available transcript/summary pairs")

    show_p = sub.add_parser("show", help="Show a transcript/summary pair")
    show_p.add_argument("pair_id", help="Pair ID from 'pairs' command")

    label_p = sub.add_parser("label", help="Label a transcript/summary pair")
    label_p.add_argument("pair_id", help="Pair ID from 'pairs' command")

    sub.add_parser("progress", help="Show labeling progress and stats")

    args = parser.parse_args()

    if args.command == "pairs":
        cmd_pairs(args)
    elif args.command == "show":
        cmd_show(args)
    elif args.command == "label":
        cmd_label(args)
    elif args.command == "progress":
        cmd_progress(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
