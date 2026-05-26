"""Re-run extraction on frozen inputs with a different model.

Reads an existing extraction dataset, replays the extraction prompt through
a specified model, and writes a new dataset in the same
``ExtractionDatasetRecord`` format.  The output can be judged directly by
``extraction_eval.py`` with no adapter scripts.

Usage::

    poetry run python -m evaluation.experiments.extraction_replay \\
        --source eval_sets/extraction_v1.jsonl \\
        --model gemini-3.5-flash \\
        --max-games 10
"""

from __future__ import annotations

import argparse
import re
import time
from datetime import datetime
from logging import getLogger
from pathlib import Path

from Agents.llm_factory import create_chat_model

from Agents.extraction import build_extraction_prompt
from Agents.schemas import GameStrategyOutput
from Agents.schemas.evaluation import ExtractionCase
from evaluation.core.io import write_jsonl
from evaluation.core.settings import REPO_ROOT, load_project_env
from evaluation.data.datasets import read_extraction_dataset

load_project_env()
logger = getLogger(__name__)

PLAYER_ID_RE = re.compile(r"player_\d+")


def _make_llm(model: str, temperature: float = 0.0, **kwargs):
    return create_chat_model(model, temperature=temperature, **kwargs)


def _run_extraction(llm, prompt: str) -> GameStrategyOutput:
    result = llm.with_structured_output(GameStrategyOutput).invoke(prompt)
    if isinstance(result, GameStrategyOutput):
        return result
    if isinstance(result, dict):
        return GameStrategyOutput.model_validate(result)
    raise TypeError(f"Unexpected extraction result type: {type(result)!r}")


def _count_player_ids(items: list[dict]) -> int:
    import json

    return sum(1 for item in items if PLAYER_ID_RE.search(json.dumps(item)))


def _build_prompt_from_case(case: ExtractionCase) -> str:
    inputs = {
        "formatted_roles": "\n".join(
            f"{pid}: {role}" for pid, role in case.roles.items()
        ),
        "formatted_discussions": case.formatted_discussions,
        "formatted_strategy_notes": case.formatted_strategy_notes,
        "formatted_previous_strategies": (
            "No previous role strategy summaries."
        ),
        "game_outcome": case.game_outcome,
    }
    return build_extraction_prompt(inputs)


def output_path(args: argparse.Namespace, model: str) -> Path:
    if args.output:
        return Path(args.output)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_model = model.replace("/", "_").replace(".", "_")
    return REPO_ROOT / "eval_sets" / f"extraction_replay_{safe_model}_{timestamp}.jsonl"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Replay extraction with a different model."
    )
    parser.add_argument("--source", type=Path, required=True,
                        help="Source extraction dataset (JSONL).")
    parser.add_argument("--model", type=str, required=True,
                        help="Model to use for extraction replay.")
    parser.add_argument("--max-games", type=int, default=0,
                        help="Limit number of games (0 = all).")
    parser.add_argument("--start-offset", type=int, default=0,
                        help="Skip first N games.")
    parser.add_argument("--output", type=Path, default=None,
                        help="Output JSONL path (default: auto-named in eval_sets/).")
    parser.add_argument("--eval-set-id", type=str, default=None,
                        help="Override eval_set_id (default: replay_{model}).")
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--thinking-mode", type=str, default=None,
                        help="Thinking mode: off/minimal/low/medium/high/max.")
    parser.add_argument("--sleep-seconds", type=float, default=1.0)
    parser.add_argument("--max-retries", type=int, default=1)
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    all_records = read_extraction_dataset(args.source)
    records = all_records[args.start_offset:]
    if args.max_games:
        records = records[: args.max_games]

    llm_kwargs = {}
    if args.thinking_mode:
        llm_kwargs["model_kwargs"] = {
            "thinking_config": {"mode": args.thinking_mode}
        }
    llm = _make_llm(args.model, args.temperature, **llm_kwargs)

    eval_set_id = args.eval_set_id or f"replay_{args.model}"
    out = output_path(args, args.model)

    print(f"Source: {args.source} ({len(all_records)} total)", flush=True)
    print(f"Model: {args.model}", flush=True)
    if args.thinking_mode:
        print(f"Thinking: {args.thinking_mode}", flush=True)
    print(f"Games: {len(records)} (offset={args.start_offset})", flush=True)
    print(f"Output: {out}", flush=True)
    print("", flush=True)

    total_obs, total_sp = 0, 0
    obs_with_ids, sp_with_ids = 0, 0
    written = 0

    for i, record in enumerate(records, 1):
        source_case = record.extraction_case
        prompt = _build_prompt_from_case(source_case)

        output = None
        for attempt in range(args.max_retries + 1):
            try:
                output = _run_extraction(llm, prompt)
                break
            except Exception as exc:
                logger.warning(
                    "Extraction failed attempt %d: %s", attempt + 1, exc
                )
                if attempt < args.max_retries:
                    time.sleep(2)

        if output is None:
            print(
                f"[{i}/{len(records)}] FAILED game={source_case.game_id[:8]}",
                flush=True,
            )
            continue

        obs = [o.model_dump(mode="json") for o in output.observations]
        sps = [s.model_dump(mode="json") for s in output.strategy_points]

        replayed_case = ExtractionCase(
            schema_version=source_case.schema_version,
            trace_id=source_case.trace_id,
            observation_id=source_case.observation_id,
            span_name=source_case.span_name,
            game_id=source_case.game_id,
            game_outcome=source_case.game_outcome,
            roles=source_case.roles,
            formatted_discussions=source_case.formatted_discussions,
            formatted_strategy_notes=source_case.formatted_strategy_notes,
            observations=obs,
            strategy_points=sps,
            model_used=args.model,
        )

        replayed_record = {
            "eval_set_id": eval_set_id,
            "case_id": record.case_id,
            "trace_id": record.trace_id,
            "observation_id": record.observation_id,
            "span_name": record.span_name,
            "game_id": source_case.game_id,
            "game_outcome": source_case.game_outcome,
            "created_from": f"replay of {args.source.name} with {args.model}",
            "extraction_case": replayed_case.model_dump(mode="json"),
        }
        write_jsonl(out, replayed_record)
        written += 1

        total_obs += len(obs)
        total_sp += len(sps)
        obs_with_ids += _count_player_ids(obs)
        sp_with_ids += _count_player_ids(sps)

        print(
            f"[{i}/{len(records)}] OK obs={len(obs)} sp={len(sps)} "
            f"game={source_case.game_id[:8]}",
            flush=True,
        )
        time.sleep(args.sleep_seconds)

    print(f"\nWrote {written} records to {out}", flush=True)
    print(f"Total observations: {total_obs}, strategy points: {total_sp}", flush=True)
    if total_obs:
        print(
            f"Player_ID leakage: obs={obs_with_ids}/{total_obs} "
            f"({100 * obs_with_ids / total_obs:.1f}%), "
            f"sp={sp_with_ids}/{total_sp} "
            f"({100 * sp_with_ids / total_sp:.1f}%)",
            flush=True,
        )


if __name__ == "__main__":
    main()
