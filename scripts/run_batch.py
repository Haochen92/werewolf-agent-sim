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

# Imported after sys.path is set so the evaluation package resolves; lightweight (no heavy deps).
from evaluation.src.data import batch_layout


ROLES = ("wolf", "villager", "healer", "investigator", "serial_killer", "vigilante")


def role_config(*enabled_roles: str) -> dict[str, bool]:
    enabled = set(enabled_roles)
    return {role: role in enabled for role in ROLES}


def reranking_config(
    *,
    observation_roles: tuple[str, ...] = (),
    strategy_point_roles: tuple[str, ...] = (),
) -> dict[str, dict[str, bool]]:
    return {
        "observations": role_config(*observation_roles),
        "strategy_points": role_config(*strategy_point_roles),
    }


MEMORY_CONFIGS = {
    "all_disabled": role_config(),
    "all_enabled": role_config(*ROLES),
    "wolf_only": role_config("wolf"),
    "serial_killer_only": role_config("serial_killer"),
    "villager_only": role_config("villager"),
    "healer_only": role_config("healer"),
    "investigator_only": role_config("investigator"),
    "town_only": role_config("villager", "healer", "investigator", "vigilante"),
    "specials_only": role_config("healer", "investigator"),
}

RERANKING_CONFIGS = {
    "rerank_disabled": reranking_config(),
    "rerank_enabled": reranking_config(
        observation_roles=ROLES,
        strategy_point_roles=ROLES,
    ),
    "strategy_points": reranking_config(strategy_point_roles=ROLES),
    "observations": reranking_config(observation_roles=ROLES),
}

FILTERING_CONFIGS = {
    "filter_disabled": role_config(),
    "filter_enabled": role_config(*ROLES),
}

