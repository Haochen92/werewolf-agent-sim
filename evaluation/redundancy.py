from __future__ import annotations

import argparse
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.store.base import PutOp
from langgraph.store.memory import InMemoryStore
from pydantic import ValidationError

from evaluation.settings import REPO_ROOT, load_project_env

load_project_env()

from Agents.memory import (  # noqa: E402
    embeddings,
    retrieve_observations_for_agent,
    retrieve_strategy_points_for_agent,
)
from Agents.prompts.standards import SITUATION_STANDARDS  # noqa: E402
from evaluation.formatters import (  # noqa: E402
    format_eval_retrieved_observations,
    format_eval_retrieved_strategy_points,
)
from evaluation.langfuse_client import fetch_eval_cases  # noqa: E402
from evaluation.prompts import (  # noqa: E402
    REDUNDANCY_SYSTEM_PROMPT,
    REDUNDANCY_USER_PROMPT,
)
from Agents.schemas.evaluation import EvalCase  # noqa: E402
from evaluation.schemas import RedundancyScores  # noqa: E402


DEFAULT_JUDGE_MODEL = "gemini-2.5-pro"
DEFAULT_STORE_LOAD_BATCH_SIZE = 1


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_jsonl(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(record, sort_keys=True, default=str) + "\n")


def _message_content_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict):
                text = item.get("text") or item.get("content")
                if text:
                    parts.append(str(text))
            else:
                parts.append(str(item))
        return "\n".join(parts)
    return str(content)


