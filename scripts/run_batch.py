from __future__ import annotations

import argparse
import json
import sys
import traceback
from datetime import date, datetime
from pathlib import Path
from time import perf_counter
from typing import Any

from dotenv import load_dotenv
from pydantic import BaseModel


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

load_dotenv(REPO_ROOT / ".env")


ROLES = ("wolf", "villager", "healer", "investigator")


def role_config(*enabled_roles: str) -> dict[str, bool]:
    enabled = set(enabled_roles)
    return {role: role in enabled for role in ROLES}


MEMORY_CONFIGS = {
    "all_disabled": role_config(),
    "all_enabled": role_config(*ROLES),
    "wolf_only": role_config("wolf"),
    "villager_only": role_config("villager"),
    "healer_only": role_config("healer"),
    "investigator_only": role_config("investigator"),
    "town_only": role_config("villager", "healer", "investigator"),
    "specials_only": role_config("healer", "investigator"),
}

RERANKING_CONFIGS = {
    "rerank_disabled": role_config(),
    "rerank_enabled": role_config(*ROLES),
}

DEFAULT_CONFIG_NAMES = ("all_disabled", "all_enabled", "wolf_only")


def json_safe(value: Any) -> Any:
    if isinstance(value, BaseModel):
        return json_safe(value.model_dump())
    if isinstance(value, dict):
        return {str(key): json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [json_safe(item) for item in value]
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return value


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run Werewolf games across memory configurations."
    )
    parser.add_argument(
        "--configs",
        nargs="+",
        default=list(DEFAULT_CONFIG_NAMES),
        help=(
            "Memory configs to run. Use 'all' for every built-in config. "
            f"Available: {', '.join(MEMORY_CONFIGS)}"
        ),
    )
    parser.add_argument(
        "--runs-per-config",
        type=int,
        default=1,
        help="Number of games to run for each selected memory config.",
    )
    parser.add_argument(
        "--max-discussion-rounds-per-day",
        type=int,
        default=None,
        help=(
            "Maximum public discussion rounds before each day vote. "
            "Defaults to the game config value."
        ),
    )
    parser.add_argument(
        "--session-prefix",
        default=None,
        help="Prefix for Langfuse session IDs. Defaults to batch timestamp.",
    )
    parser.add_argument(
        "--session-scope",
        choices=("run", "config", "batch"),
        default="config",
        help=(
            "How to group Langfuse sessions: 'run' creates one session per game "
            "run, 'config' creates one session per memory config (default), "
            "and 'batch' puts all runs in one session."
        ),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="JSONL output path. Defaults to batch_results/<session-prefix>.jsonl.",
    )
    parser.add_argument(
        "--fail-fast",
        action="store_true",
        help="Stop the batch after the first failed run.",
    )
    parser.add_argument(
        "--continue-on-quota-error",
        action="store_true",
        help=(
            "Keep running after provider quota exhaustion errors. By default, "
            "quota exhaustion stops the batch because later runs are likely to fail."
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the planned runs without invoking games.",
    )
    parser.add_argument(
        "--memory-store-dir",
        type=Path,
        default=None,
        help=(
            "Use one versioned memory store directory for both seeding and dumping."
        ),
    )
    parser.add_argument(
        "--seed-store-dir",
        type=Path,
        default=None,
        help="Memory store directory used to seed the run.",
    )
    parser.add_argument(
        "--dump-store-dir",
        type=Path,
        default=None,
        help="Memory store directory where postgame extraction dumps memory.",
    )
    parser.add_argument(
        "--reranking",
        choices=list(RERANKING_CONFIGS),
        default="rerank_disabled",
        help=(
            "Reranking config for memory retrieval. "
            f"Available: {', '.join(RERANKING_CONFIGS)}"
        ),
    )
    parser.add_argument(
        "--no-memory-seed",
        action="store_true",
        help="Start the process without seeding memory from JSON snapshots.",
    )
    parser.add_argument(
        "--no-memory-dump",
        action="store_true",
        help="Disable postgame memory snapshot dumps.",
    )
    return parser.parse_args()


def selected_config_names(raw_names: list[str]) -> list[str]:
    if "all" in raw_names:
        return list(MEMORY_CONFIGS)

    unknown = [name for name in raw_names if name not in MEMORY_CONFIGS]
    if unknown:
        valid = ", ".join(["all", *MEMORY_CONFIGS])
        raise ValueError(f"Unknown config(s): {', '.join(unknown)}. Valid: {valid}")

    return raw_names


def output_path(session_prefix: str, requested_path: Path | None) -> Path:
    if requested_path is not None:
        return requested_path
    return REPO_ROOT / "batch_results" / f"{session_prefix}.jsonl"


def write_record(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(json_safe(record), sort_keys=True) + "\n")


def is_quota_exhaustion_error(exc: Exception) -> bool:
    error_text = repr(exc)
    return "RESOURCE_EXHAUSTED" in error_text or "Quota exceeded" in error_text


def is_non_recoverable_batch_error(exc: Exception) -> bool:
    error_text = repr(exc)
    return is_quota_exhaustion_error(exc) or (
        "Number of embeddings" in error_text
        and "does not match number of indices" in error_text
    ) or (
        "NOT_FOUND" in error_text
        and "is not found" in error_text
        and "embedContent" in error_text
    )


def run_id(session_prefix: str, config_name: str, run_index: int) -> str:
    return f"{session_prefix}_{config_name}_{run_index:03d}"


def langfuse_session_id(
    session_prefix: str,
    config_name: str,
    run_index: int,
    session_scope: str,
) -> str:
    if session_scope == "batch":
        return session_prefix
    if session_scope == "config":
        return f"{session_prefix}_{config_name}"
    return run_id(session_prefix, config_name, run_index)


def memory_persistence_config_from_args(args: argparse.Namespace) -> dict[str, Any] | None:
    """Return optional memory store override config for experiment batches."""
    if not any(
        (
            args.memory_store_dir,
            args.seed_store_dir,
            args.dump_store_dir,
            args.no_memory_seed,
            args.no_memory_dump,
        )
    ):
        return None

    seed_store_dir = args.seed_store_dir or args.memory_store_dir
    dump_store_dir = args.dump_store_dir or args.memory_store_dir
    config: dict[str, Any] = {
        "seed_enabled": not args.no_memory_seed,
        "dump_enabled": not args.no_memory_dump,
    }
    if seed_store_dir:
        config["seed_store_dir"] = str(seed_store_dir)
    if dump_store_dir:
        config["dump_store_dir"] = str(dump_store_dir)
    return config


def game_config_from_args(args: argparse.Namespace) -> dict[str, Any] | None:
    if args.max_discussion_rounds_per_day is None:
        return None
    return {
        "max_discussion_rounds_per_day": args.max_discussion_rounds_per_day,
    }


def run_batch(args: argparse.Namespace) -> int:
    config_names = selected_config_names(args.configs)
    memory_persistence_config = memory_persistence_config_from_args(args)
    reranking_config = RERANKING_CONFIGS[args.reranking]
    game_config = game_config_from_args(args)
    session_prefix = args.session_prefix or datetime.now().strftime(
        "batch_%Y%m%d_%H%M%S"
    )
    results_path = output_path(session_prefix, args.output)

    planned_runs = [
        (config_name, run_index)
        for config_name in config_names
        for run_index in range(1, args.runs_per_config + 1)
    ]

    print(f"Planned runs: {len(planned_runs)}")
    for config_name, run_index in planned_runs:
        current_run_id = run_id(session_prefix, config_name, run_index)
        session_id = langfuse_session_id(
            session_prefix,
            config_name,
            run_index,
            args.session_scope,
        )
        print(
            f"- {current_run_id}: session={session_id} "
            f"{MEMORY_CONFIGS[config_name]}"
        )
    if any(reranking_config.values()):
        print(f"Reranking config: {reranking_config}")
    if memory_persistence_config:
        print(f"Memory persistence override: {memory_persistence_config}")
    if game_config:
        print(f"Game config override: {game_config}")

    if args.dry_run:
        return 0

    from Agents.main import run_game

    print(f"Writing JSONL results to: {results_path}")
    failures = 0
    started_runs = 0

    for planned_run_index, (config_name, run_index) in enumerate(planned_runs):
        started_runs += 1
        memory_config = MEMORY_CONFIGS[config_name]
        current_run_id = run_id(session_prefix, config_name, run_index)
        session_id = langfuse_session_id(
            session_prefix,
            config_name,
            run_index,
            args.session_scope,
        )
        started_at = datetime.now()
        started_timer = perf_counter()
        print(f"Running {current_run_id} in session {session_id}")

        try:
            outcome = run_game(
                memory_config=memory_config,
                session_id=session_id,
                game_config=game_config,
                memory_persistence_config=memory_persistence_config,
                reranking_config=reranking_config,
            )
            result = outcome.result
            duration_seconds = perf_counter() - started_timer
            record = {
                "status": "success",
                "config_name": config_name,
                "memory_config": memory_config,
                "reranking_config": reranking_config,
                "game_config": game_config,
                "run_index": run_index,
                "run_id": current_run_id,
                "session_id": session_id,
                "memory_persistence_config": memory_persistence_config,
                "started_at": started_at,
                "ended_at": datetime.now(),
                "duration_seconds": round(duration_seconds, 3),
                "winner": result.get("winner"),
                "current_day": result.get("current_day"),
                "surviving_wolves": result.get("surviving_wolves"),
                "surviving_villagers": result.get("surviving_villagers"),
                "roles": result.get("roles"),
                "investigator_results": result.get("investigator_results"),
                "computed_metrics": outcome.game_metrics.model_dump(mode="json"),
            }
            write_record(results_path, record)
            print(
                f"Completed {current_run_id}: winner={record['winner']} "
                f"day={record['current_day']}"
            )
        except Exception as exc:
            failures += 1
            duration_seconds = perf_counter() - started_timer
            record = {
                "status": "error",
                "config_name": config_name,
                "memory_config": memory_config,
                "reranking_config": reranking_config,
                "game_config": game_config,
                "run_index": run_index,
                "run_id": current_run_id,
                "session_id": session_id,
                "memory_persistence_config": memory_persistence_config,
                "started_at": started_at,
                "ended_at": datetime.now(),
                "duration_seconds": round(duration_seconds, 3),
                "error": repr(exc),
                "traceback": traceback.format_exc(),
            }
            write_record(results_path, record)
            print(f"Failed {current_run_id}: {exc}", file=sys.stderr)
            if args.fail_fast:
                break
            if is_non_recoverable_batch_error(exc) and not args.continue_on_quota_error:
                remaining_runs = len(planned_runs) - (planned_run_index + 1)
                print(
                    "Stopping batch after a non-recoverable batch error; "
                    f"{remaining_runs} planned run(s) were not started. "
                    "Use --continue-on-quota-error to keep running anyway.",
                    file=sys.stderr,
                )
                break

    successes = started_runs - failures
    not_started = len(planned_runs) - started_runs
    summary = f"Batch complete: {successes} succeeded, {failures} failed"
    if not_started:
        summary += f", {not_started} not started"
    print(summary)
    return 1 if failures else 0


def main() -> None:
    try:
        args = parse_args()
        exit_code = run_batch(args)
    except Exception as exc:
        print(f"Batch setup failed: {exc}", file=sys.stderr)
        exit_code = 2
    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
