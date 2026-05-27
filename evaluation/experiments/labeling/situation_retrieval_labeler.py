"""Golden-label tool for situation summary retrieval evaluation.

Supports the co-labeling workflow:
1. **show**: Display a case's game state (exactly what the situation summary sees)
2. **retrieve**: Run retrieval with given situations against the store, display results
3. **label**: Record golden situations and graded relevance labels for retrieved memories
4. **sample**: Select a balanced subset of cases for labeling
5. **progress**: Show labeling progress

Usage::

    # Show game state for a case (what the situation summary model sees)
    poetry run python -m evaluation.experiments.labeling.situation_retrieval_labeler \
        show --case-index 0

    # Show game state with the pipeline-captured situations for comparison
    poetry run python -m evaluation.experiments.labeling.situation_retrieval_labeler \
        show --case-index 0 --show-captured

    # Run retrieval with custom situations and display candidates for labeling
    poetry run python -m evaluation.experiments.labeling.situation_retrieval_labeler \
        retrieve --case-index 0 \
        --situations "situation 1" "situation 2"

    # Retrieve using the pipeline-captured situations (for baseline comparison)
    poetry run python -m evaluation.experiments.labeling.situation_retrieval_labeler \
        retrieve --case-index 0 --use-captured

    # Sample cases for labeling (balanced across roles)
    poetry run python -m evaluation.experiments.labeling.situation_retrieval_labeler \
        sample --count 20

    # Show labeling progress
    poetry run python -m evaluation.experiments.labeling.situation_retrieval_labeler \
        progress
"""

from __future__ import annotations

import argparse
import json
import random
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

from Agents.formatters import (
    format_day_channel_for_day,
    format_day_summaries,
    format_investigator_results,
    format_wolf_channel,
)
from Agents.memory import (
    retrieve_observations_for_agent,
    retrieve_strategy_points_for_agent,
)
from Agents.memory_persistence import seed_memory_from_json_files
from Agents.prompts import SITUATION_ROLE_LENS, SITUATION_STANDARDS
from Agents.schemas.evaluation import EvalCase
from evaluation.core.settings import REPO_ROOT
from evaluation.data.datasets import EvalDatasetRecord, read_eval_dataset

EVAL_DATASET = REPO_ROOT / "eval_sets" / "v4_filtering_eval.jsonl"
STORE_DIR = REPO_ROOT / "Agents" / "memory_stores" / "v4_deduped_v2"
GOLDEN_LABELS_PATH = (
    REPO_ROOT
    / "evidence"
    / "extraction"
    / "situation_summary"
    / "retrieval_golden_labels.json"
)

_store_seeded = False


def _ensure_store():
    global _store_seeded
    if _store_seeded:
        return
    from Agents.memory import store

    seed_memory_from_json_files(
        observations_path=STORE_DIR / "observations.json",
        strategy_points_path=STORE_DIR / "strategy_points.json",
        target_store=store,
    )
    _store_seeded = True


def load_records() -> list[EvalDatasetRecord]:
    return read_eval_dataset(EVAL_DATASET)


def _compute_sha256(path: Path) -> str:
    import hashlib

    return hashlib.sha256(path.read_bytes()).hexdigest()[:12]


def load_labels() -> dict:
    if not GOLDEN_LABELS_PATH.exists():
        return {
            "eval_set_id": "situation_retrieval_golden_v1",
            "created_at": datetime.now().isoformat(),
            "labeler": "human+claude",
            "description": (
                "Golden labels for situation summary retrieval evaluation. "
                "Contains golden situation queries and graded relevance labels "
                "for retrieved memories."
            ),
            "frozen_artifacts": {
                "dataset": {
                    "path": "eval_sets/v4_filtering_eval.jsonl",
                    "sha256": _compute_sha256(EVAL_DATASET),
                    "cases": 40,
                },
                "memory_store": {
                    "path": "Agents/memory_stores/v4_deduped_v2/",
                    "observations_sha256": _compute_sha256(
                        STORE_DIR / "observations.json"
                    ),
                    "strategy_points_sha256": _compute_sha256(
                        STORE_DIR / "strategy_points.json"
                    ),
                    "observations_count": 194,
                    "strategy_points_count": 205,
                },
            },
            "label_schema": {
                "situation_quality": "Human-written or validated golden situation queries",
                "relevance": {
                    "2": "Highly relevant — directly addresses the game dynamic",
                    "1": "Partially relevant — related but different angle/phase/specificity",
                    "0": "Not relevant — different situation entirely",
                },
            },
            "labels": [],
        }
    with open(GOLDEN_LABELS_PATH) as f:
        return json.load(f)