RETRIEVAL_TYPES_CONFIGS = {
    "both": {"observations": True, "strategy_points": True},
    "observations_only": {"observations": True, "strategy_points": False},
    "strategy_points_only": {"observations": False, "strategy_points": True},
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
        "--game-ids-file",
        default=None,
        help=(
            "JSON file: a list of game_ids (or an object with a 'game_ids' key). "
            "Pins the per-game seed so every selected config plays the SAME role "
            "draws — the paired A/B design. Overrides --runs-per-config to the "
            "length of the list."
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
        "--filtering",
        choices=list(FILTERING_CONFIGS),
        default="filter_disabled",
        help=(
            "Retrieval filtering config (MMR for strategy points, dedup gate "
            f"for observations). Available: {', '.join(FILTERING_CONFIGS)}"
        ),
    )
    parser.add_argument(
        "--retrieval-types",
        choices=list(RETRIEVAL_TYPES_CONFIGS),
        default="both",
        help=(
            "Which memory types to retrieve. "
            f"Available: {', '.join(RETRIEVAL_TYPES_CONFIGS)}"
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
    parser.add_argument(
        "--extract-without-dump",
        action="store_true",
        help=(
            "Run (and trace) postgame extraction even when --no-memory-dump is set, "
            "but skip persistence. For measuring per-role fan-out + cache cost on a "
            "throwaway game without writing to the store."
        ),
    )
    parser.add_argument(
        "--experiment",
        default=None,
        help=(
            "Experiment id = the batch_results/<id>/ folder name. Defaults to the "
            "session prefix, so every run is structured (games/, eval_cases/, "
            "config.json, summary.json). Use --flat for the legacy flat layout."
        ),
    )
    parser.add_argument(
        "--description",
        default=None,
        help="Free-text note describing the experiment; recorded in config.json.",
    )
    parser.add_argument(
        "--flat",
        action="store_true",
        help=(
            "Opt out of the experiment-folder layout: write the legacy flat "
            "batch_results/<session-prefix>.jsonl + eval_cases/<session>/ instead."
        ),
    )
    parser.add_argument(
        "--skip-embedding-canary",
        action="store_true",
        help=(
            "Skip the embedding-alias drift check that runs at batch start (default "
            "on). Only skip if embedding creds are unavailable; drift silently "
            "corrupts every store vector and retrieval query."
        ),
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


def resolve_experiment(args: argparse.Namespace, session_prefix: str) -> str | None:
    """The experiment-folder name. Structured layout is the DEFAULT: an explicit
    --experiment, else the session prefix. Returns None ONLY under --flat (the
    backwards-compatible escape hatch → legacy flat batch_results/<prefix>.jsonl)."""
    if args.flat:
        return None
    return args.experiment or session_prefix


def write_record(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(json_safe(record), sort_keys=True) + "\n")


def write_eval_cases_sidecar(
    session_id: str,
    game_id: str,
    eval_records: list[dict] | None,
    experiment: str | None = None,
) -> Path | None:
    """Persist a game's locally-emitted eval cases (normalized span dicts) as a
    per-game sidecar the frozen-set builders read directly — no Langfuse fetch.

    One file per game, overwritten if present: game_id is a fresh uuid4 per run,
    so unlike the appended batch JSONL a cancelled rerun can't leave stale cruft.
    With an experiment set, the sidecar nests under that experiment's folder.
    """
    if not eval_records:
        return None
    if experiment:
        path = batch_layout.eval_cases_path(experiment, session_id, game_id)
    else:
        path = REPO_ROOT / "batch_results" / "eval_cases" / session_id / f"{game_id}.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        for eval_record in eval_records:
            file.write(json.dumps(json_safe(eval_record), sort_keys=True) + "\n")
    return path


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
            args.extract_without_dump,
        )
    ):
        return None

    seed_store_dir = args.seed_store_dir or args.memory_store_dir
    dump_store_dir = args.dump_store_dir or args.memory_store_dir
    config: dict[str, Any] = {
        "seed_enabled": not args.no_memory_seed,
        "dump_enabled": not args.no_memory_dump,
    }
    if args.extract_without_dump:
        config["extraction"] = {"extract_without_dump": True}
    if seed_store_dir:
        config["seed_store_dir"] = str(seed_store_dir)
    if dump_store_dir:
        config["dump_store_dir"] = str(dump_store_dir)
    return config


def load_game_ids(path: str | None) -> list[str] | None:
    """Load a pinned seed set (list of game_ids) for the paired A/B.

    Accepts a JSON list, or an object with a ``game_ids`` key. Returns None when no
    file is given — each game then mints a fresh uuid4 (the default). Pinning the
    same ids across configs makes every arm play identical role draws.
    """
    if not path:
        return None
    data = json.loads(Path(path).read_text())
    game_ids = data["game_ids"] if isinstance(data, dict) else data
    if not isinstance(game_ids, list) or not all(isinstance(g, str) for g in game_ids):
        raise SystemExit(
            f"--game-ids-file must be a JSON list of strings (or {{'game_ids': [...]}}): {path}"
        )
    if len(set(game_ids)) != len(game_ids):
        raise SystemExit("--game-ids-file contains duplicate game_ids")
    return game_ids


def faction_survivors(result: dict[str, Any]) -> dict[str, list[str]]:
    """Marker-derived, unambiguous survivor breakdown for the durable record.

    The graph's `surviving_villagers` channel is really the NON-WOLF bucket (town + the solo serial
    killer), so reading it as "town" silently miscounts the SK. Split it by `roles` so replay/analysis
    never has to know that quirk: wolves / town (non-wolf, non-SK) / serial_killer.
    """
    roles = result.get("roles") or {}
    non_wolf = result.get("surviving_villagers") or []
    return {
        "wolves": list(result.get("surviving_wolves") or []),
        "town": [p for p in non_wolf if roles.get(p) != "serial_killer"],
        "serial_killer": [p for p in non_wolf if roles.get(p) == "serial_killer"],
    }


def run_batch(args: argparse.Namespace) -> int:
    config_names = selected_config_names(args.configs)
    memory_persistence_config = memory_persistence_config_from_args(args)
    reranking_config = RERANKING_CONFIGS[args.reranking]
    filtering_config = FILTERING_CONFIGS[args.filtering]
    retrieval_types_config = RETRIEVAL_TYPES_CONFIGS[args.retrieval_types]
    # No game-config CLI overrides currently; games use the defaults. The general
    # game_config seam is kept (recorded + passed to run_game) for future overrides.
    game_config = None
    game_ids = load_game_ids(args.game_ids_file)
    runs_per_config = len(game_ids) if game_ids else args.runs_per_config
    session_prefix = args.session_prefix or datetime.now().strftime(
        "batch_%Y%m%d_%H%M%S"
    )
    experiment = resolve_experiment(args, session_prefix)
    # --output (explicit) wins; else an experiment routes game records under its
    # folder; else (--flat) the legacy flat path.
    if args.output is None and experiment:
        results_path = batch_layout.game_records_path(experiment, session_prefix)
    else:
        results_path = output_path(session_prefix, args.output)

    planned_runs = [
        (config_name, run_index)
        for config_name in config_names
        for run_index in range(1, runs_per_config + 1)
    ]
    if game_ids:
        print(
            f"Seed set: pinning {len(game_ids)} game_ids across "
            f"{len(config_names)} config(s) — paired (run_index i → game_ids[i-1])."
        )

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
    if any(filtering_config.values()):
        print(f"Filtering config: {filtering_config}")
    if not all(retrieval_types_config.values()):
        print(f"Retrieval types: {retrieval_types_config}")
    if memory_persistence_config:
        print(f"Memory persistence override: {memory_persistence_config}")
    if game_config:
        print(f"Game config override: {game_config}")

    if args.dry_run:
        return 0

    from Agents.turn import prompt_log
    from Agents.main import run_game
    from Agents.run_fingerprint import runtime_fingerprint
    from tests.leak_test import run_leak_tests

    # Resolved once per batch: code/prompt versions, model IDs, params, backend.
    # Makes each JSONL record self-describing — a record is only comparable to
    # another if their bundles match (model, prompts, backend, ...).
    fingerprint = runtime_fingerprint()
    print(f"Runtime fingerprint: {fingerprint}")

    # Embedding-alias drift canary: assert the store's embedding geometry still matches its
    # pins before spending a run on (silently) corrupted retrieval. Default-on; drift raises.
    if not args.skip_embedding_canary:
        from evaluation.src.core.embedding_canary import check_embedding_canary

        if check_embedding_canary():
            print("Embedding canary: OK (no alias drift).")

    print(f"Writing JSONL results to: {results_path}")

    if experiment:
        # config.json = a faithful mirror of the RESOLVED run config (what actually
        # ran, not the nominal request) + the runtime fingerprint. Write-if-absent,
        # so a loop campaign's first call stamps it and the rest no-op. Re-runnable:
        # it carries every knob run_batch resolved.
        resolved_config = {
            "configs": config_names,
            "memory_configs": {n: MEMORY_CONFIGS[n] for n in config_names},
            "runs_per_config": runs_per_config,
            "game_ids_pinned": game_ids,
            "reranking": args.reranking,
            "reranking_config": reranking_config,
            "filtering": args.filtering,
            "filtering_config": filtering_config,
            "retrieval_types": args.retrieval_types,
            "retrieval_types_config": retrieval_types_config,
            "memory_persistence_config": memory_persistence_config,
            "game_config": game_config,
        }
        # Scannable trio first (experiment / description / overview), then provenance,
        # then the full resolved config + fingerprint.
        run_config = {
            "experiment": experiment,
            "description": args.description,
            "overview": batch_layout.config_overview(resolved_config, fingerprint),
            "created_at": datetime.now().isoformat(),
            "source": {
                "argv": sys.argv[1:],
                "session_prefix": session_prefix,
                "session_scope": args.session_scope,
            },
            "resolved_config": resolved_config,
            "runtime_fingerprint": fingerprint,
        }
        config_file = batch_layout.write_run_config(experiment, json_safe(run_config))
        print(f"Experiment config: {config_file}")

    failures = 0
    started_runs = 0
    leak_games = 0

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

        game_id = game_ids[run_index - 1] if game_ids else None
        try:
            outcome = run_game(
                memory_config=memory_config,
                session_id=session_id,
                game_config=game_config,
                memory_persistence_config=memory_persistence_config,
                reranking_config=reranking_config,
                filtering_config=filtering_config,
                retrieval_types_config=retrieval_types_config,
                game_id=game_id,
            )
            result = outcome.result
            duration_seconds = perf_counter() - started_timer
            # run_game clears prompt_log at start, so the global holds exactly
            # this game's prompts. Leaks are recorded (not raised) so the game
            # result is preserved; the batch still exits non-zero on any leak.
            leaks = run_leak_tests(prompt_log, result.get("roles") or {})
            if leaks:
                leak_games += 1
                print(
                    f"LEAK DETECTED in {current_run_id}: {len(leaks)} leak(s)",
                    file=sys.stderr,
                )
            eval_cases_path = write_eval_cases_sidecar(
                session_id, outcome.game_id, outcome.eval_records, experiment
            )
            record = {
                "status": "success",
                "runtime_fingerprint": fingerprint,
                "config_name": config_name,
                "memory_config": memory_config,
                "reranking_config": reranking_config,
                "filtering_config": filtering_config,
                "retrieval_types_config": retrieval_types_config,
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
                # Unambiguous marker-derived split (surviving_villagers = non-wolf bucket incl. SK).
                "faction_survivors": faction_survivors(result),
                "roles": result.get("roles"),
                "investigator_results": result.get("investigator_results"),
                "day_channel": result.get("day_channel"),
                "day_summaries": result.get("day_summaries"),
                "computed_metrics": outcome.game_metrics.model_dump(mode="json"),
                # Raw per-decision accumulators for offline inspection — day votes
                # (counts, ties, no-lynch) and night targets/deaths/kill-landed.
                # The derived proxies live in computed_metrics.
                "day_resolutions": (outcome.raw_metrics or {}).get("day_resolutions"),
                "night_resolutions": (outcome.raw_metrics or {}).get("night_resolutions"),
                # Per-game memory dedup outcomes (absorption rate / store saturation);
                # empty {} for extraction-off / no-dump games.
                "dedup_stats": (outcome.raw_metrics or {}).get("dedup_stats"),
                "leak_check": {"passed": not leaks, "leaks": leaks},
                # Record→trace link + the per-game eval-case sidecar pointer
                # (repo-relative); builders follow it instead of fetching Langfuse.
                "game_id": outcome.game_id,
                "trace_id": outcome.trace_id,
                "eval_cases_path": (
                    str(eval_cases_path.relative_to(REPO_ROOT))
                    if eval_cases_path
                    else None
                ),
                "eval_case_count": len(outcome.eval_records or []),
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
                "runtime_fingerprint": fingerprint,
                "config_name": config_name,
                "memory_config": memory_config,
                "reranking_config": reranking_config,
                "filtering_config": filtering_config,
                "retrieval_types_config": retrieval_types_config,
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
    if leak_games:
        summary += f", {leak_games} game(s) WITH PRIVATE-INFO LEAKS"
    print(summary)

    if experiment:
        batch_layout.merge_run_summary(
            experiment,
            session_prefix,
            {
                "configs": config_names,
                "status": "complete" if not failures else "errors",
                "successes": successes,
                "failures": failures,
                "not_started": not_started,
                "leak_games": leak_games,
            },
        )

    return 1 if failures or leak_games else 0


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
