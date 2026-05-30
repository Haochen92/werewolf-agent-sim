"""Export candidates as a file for manual labeling in ChatGPT/Claude.

Renders the full game state (what the situation summary model sees) alongside
retrieved candidates, so the labeler has complete context.

Usage:
    # All 20 new cases into one file (with game context)
    poetry run python evidence/fine_tuning/cross_encoder/reranker/export_for_manual_labeling.py

    # Specific cases
    poetry run python evidence/fine_tuning/cross_encoder/reranker/export_for_manual_labeling.py \
        --cases 4 5 7

    # Per-case files
    poetry run python evidence/fine_tuning/cross_encoder/reranker/export_for_manual_labeling.py \
        --per-case
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
CANDIDATES_PATH = (
    REPO_ROOT / "evidence" / "fine_tuning" / "cross_encoder" / "reranker"
    / "candidates_for_labeling.json"
)
EVAL_DATASET = REPO_ROOT / "eval_sets" / "v4_filtering_eval.jsonl"
OUTPUT_DIR = REPO_ROOT / "evidence" / "fine_tuning" / "cross_encoder" / "reranker" / "labeling_prompts"

SYSTEM_INSTRUCTIONS = """\
You are labeling retrieval results for a werewolf social deduction game's episodic memory system.

A player in a specific game situation is retrieving past experiences from memory to inform their decision.
For each retrieved memory, rate how relevant it would be to recall in the current situation.

## Relevance Scale
- **2** (Highly relevant): Directly addresses the same game dynamic, information landscape, or strategic challenge. The player would clearly benefit from recalling this.
- **1** (Partially relevant): Related (similar role, overlapping themes, adjacent phase) but different angle or specificity. Useful background but not a direct match.
- **0** (Not relevant): Different situation entirely. Recalling it would not help.

## Key Factors
- Same type of strategic challenge? (voting record analysis, information-starved play, role exposure management)
- Comparable game phase? (early/mid/endgame)
- Same role dynamics?
- Would recalling this memory actually help the player decide what to do?

For EACH case below, read the game state and golden situation query, then rate every retrieved memory.
Respond with a JSON array per case containing objects with "key" (the 12-char prefix shown) and "relevance" (0/1/2).
"""


def _format_memory(item: dict, mem_type: str, idx: int) -> str:
    lines = [f"### Memory {idx} ({mem_type}) [key: {item['key'][:12]}] (score: {item['score']:.4f})"]
    lines.append(f"**Situation:** {item['situation']}")
    if mem_type == "observation":
        if item.get("approach"):
            lines.append(f"**Approach:** {item['approach']}")
        if item.get("outcome"):
            lines.append(f"**Outcome:** {item['outcome']}")
    else:
        if item.get("action"):
            lines.append(f"**Action:** {item['action']}")
    return "\n".join(lines)


def build_case_section(case: dict, game_state_text: str) -> str:
    lines = []
    lines.append(f"# Case {case['case_index']}: {case['player_role']} — {case['action_phase']} (day {case['day']} round {case['round']})")
    lines.append("")

    lines.append("## Game State (what the player sees)")
    lines.append("```")
    lines.append(game_state_text)
    lines.append("```")
    lines.append("")

    lines.append("## Golden Situation Query (what we're retrieving for)")
    lines.append("")
    for i, sit in enumerate(case["golden_situations"], 1):
        lines.append(f"**Situation {i}:** {sit}")
        lines.append("")

    lines.append("## Retrieved Memories to Label")
    lines.append("")

    all_items = []
    for obs in case["retrieved_observations"]:
        all_items.append(("observation", obs))
    for sp in case["retrieved_strategy_points"]:
        all_items.append(("strategy_point", sp))

    for idx, (mem_type, item) in enumerate(all_items, 1):
        lines.append(_format_memory(item, mem_type, idx))
        lines.append("")

    lines.append(f"## Response for Case {case['case_index']}")
    lines.append("")
    lines.append(f"Rate each of the {len(all_items)} memories above. JSON format:")
    lines.append("```json")
    labels = []
    for idx, (mem_type, item) in enumerate(all_items, 1):
        labels.append(f'  {{"idx": {idx}, "key": "{item["key"][:12]}", "type": "{mem_type}", "relevance": _}}')
    lines.append("[\n" + ",\n".join(labels) + "\n]")
    lines.append("```")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidates", type=Path, default=CANDIDATES_PATH)
    parser.add_argument("--eval-dataset", type=Path, default=EVAL_DATASET,
                        help="Eval dataset JSONL (must match candidate case indices)")
    parser.add_argument("--cases", type=int, nargs="*", help="Specific case indices")
    parser.add_argument("--per-case", action="store_true", help="One file per case")
    parser.add_argument("--batch-size", type=int, default=None,
                        help="Split into batches of N cases (for ChatGPT context limits)")
    args = parser.parse_args()

    with open(args.candidates) as f:
        data = json.load(f)

    from evaluation.data.datasets import read_eval_dataset
    from evaluation.experiments.labeling.situation_retrieval_labeler import format_game_state

    records = read_eval_dataset(args.eval_dataset)
    print(f"Loaded {len(records)} eval records")

    cases = data["cases"]
    if args.cases:
        cases = [c for c in cases if c["case_index"] in args.cases]

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    sections = []
    for case in cases:
        record = records[case["case_index"]]
        game_state = format_game_state(record)
        section = build_case_section(case, game_state)
        sections.append((case, section))

        if args.per_case:
            out = OUTPUT_DIR / f"case_{case['case_index']:02d}.md"
            out.write_text(SYSTEM_INSTRUCTIONS + "\n\n---\n\n" + section)
            n_items = len(case["retrieved_observations"]) + len(case["retrieved_strategy_points"])
            print(f"  Case {case['case_index']:2d}: {n_items} items → {out.name} ({out.stat().st_size/1024:.1f} KB)")

    if args.batch_size:
        for batch_idx in range(0, len(sections), args.batch_size):
            batch = sections[batch_idx:batch_idx + args.batch_size]
            batch_num = batch_idx // args.batch_size + 1
            case_ids = [c["case_index"] for c, _ in batch]
            batch_text = SYSTEM_INSTRUCTIONS + "\n\n---\n\n" + "\n\n---\n\n".join(s for _, s in batch)
            batch_path = OUTPUT_DIR / f"batch_{batch_num}_cases_{'_'.join(str(i) for i in case_ids)}.md"
            batch_path.write_text(batch_text)
            batch_items = sum(
                len(c["retrieved_observations"]) + len(c["retrieved_strategy_points"])
                for c, _ in batch
            )
            print(f"  Batch {batch_num}: {len(batch)} cases, {batch_items} items → {batch_path.name} ({batch_path.stat().st_size/1024:.1f} KB)")

    all_sections_text = [s for _, s in sections]
    combined = SYSTEM_INSTRUCTIONS + "\n\n---\n\n" + "\n\n---\n\n".join(all_sections_text)
    combined_path = OUTPUT_DIR / "all_cases_labeling.md"
    combined_path.write_text(combined)

    total_items = sum(
        len(c["retrieved_observations"]) + len(c["retrieved_strategy_points"])
        for c, _ in sections
    )
    print(f"\nCombined: {len(cases)} cases, {total_items} items → {combined_path}")
    print(f"  File size: {combined_path.stat().st_size / 1024:.1f} KB")


if __name__ == "__main__":
    main()
