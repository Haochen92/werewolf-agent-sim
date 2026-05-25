"""Re-run dedup decisions on frozen inputs with a different model.

Reads an existing dedup dataset, replays the dedup prompt through a specified
model, and writes a new dataset in the same ``DedupDatasetRecord`` format.
The output can be judged directly by ``dedup_eval.py``.

Usage::

    poetry run python -m evaluation.experiments.dedup_replay \\
        --source eval_sets/dedup_v1.jsonl \\
        --model gemini-3.5-flash \\
        --max-cases 15
"""

from __future__ import annotations

import argparse
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel

from Agents.memory_deduplication import (
    ObservationDedupDecisionOutput,
    StrategyDedupDecisionOutput,
)
from Agents.prompts.dedup import OBSERVATION_DEDUP_PROMPT, STRATEGY_DEDUP_PROMPT
from Agents.prompts.standards import EPISTEMIC_STATUS_RULE, SITUATION_STANDARDS
from Agents.schemas.evaluation import DedupCandidate, DedupCase
from evaluation.core.io import write_jsonl
from evaluation.core.settings import REPO_ROOT, load_project_env
from evaluation.data.datasets import read_dedup_dataset

load_project_env()
logger = logging.getLogger(__name__)


def _make_llm(model: str, temperature: float = 0.0, **kwargs):
    return ChatGoogleGenerativeAI(model=model, temperature=temperature, **kwargs)


# ---------------------------------------------------------------------------
# Prompt reconstruction from frozen DedupCase
# ---------------------------------------------------------------------------


def _format_candidates_for_observations(candidates: list[DedupCandidate]) -> str:
    if not candidates:
        return "(none)"
    lines = []
    for c in candidates:
        lines.append(
            f"[{c.candidate_number}] Candidate: {c.candidate_number}; "
            f"Key: {c.key} "
            f"(similarity={c.similarity:.3f}, "
            f"observed={c.observation_count}x)\n"
            f"    Situation: {c.situation}\n"
            f"    Approach: {c.approach or ''}\n"
            f"    Outcome: {c.outcome or ''}"
        )
    return "\n\n".join(lines)


def _format_candidates_for_strategy(candidates: list[DedupCandidate]) -> str:
    if not candidates:
        return "(none)"
    lines = []
    for c in candidates:
        lines.append(
            f"[{c.candidate_number}] Candidate: {c.candidate_number}; "
            f"Key: {c.key} "
            f"(similarity={c.similarity:.3f}, "
            f"observed={c.observation_count}x)\n"
            f"    Action: {c.action or ''}\n"
            f"    Situation: {c.situation}"
        )
    return "\n\n".join(lines)


def _build_observation_prompt(case: DedupCase) -> str:
    entry = case.new_entry
    return OBSERVATION_DEDUP_PROMPT.format(
        new_role=case.perspective,
        new_situation=entry.get("situation", ""),
        new_approach=entry.get("approach", ""),
        new_outcome=entry.get("outcome", ""),
        total_similar_count=len(case.candidates),
        top_n=len(case.candidates),
        existing_entries=_format_candidates_for_observations(case.candidates),
    )


def _build_strategy_prompt(case: DedupCase) -> str:
    entry = case.new_entry
    return STRATEGY_DEDUP_PROMPT.format(
        situation_standards=SITUATION_STANDARDS,
        epistemic_status_rule=EPISTEMIC_STATUS_RULE,
        new_role=case.perspective,
        new_situation=entry.get("situation", ""),
        new_action=entry.get("action", ""),
        total_similar_count=len(case.candidates),
        top_n=len(case.candidates),
        existing_entries=_format_candidates_for_strategy(case.candidates),
    )


def _output_schema_for(item_type: str) -> type[BaseModel]:
    if item_type == "observation":
        return ObservationDedupDecisionOutput
    return StrategyDedupDecisionOutput


# ---------------------------------------------------------------------------
# Run one replay
# ---------------------------------------------------------------------------