def save_labels(labels: dict) -> None:
    GOLDEN_LABELS_PATH.parent.mkdir(parents=True, exist_ok=True)
    labels_sorted = sorted(labels["labels"], key=lambda x: x["case_index"])
    labels["labels"] = labels_sorted
    with open(GOLDEN_LABELS_PATH, "w") as f:
        json.dump(labels, f, indent=2)
        f.write("\n")


# ---------------------------------------------------------------------------
# Display helpers
# ---------------------------------------------------------------------------

def format_game_state(record: EvalDatasetRecord) -> str:
    """Render the game state exactly as the situation summary prompt sees it."""
    case = record.eval_case
    private = case.private_context
    role = case.player_role

    lines = []
    lines.append(f"{'=' * 80}")
    lines.append(
        f"CASE {record.case_id} | {role} | day {case.day} round {case.round} | "
        f"{case.action_phase}"
    )
    lines.append(f"{'=' * 80}")
    lines.append("")

    lines.append(f"Role: {role}")
    lines.append(f"Day: {case.day}, Round: {case.round}")
    lines.append("")

    if role == "wolf":
        lines.append(
            f"Surviving villagers: {', '.join(private.surviving_villagers)}"
        )
        lines.append(
            f"Known surviving wolf allies: {', '.join(private.surviving_wolves)}"
        )
    else:
        lines.append(f"Surviving players: {', '.join(private.surviving_players)}")
    lines.append("")

    day_summaries = format_day_summaries(private.day_summaries, before_day=case.day)
    lines.append("--- Previous days summary ---")
    lines.append(day_summaries)
    lines.append("")

    day_channel = format_day_channel_for_day(case.visible_discussion, case.day)
    lines.append("--- Today's public discussion ---")
    lines.append(day_channel)
    lines.append("")

    if role == "wolf":
        wolf_channel = format_wolf_channel(private.wolf_channel)
        lines.append("--- Wolf night chat ---")
        lines.append(wolf_channel)
        lines.append("")

    if role == "investigator":
        inv_results = format_investigator_results(private.investigator_results)
        lines.append("--- Your private investigation results ---")
        lines.append(inv_results)
        lines.append("")

    lines.append("--- Strategy note ---")
    lines.append(private.previous_strategy or "(none)")
    lines.append("")

    lines.append("--- Situation standards (shared) ---")
    lines.append(SITUATION_STANDARDS.strip())
    lines.append("")

    role_lens = SITUATION_ROLE_LENS.get(role, "")
    if role_lens:
        lines.append("--- Role-specific lens ---")
        lines.append(role_lens)
        lines.append("")

    return "\n".join(lines)


def format_captured_situations(case: EvalCase) -> str:
    """Show the pipeline-captured situations for comparison."""
    if not case.situations:
        return "(no captured situations)"
    lines = ["--- Pipeline-captured situations ---"]
    for i, sit in enumerate(case.situations, 1):
        lines.append(f"  [{i}] {sit}")
    return "\n".join(lines)


def format_retrieved_items(
    observations: list,
    strategy_points: list,
) -> str:
    """Format retrieved items for labeling review."""
    lines = []

    if observations:
        lines.append("--- Retrieved Observations ---")
        for i, item in enumerate(observations, 1):
            obs = item.observation
            lines.append(f"  [{i}] key={item.key}  score={item.score:.4f}")
            lines.append(f"      Matched situation: {item.matched_situation[:80]}...")
            lines.append(f"      SITUATION:  {obs.situation}")
            if obs.approach:
                lines.append(f"      APPROACH:   {obs.approach}")
            if obs.outcome:
                lines.append(f"      OUTCOME:    {obs.outcome}")
            lines.append(f"      (observed {obs.observation_count}x)")
            lines.append("")
    else:
        lines.append("--- Retrieved Observations ---")
        lines.append("  (none)")
        lines.append("")

    if strategy_points:
        lines.append("--- Retrieved Strategy Points ---")
        for i, item in enumerate(strategy_points, 1):
            sp = item.strategy_point
            lines.append(f"  [{i}] key={item.key}  score={item.score:.4f}")
            lines.append(f"      Matched situation: {item.matched_situation[:80]}...")
            lines.append(f"      SITUATION:  {sp.situation}")
            lines.append(f"      ACTION:     {sp.action}")
            lines.append(f"      (observed {sp.observation_count}x)")
            lines.append("")
    else:
        lines.append("--- Retrieved Strategy Points ---")
        lines.append("  (none)")
        lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_show(records: list[EvalDatasetRecord], args: argparse.Namespace) -> None:
    record = records[args.case_index]
    print(format_game_state(record))

    if args.show_captured:
        print(format_captured_situations(record.eval_case))
        print()


