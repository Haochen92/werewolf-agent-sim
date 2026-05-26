"""Label auto-dedup dataset cases via LLM to create golden labels.

Reads an AutoDedupRecord JSONL dataset, runs the production dedup prompt
through a configurable LLM, and outputs a golden labels JSON file compatible
with eval_auto_dedup.py calibration.

Usage::

    poetry run python -m evaluation.experiments.auto_dedup_labeler \
        --dataset eval_sets/auto_dedup_v1_cross_game.jsonl \
        --output evidence/auto_dedup/cross_game_golden_labels.json \
        --model gemini-2.5-pro

    # Resume from a partial run (reads existing output and skips labeled cases)
    poetry run python -m evaluation.experiments.auto_dedup_labeler \
        --dataset eval_sets/auto_dedup_v1_cross_game.jsonl \
        --output evidence/auto_dedup/cross_game_golden_labels.json \
        --model gemini-2.5-pro --resume
"""

from __future__ import annotations

import argparse
import json
import logging
import time
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

from Agents.llm_factory import create_chat_model
from Agents.memory_deduplication import (
    ObservationDedupDecisionOutput,
    StrategyDedupDecisionOutput,
)
from Agents.prompts.dedup import OBSERVATION_DEDUP_PROMPT, STRATEGY_DEDUP_PROMPT
from Agents.prompts.standards import EPISTEMIC_STATUS_RULE, SITUATION_STANDARDS
from evaluation.core.settings import load_project_env
from evaluation.data.datasets import AutoDedupRecord, read_auto_dedup_dataset

load_project_env()
logger = logging.getLogger(__name__)


def _format_obs_candidates(candidates: list[dict]) -> str:
    if not candidates:
        return "(none)"
    lines = []
    for c in candidates:
        lines.append(
            f"[{c['candidate_number']}] Candidate: {c['candidate_number']}; "
            f"Key: {c.get('key', '')} "
            f"(similarity={c.get('similarity', 0):.3f}, "
            f"observed={c.get('observation_count', 1)}x)\n"
            f"    Situation: {c.get('situation', '')}\n"
            f"    Approach: {c.get('approach', '')}\n"
            f"    Outcome: {c.get('outcome', '')}"
        )
    return "\n\n".join(lines)


def _format_sp_candidates(candidates: list[dict]) -> str:
    if not candidates:
        return "(none)"
    lines = []
    for c in candidates:
        lines.append(
            f"[{c['candidate_number']}] Candidate: {c['candidate_number']}; "
            f"Key: {c.get('key', '')} "
            f"(similarity={c.get('similarity', 0):.3f}, "
            f"observed={c.get('observation_count', 1)}x)\n"
            f"    Action: {c.get('action', '')}\n"
            f"    Situation: {c.get('situation', '')}"
        )
    return "\n\n".join(lines)


def _build_prompt(record: AutoDedupRecord) -> str:
    entry = record.new_entry
    n_cands = len(record.candidates)

    if record.item_type == "observation":
        return OBSERVATION_DEDUP_PROMPT.format(
            new_role=record.perspective,
            new_situation=entry.get("situation", ""),
            new_approach=entry.get("approach", ""),
            new_outcome=entry.get("outcome", ""),
            total_similar_count=n_cands,
            top_n=n_cands,
            existing_entries=_format_obs_candidates(record.candidates),
        )
    else:
        return STRATEGY_DEDUP_PROMPT.format(
            situation_standards=SITUATION_STANDARDS,
            epistemic_status_rule=EPISTEMIC_STATUS_RULE,
            new_role=record.perspective,
            new_situation=entry.get("situation", ""),
            new_action=entry.get("action", ""),
            total_similar_count=n_cands,
            top_n=n_cands,
            existing_entries=_format_sp_candidates(record.candidates),
        )


def _label_one(
    llm,
    record: AutoDedupRecord,
    max_retries: int = 2,
) -> tuple[str, dict[str, Any] | None] | None:
    prompt = _build_prompt(record)
    schema = (
        ObservationDedupDecisionOutput
        if record.item_type == "observation"
        else StrategyDedupDecisionOutput
    )

    for attempt in range(max_retries + 1):
        try:
            result = llm.with_structured_output(schema).invoke(
                [{"role": "user", "content": prompt}],
                config={"run_name": f"auto_dedup_label_{record.item_type}"},
            )
            if isinstance(result, dict):
                result = schema.model_validate(result)
            decision = result.result
            letter = decision.decision[0].upper()
            detail = decision.model_dump(mode="json")
            return letter, detail
        except Exception as exc:
            logger.warning("Attempt %d failed for case %d: %s", attempt + 1, record.case_index, exc)
            if attempt < max_retries:
                time.sleep(2)

    return None