def _strip_json_fences(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()


def _parse_redundancy_scores(text: str) -> RedundancyScores:
    payload = json.loads(_strip_json_fences(text))
    return RedundancyScores.model_validate(payload)


def build_store_from_snapshots(
    observations_path: Path,
    strategy_points_path: Path,
    batch_size: int = DEFAULT_STORE_LOAD_BATCH_SIZE,
) -> InMemoryStore:
    """Load snapshot entries directly, preserving exact JSON keys and values."""
    target_store = InMemoryStore(
        index={
            "dims": 1536,
            "embed": embeddings,
            "fields": ["content"],
        }
    )

    put_ops: list[PutOp] = []
    for path in (observations_path, strategy_points_path):
        payload = _read_json(path)
        for namespace_key, items in payload.get("namespaces", {}).items():
            namespace = tuple(namespace_key.split("/"))
            if len(namespace) != 2:
                continue
            for item in items:
                key = item.get("key")
                value = item.get("value", item)
                if key and value.get("content"):
                    put_ops.append(PutOp(namespace, key, value))

    print(
        f"  Indexing {len(put_ops)} memory items from "
        f"{observations_path.name} and {strategy_points_path.name}",
        flush=True,
    )
    for start in range(0, len(put_ops), batch_size):
        target_store.batch(put_ops[start : start + batch_size])
        indexed_count = min(start + batch_size, len(put_ops))
        if indexed_count == len(put_ops) or indexed_count % 25 == 0:
            print(f"    indexed {indexed_count}/{len(put_ops)} items", flush=True)

    return target_store


def read_eval_contexts(path: Path, max_samples: int | None) -> list[dict[str, Any]]:
    contexts: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    with path.open(encoding="utf-8") as file:
        for line_number, line in enumerate(file, 1):
            stripped = line.strip()
            if not stripped:
                continue
            record = json.loads(stripped)
            trace_id = record.get("trace_id")
            observation_id = record.get("observation_id")
            if not trace_id or not observation_id:
                raise ValueError(
                    f"Missing trace_id or observation_id on line {line_number} of {path}"
                )
            key = (trace_id, observation_id)
            if key in seen:
                continue
            seen.add(key)
            contexts.append(record)
            if max_samples is not None and len(contexts) >= max_samples:
                break
    return contexts


def fetch_matching_eval_case(
    trace_id: str,
    observation_id: str,
) -> EvalCase | None:
    for case in fetch_eval_cases(trace_id):
        if case.observation_id == observation_id:
            return case
    return None


def minimal_redundancy_scores(item_count: int) -> RedundancyScores:
    return RedundancyScores(
        redundancy_score=1,
        unique_idea_count=item_count,
        redundant_pairs=[],
        brief_reasoning=(
            "Fewer than two items were retrieved, so redundancy is not present."
        ),
    )


def run_redundancy_judge(
    *,
    item_type: str,
    situations: list[str],
    items_formatted: str,
    item_count: int,
    model: str,
) -> RedundancyScores | None:
    if item_count < 2:
        return minimal_redundancy_scores(item_count)

    prompt = REDUNDANCY_USER_PROMPT.format(
        item_type=item_type,
        situation_standards=SITUATION_STANDARDS,
        situations="\n".join(f"- {situation}" for situation in situations),
        items=items_formatted,
    )
    llm = ChatGoogleGenerativeAI(model=model, temperature=0.0)
    try:
        response = llm.invoke(
            [
                {"role": "system", "content": REDUNDANCY_SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ]
        )
        return _parse_redundancy_scores(_message_content_text(response.content))
    except (json.JSONDecodeError, ValidationError) as exc:
        print(f"  Redundancy judge returned invalid output: {exc}", flush=True)
        return None
    except Exception as exc:
        print(f"  Redundancy judge failed: {exc}", flush=True)
        return None


def parse_snapshot(raw: list[str]) -> tuple[str, Path, Path]:
    if len(raw) != 3:
        raise argparse.ArgumentTypeError(
            "--snapshot requires: LABEL OBSERVATIONS_JSON STRATEGY_POINTS_JSON"
        )
    label, observations_path, strategy_points_path = raw
    return label, Path(observations_path), Path(strategy_points_path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Replay retrieval queries from Langfuse spans against memory snapshots "
            "and optionally judge qualitative redundancy."
        )
    )
    parser.add_argument(
        "--eval-results",
        type=Path,
        required=True,
        help="JSONL eval output containing trace_id and observation_id fields.",
    )
    parser.add_argument(
        "--snapshot",
        nargs=3,
        action="append",
        metavar=("LABEL", "OBSERVATIONS_JSON", "STRATEGY_POINTS_JSON"),
        required=True,
        help=(
            "Memory snapshot to test. Can be passed multiple times, for example: "
            "--snapshot pre Agents/data/werewolf_observations_pre_dedup.json "
            "Agents/data/werewolf_strategy_points_pre_dedup.json"
        ),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="JSONL output path. Defaults to eval_results/redundancy_<timestamp>.jsonl.",
    )
    parser.add_argument(
        "--max-samples",
        type=int,
        default=0,
        help="Limit number of eval rows to replay. Use 0 for all rows.",
    )
    parser.add_argument(
        "--judge",
        action="store_true",
        help="Call the LLM redundancy judge. Without this, only replay retrieval.",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_JUDGE_MODEL,
        help=f"Judge model name (default: {DEFAULT_JUDGE_MODEL}).",
    )
    parser.add_argument(
        "--sleep-seconds",
        type=float,
        default=1.0,
        help="Delay between judge calls when --judge is used.",
    )
    args = parser.parse_args()
    if args.max_samples < 0:
        parser.error("--max-samples must be 0 or greater")
    return args


def output_path(requested: Path | None) -> Path:
    if requested:
        return requested
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return REPO_ROOT / "eval_results" / f"retrieval_redundancy_{timestamp}.jsonl"


def main() -> None:
    args = parse_args()
    contexts = read_eval_contexts(
        args.eval_results,
        max_samples=args.max_samples or None,
    )
    snapshots = [parse_snapshot(raw) for raw in args.snapshot]
    out_path = output_path(args.output)

    print(f"Loaded {len(contexts)} eval contexts from {args.eval_results}", flush=True)
    print(f"Testing {len(snapshots)} memory snapshot(s)", flush=True)
    print(f"Writing replay results to {out_path}", flush=True)

    stores: dict[str, InMemoryStore] = {}
    for label, observations_path, strategy_points_path in snapshots:
        print(f"Loading snapshot '{label}'", flush=True)
        stores[label] = build_store_from_snapshots(
            observations_path,
            strategy_points_path,
        )

    case_cache: dict[tuple[str, str], EvalCase | None] = {}
    written = 0
    for context_index, context in enumerate(contexts, 1):
        trace_id = context["trace_id"]
        observation_id = context["observation_id"]
        cache_key = (trace_id, observation_id)
        case = case_cache.get(cache_key)
        if cache_key not in case_cache:
            case = fetch_matching_eval_case(trace_id, observation_id)
            case_cache[cache_key] = case

        if not case:
            print(
                f"[{context_index}/{len(contexts)}] Missing eval case "
                f"{trace_id}:{observation_id}; skipping",
                flush=True,
            )
            continue

        role = case.player_role
        situations = case.situations
        if not role or not situations:
            print(
                f"[{context_index}/{len(contexts)}] Missing role or situations "
                f"for {trace_id}:{observation_id}; skipping",
                flush=True,
            )
            continue

        print(
            f"[{context_index}/{len(contexts)}] {case.span_name} "
            f"role={role} situations={len(situations)}",
            flush=True,
        )

        for label, store in stores.items():
            observations = retrieve_observations_for_agent(store, role, situations)
            strategy_points = retrieve_strategy_points_for_agent(store, role, situations)

            observation_scores = None
            strategy_point_scores = None
            if args.judge:
                observation_scores = run_redundancy_judge(
                    item_type="observations",
                    situations=situations,
                    items_formatted=format_eval_retrieved_observations(observations),
                    item_count=len(observations),
                    model=args.model,
                )
                time.sleep(args.sleep_seconds)
                strategy_point_scores = run_redundancy_judge(
                    item_type="strategy points",
                    situations=situations,
                    items_formatted=format_eval_retrieved_strategy_points(strategy_points),
                    item_count=len(strategy_points),
                    model=args.model,
                )
                time.sleep(args.sleep_seconds)

            record = {
                "snapshot": label,
                "source_eval_results": str(args.eval_results),
                "trace_id": trace_id,
                "observation_id": observation_id,
                "span_name": case.span_name,
                "role": role,
                "day": case.day,
                "round": case.round,
                "action_type": case.action_type,
                "situations": situations,
                "retrieved_observations": [
                    item.model_dump(mode="json") for item in observations
                ],
                "retrieved_strategy_points": [
                    item.model_dump(mode="json") for item in strategy_points
                ],
                "observation_redundancy": (
                    observation_scores.model_dump(mode="json")
                    if observation_scores
                    else None
                ),
                "strategy_point_redundancy": (
                    strategy_point_scores.model_dump(mode="json")
                    if strategy_point_scores
                    else None
                ),
                "judge_model": args.model if args.judge else None,
            }
            _write_jsonl(out_path, record)
            written += 1

            if args.judge:
                obs_score = (
                    observation_scores.redundancy_score
                    if observation_scores
                    else None
                )
                sp_score = (
                    strategy_point_scores.redundancy_score
                    if strategy_point_scores
                    else None
                )
                print(
                    f"  {label}: obs={len(observations)} red={obs_score}; "
                    f"strategy={len(strategy_points)} red={sp_score}",
                    flush=True,
                )
            else:
                print(
                    f"  {label}: obs={len(observations)} "
                    f"strategy={len(strategy_points)}",
                    flush=True,
                )

    print(f"Done. Wrote {written} records to {out_path}", flush=True)


if __name__ == "__main__":
    main()