def _serialize_retrieved(
    observations: list,
    strategy_points: list,
) -> dict[str, list[dict[str, Any]]]:
    """Serialize retrieved items into a dict for staging/labeling."""
    obs_list = []
    for item in observations:
        obs = item.observation
        obs_list.append({
            "key": item.key,
            "score": round(item.score, 4) if item.score else 0.0,
            "matched_situation": item.matched_situation,
            "situation": obs.situation,
            "approach": obs.approach or "",
            "outcome": obs.outcome or "",
            "observation_count": obs.observation_count,
        })
    sp_list = []
    for item in strategy_points:
        sp = item.strategy_point
        sp_list.append({
            "key": item.key,
            "score": round(item.score, 4) if item.score else 0.0,
            "matched_situation": item.matched_situation,
            "situation": sp.situation,
            "action": sp.action,
            "observation_count": sp.observation_count,
        })
    return {"observations": obs_list, "strategy_points": sp_list}


def cmd_retrieve(
    records: list[EvalDatasetRecord], args: argparse.Namespace
) -> None:
    from Agents.memory import store

    _ensure_store()
    record = records[args.case_index]
    case = record.eval_case

    if args.use_captured:
        situations = list(case.situations)
        print("Using pipeline-captured situations:")
    else:
        situations = list(args.situations)
        print("Using provided situations:")

    for i, sit in enumerate(situations, 1):
        print(f"  [{i}] {sit}")
    print()

    top_k = args.top_k

    observations = retrieve_observations_for_agent(
        store=store,
        role=case.player_role,
        action_phase=case.action_phase,
        situations=situations,
        top_k=top_k,
    )
    observations.sort(key=lambda x: x.score or 0, reverse=True)

    strategy_points = retrieve_strategy_points_for_agent(
        store=store,
        role=case.player_role,
        action_phase=case.action_phase,
        situations=situations,
        top_k=top_k,
    )
    strategy_points.sort(key=lambda x: x.score or 0, reverse=True)

    print(format_retrieved_items(observations, strategy_points))
    print(f"Total: {len(observations)} observations, {len(strategy_points)} strategy points")