def _load_existing_labels(path: Path) -> dict:
    if not path.exists():
        return {}
    with path.open() as f:
        data = json.load(f)
    return {label["case_index"]: label for label in data.get("labels", [])}


def label_dataset(
    records: list[AutoDedupRecord],
    model: str,
    output_path: Path,
    resume: bool = False,
    sleep_seconds: float = 1.0,
    max_retries: int = 2,
    max_cases: int = 0,
    thinking_mode: str | None = None,
) -> None:
    existing_labels: dict[int, dict] = {}
    if resume:
        existing_labels = _load_existing_labels(output_path)
        if existing_labels:
            print(f"Resuming: {len(existing_labels)} cases already labeled")

    llm_kwargs: dict[str, Any] = {}
    if thinking_mode:
        llm_kwargs["model_kwargs"] = {"thinking_config": {"mode": thinking_mode}}
    llm = create_chat_model(model, temperature=0.0, **llm_kwargs)

    if max_cases:
        records = records[:max_cases]

    labels: list[dict] = list(existing_labels.values())
    counts: Counter[str] = Counter(l["golden_label"] for l in labels)
    failures = 0

    for i, record in enumerate(records, 1):
        if record.case_index in existing_labels:
            print(
                f"[{i}/{len(records)}] SKIP case={record.case_index} "
                f"(already labeled: {existing_labels[record.case_index]['golden_label']})"
            )
            continue

        result = _label_one(llm, record, max_retries=max_retries)

        if result is None:
            print(f"[{i}/{len(records)}] FAIL case={record.case_index} {record.item_type}")
            failures += 1
            continue

        letter, detail = result
        label_entry: dict[str, Any] = {
            "case_index": record.case_index,
            "item_type": record.item_type,
            "golden_label": letter,
        }
        if letter == "D" and detail:
            cand_num = detail.get("duplicate_of_candidate")
            if cand_num is not None:
                label_entry["duplicate_of_candidate"] = cand_num
        if detail:
            label_entry["reasoning"] = detail.get("reasoning", "")

        labels.append(label_entry)
        existing_labels[record.case_index] = label_entry
        counts[letter] += 1

        print(
            f"[{i}/{len(records)}] {letter} case={record.case_index} "
            f"{record.item_type:16s} {record.perspective}/{record.action_phase} "
            f"sit_sim={record.situation_sim:.3f}"
        )

        _save_golden(output_path, labels, records[0].eval_set_id, model)

        if i < len(records):
            time.sleep(sleep_seconds)

    _save_golden(output_path, labels, records[0].eval_set_id, model)

    print(f"\nLabeled {len(labels)} cases ({failures} failures)")
    print(f"Distribution: {dict(counts.most_common())}")
    print(f"Saved to {output_path}")


def _save_golden(
    path: Path,
    labels: list[dict],
    eval_set_id: str,
    model: str,
) -> None:
    sorted_labels = sorted(labels, key=lambda x: x["case_index"])
    counts = Counter(l["golden_label"] for l in sorted_labels)

    golden = {
        "eval_set_id": eval_set_id,
        "created_at": datetime.now().isoformat(),
        "labeler": f"LLM:{model}",
        "description": f"Auto-labeled by {model} using production dedup prompts",
        "label_schema": {
            "D": "DISCARD - duplicate of an existing candidate",
            "K": "KEEP - distinct, keep as a new entry",
        },
        "summary": ", ".join(f"{k}={v}" for k, v in counts.most_common()),
        "labels": sorted_labels,
    }

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        json.dump(golden, f, indent=2)
        f.write("\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Label auto-dedup dataset cases via LLM."
    )
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--model", type=str, default="gemini-2.5-pro")
    parser.add_argument("--max-cases", type=int, default=0)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--sleep-seconds", type=float, default=1.0)
    parser.add_argument("--max-retries", type=int, default=2)
    parser.add_argument("--thinking-mode", type=str, default=None)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    records = read_auto_dedup_dataset(args.dataset)
    print(f"Loaded {len(records)} cases from {args.dataset}")
    print(f"Model: {args.model}")
    if args.thinking_mode:
        print(f"Thinking: {args.thinking_mode}")
    print(f"Output: {args.output}")
    print()

    label_dataset(
        records=records,
        model=args.model,
        output_path=args.output,
        resume=args.resume,
        sleep_seconds=args.sleep_seconds,
        max_retries=args.max_retries,
        max_cases=args.max_cases,
        thinking_mode=args.thinking_mode,
    )


if __name__ == "__main__":
    main()