def _replay_dedup_decision(
    llm: ChatGoogleGenerativeAI,
    case: DedupCase,
    max_retries: int = 1,
) -> tuple[str, dict[str, Any] | None] | None:
    """Re-run a dedup decision and return (decision_letter, detail_dict)."""
    if case.item_type == "observation":
        prompt = _build_observation_prompt(case)
    else:
        prompt = _build_strategy_prompt(case)

    output_schema = _output_schema_for(case.item_type)

    for attempt in range(max_retries + 1):
        try:
            result = llm.with_structured_output(output_schema).invoke(
                [{"role": "user", "content": prompt}],
                config={"run_name": f"dedup_replay_{case.item_type}"},
            )
            if isinstance(result, dict):
                result = output_schema.model_validate(result)

            decision = result.result
            decision_letter = decision.decision[0].upper()
            detail = decision.model_dump(mode="json")
            return decision_letter, detail

        except Exception as exc:
            logger.warning(
                "Dedup replay failed attempt %d: %s", attempt + 1, exc
            )
            if attempt < max_retries:
                time.sleep(2)

    return None


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def output_path(args: argparse.Namespace, model: str) -> Path:
    if args.output:
        return Path(args.output)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_model = model.replace("/", "_").replace(".", "_")
    return REPO_ROOT / "eval_sets" / f"dedup_replay_{safe_model}_{timestamp}.jsonl"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Replay dedup decisions with a different model."
    )
    parser.add_argument("--source", type=Path, required=True,
                        help="Source dedup dataset (JSONL).")
    parser.add_argument("--model", type=str, required=True,
                        help="Model to use for dedup replay.")
    parser.add_argument("--max-cases", type=int, default=0,
                        help="Limit number of cases (0 = all).")
    parser.add_argument("--filter-auto", action="store_true",
                        help="Skip auto-discard cases (no LLM call in original).")
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--eval-set-id", type=str, default=None)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--thinking-mode", type=str, default=None,
                        help="Thinking mode: off/minimal/low/medium/high/max.")
    parser.add_argument("--sleep-seconds", type=float, default=1.0)
    parser.add_argument("--max-retries", type=int, default=1)
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    records = read_dedup_dataset(args.source)
    if args.filter_auto:
        records = [r for r in records if not r.auto]
    if args.max_cases:
        records = records[: args.max_cases]

    llm_kwargs: dict[str, Any] = {}
    if args.thinking_mode:
        llm_kwargs["model_kwargs"] = {
            "thinking_config": {"mode": args.thinking_mode}
        }
    llm = _make_llm(args.model, args.temperature, **llm_kwargs)

    eval_set_id = args.eval_set_id or f"dedup_replay_{args.model}"
    out = output_path(args, args.model)

    print(f"Source: {args.source} ({len(records)} cases)", flush=True)
    print(f"Model: {args.model}", flush=True)
    if args.thinking_mode:
        print(f"Thinking: {args.thinking_mode}", flush=True)
    print(f"Output: {out}", flush=True)
    print("", flush=True)

    from collections import Counter

    decision_counts: Counter[str] = Counter()
    written = 0

    for i, record in enumerate(records, 1):
        case = record.dedup_case
        result = _replay_dedup_decision(llm, case, max_retries=args.max_retries)

        if result is None:
            print(
                f"[{i}/{len(records)}] FAILED {case.item_type} "
                f"{case.perspective}/{case.action_phase}",
                flush=True,
            )
            continue

        decision_letter, detail = result
        decision_counts[decision_letter] += 1

        replayed_case = DedupCase(
            schema_version=case.schema_version,
            trace_id=case.trace_id,
            observation_id=case.observation_id,
            span_name=case.span_name,
            game_id=case.game_id,
            item_type=case.item_type,
            perspective=case.perspective,
            action_phase=case.action_phase,
            new_entry=case.new_entry,
            candidates=case.candidates,
            decision=decision_letter,
            decision_detail=detail,
            auto=False,
        )

        replayed_record = {
            "eval_set_id": eval_set_id,
            "case_id": record.case_id,
            "trace_id": record.trace_id,
            "observation_id": record.observation_id,
            "span_name": record.span_name,
            "game_id": case.game_id,
            "item_type": case.item_type,
            "perspective": case.perspective,
            "action_phase": case.action_phase,
            "decision": decision_letter,
            "auto": False,
            "created_from": f"replay of {args.source.name} with {args.model}",
            "dedup_case": replayed_case.model_dump(mode="json"),
        }
        write_jsonl(out, replayed_record)
        written += 1

        print(
            f"[{i}/{len(records)}] {decision_letter} "
            f"{case.item_type} {case.perspective}/{case.action_phase}",
            flush=True,
        )
        time.sleep(args.sleep_seconds)

    print(f"\nWrote {written} records to {out}", flush=True)
    if decision_counts:
        print("Decision distribution:", flush=True)
        for label, count in decision_counts.most_common():
            print(f"  {label}: {count}", flush=True)


if __name__ == "__main__":
    main()