def cmd_sample(
    records: list[EvalDatasetRecord], args: argparse.Namespace
) -> None:
    count = args.count
    seed = args.seed
    rng = random.Random(seed)

    by_role: dict[str, list[int]] = {}
    for i, rec in enumerate(records):
        by_role.setdefault(rec.player_role, []).append(i)

    per_role = max(1, count // len(by_role))
    remainder = count - per_role * len(by_role)

    selected: list[int] = []
    for role in sorted(by_role.keys()):
        indices = by_role[role]
        rng.shuffle(indices)
        n = per_role + (1 if remainder > 0 else 0)
        if remainder > 0:
            remainder -= 1
        selected.extend(indices[:n])

    selected.sort()

    print(f"Selected {len(selected)} cases (seed={seed}):\n")
    for idx in selected:
        rec = records[idx]
        print(
            f"  [{idx:2d}] {rec.player_role:13s} day={rec.eval_case.day} "
            f"round={rec.eval_case.round} {rec.eval_case.action_phase}"
        )

    role_counts = Counter(records[i].player_role for i in selected)
    phase_counts = Counter(records[i].eval_case.action_phase for i in selected)
    print(f"\nRoles: {dict(role_counts)}")
    print(f"Phases: {dict(phase_counts)}")


def cmd_label(
    records: list[EvalDatasetRecord], args: argparse.Namespace
) -> None:
    """Record golden situations and retrieval relevance labels for a case.

    Accepts a JSON file with the structure::

        {
            "golden_situations": ["situation 1", "situation 2"],
            "observation_labels": [
                {"key": "uuid", "relevance": 2, "situation": "...", "approach": "...", "outcome": "..."},
                ...
            ],
            "strategy_labels": [
                {"key": "uuid", "relevance": 1, "situation": "...", "action": "..."},
                ...
            ],
            "notes": "optional notes"
        }

    The memory text fields (situation, approach, outcome, action) are stored
    alongside the key and relevance score so the golden labels file is
    self-contained and auditable without cross-referencing the store.
    """
    labels = load_labels()
    record = records[args.case_index]
    case = record.eval_case

    with open(args.labels_file) as f:
        label_data = json.load(f)

    golden_situations = label_data.get("golden_situations", [])
    if not golden_situations:
        print("ERROR: golden_situations required in labels file")
        return

    observation_labels = label_data.get("observation_labels", [])
    strategy_labels = label_data.get("strategy_labels", [])

    label_entry = {
        "case_index": args.case_index,
        "case_id": record.case_id,
        "player_role": case.player_role,
        "day": case.day,
        "round": case.round,
        "action_phase": case.action_phase,
        "captured_situations": list(case.situations),
        "golden_situations": golden_situations,
        "observation_labels": observation_labels,
        "strategy_labels": strategy_labels,
        "notes": label_data.get("notes", ""),
    }

    existing_ids = {l["case_index"] for l in labels["labels"]}
    if args.case_index in existing_ids:
        labels["labels"] = [
            l for l in labels["labels"] if l["case_index"] != args.case_index
        ]
        print(f"Replacing existing label for case {args.case_index}")

    labels["labels"].append(label_entry)
    save_labels(labels)

    rel_dist = Counter(
        ol["relevance"] for ol in observation_labels + strategy_labels
    )
    print(f"Saved label for case {args.case_index} ({case.player_role} "
          f"day={case.day} round={case.round})")
    print(f"  Golden situations: {len(golden_situations)}")
    print(f"  Observation labels: {len(observation_labels)}")
    print(f"  Strategy labels: {len(strategy_labels)}")
    print(f"  Relevance distribution: {dict(sorted(rel_dist.items()))}")
    print(f"  Saved to {GOLDEN_LABELS_PATH}")


def cmd_progress(
    records: list[EvalDatasetRecord], _args: argparse.Namespace
) -> None:
    labels = load_labels()
    labeled_indices = {l["case_index"] for l in labels["labels"]}

    print(f"Labeled: {len(labeled_indices)}/{len(records)} cases")
    print()

    role_done: Counter[str] = Counter()
    role_total: Counter[str] = Counter()
    for i, rec in enumerate(records):
        role_total[rec.player_role] += 1
        if i in labeled_indices:
            role_done[rec.player_role] += 1

    print("Per-role progress:")
    for role in sorted(role_total.keys()):
        print(f"  {role:13s}: {role_done[role]}/{role_total[role]}")
    print()

    total_obs_labels = sum(
        len(l.get("observation_labels", [])) for l in labels["labels"]
    )
    total_strat_labels = sum(
        len(l.get("strategy_labels", [])) for l in labels["labels"]
    )
    print(f"Total relevance labels: {total_obs_labels} obs + {total_strat_labels} strat")
    print()

    if labels["labels"]:
        all_obs_scores = [
            ol["relevance"]
            for l in labels["labels"]
            for ol in l.get("observation_labels", [])
        ]
        all_strat_scores = [
            sl["relevance"]
            for l in labels["labels"]
            for sl in l.get("strategy_labels", [])
        ]
        if all_obs_scores:
            dist = Counter(all_obs_scores)
            print(f"Observation relevance distribution: {dict(sorted(dist.items()))}")
        if all_strat_scores:
            dist = Counter(all_strat_scores)
            print(f"Strategy relevance distribution: {dict(sorted(dist.items()))}")
        print()

    for i, rec in enumerate(records):
        status = "DONE" if i in labeled_indices else "    "
        case = rec.eval_case
        print(
            f"  [{status}] {i:2d}: {rec.player_role:13s} "
            f"day={case.day} r={case.round} {case.action_phase}"
        )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Golden-label tool for situation summary retrieval evaluation."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # show
    show = sub.add_parser(
        "show", help="Display game state for a case (what the model sees)"
    )
    show.add_argument("--case-index", type=int, required=True)
    show.add_argument(
        "--show-captured",
        action="store_true",
        help="Also show pipeline-captured situations",
    )

    # retrieve
    retrieve = sub.add_parser(
        "retrieve",
        help="Run retrieval with situations and display candidates",
    )
    retrieve.add_argument("--case-index", type=int, required=True)
    retrieve.add_argument(
        "--situations",
        nargs="+",
        help="Situation queries to use for retrieval",
    )
    retrieve.add_argument(
        "--use-captured",
        action="store_true",
        help="Use the pipeline-captured situations instead",
    )
    retrieve.add_argument("--top-k", type=int, default=10)

    # label
    label = sub.add_parser(
        "label", help="Record golden labels from a JSON file"
    )
    label.add_argument("--case-index", type=int, required=True)
    label.add_argument(
        "--labels-file",
        type=Path,
        required=True,
        help="Path to JSON file with golden_situations and relevance labels",
    )

    # sample
    samp = sub.add_parser("sample", help="Sample cases for labeling")
    samp.add_argument("--count", type=int, default=20)
    samp.add_argument("--seed", type=int, default=42)

    # progress
    sub.add_parser("progress", help="Show labeling progress")

    return parser.parse_args()


def main() -> None:
    args = parse_args()
    records = load_records()
    print(f"Loaded {len(records)} cases from {EVAL_DATASET.name}")
    print()

    if args.command == "show":
        cmd_show(records, args)
    elif args.command == "retrieve":
        cmd_retrieve(records, args)
    elif args.command == "label":
        cmd_label(records, args)
    elif args.command == "sample":
        cmd_sample(records, args)
    elif args.command == "progress":
        cmd_progress(records, args)


if __name__ == "__main__":
    main()
