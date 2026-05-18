"""Build a local frozen eval dataset from Langfuse game traces."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

from Agents.schemas.evaluation import EvalCase
from evaluation.core.config_schema import DatasetBuildConfig
from evaluation.core.settings import REPO_ROOT, load_project_env
from evaluation.data.datasets import EvalDatasetRecord, record_from_case, write_eval_dataset
from evaluation.data.langfuse import (
    fetch_eval_cases,
    fetch_trace_ids_for_session_id,
    fetch_trace_ids_for_session_ids,
    fetch_trace_ids_for_session_prefix,
    read_session_ids_from_batch_results,
)
from evaluation.data.sampling import sample_cases


load_project_env()


def resolve_trace_ids(config: DatasetBuildConfig) -> list[str]:
    """Resolve the configured Langfuse source into concrete trace IDs."""
    if config.trace_ids:
        return config.trace_ids
    if config.session_id:
        print(f"Fetching traces for session ID: {config.session_id}")
        return fetch_trace_ids_for_session_id(config.session_id)
    if config.session_ids:
        print(f"Fetching traces for {len(config.session_ids)} exact session IDs.")
        return fetch_trace_ids_for_session_ids(config.session_ids)
    if config.batch_results:
        session_ids = read_session_ids_from_batch_results(config.batch_results)
        print(
            f"Fetching traces for {len(session_ids)} session IDs from "
            f"{config.batch_results}"
        )
        return fetch_trace_ids_for_session_ids(session_ids)

    print(f"Fetching traces for session prefix: {config.session_prefix}")
    return fetch_trace_ids_for_session_prefix(config.session_prefix or "")


def select_games(trace_ids: list[str], max_games: int) -> list[str]:
    """Choose evenly spaced games when a max-game cap is configured."""
    if max_games <= 0 or len(trace_ids) <= max_games:
        return trace_ids
    step = len(trace_ids) / max_games
    return [trace_ids[int(i * step)] for i in range(max_games)]


def fetch_cases_for_games(
    trace_ids: list[str],
) -> tuple[list[EvalCase], dict[str, int]]:
    """Fetch eval cases and per-game lengths for the selected traces."""
    cases: list[EvalCase] = []
    game_lengths: dict[str, int] = {}
    for trace_id in trace_ids:
        game_cases = fetch_eval_cases(trace_id)
        cases.extend(game_cases)
        game_lengths[trace_id] = max((case.day for case in game_cases), default=1)
    return cases, game_lengths


def build_dataset_records(config: DatasetBuildConfig) -> list[EvalDatasetRecord]:
    """Fetch Langfuse traces once and freeze sampled EvalCase payloads locally."""
    trace_ids = resolve_trace_ids(config)
    if not trace_ids:
        return []

    games_to_sample = select_games(trace_ids, config.max_games)
    print(f"Found {len(trace_ids)} traces; sampling from {len(games_to_sample)} games.")

    cases, game_lengths = fetch_cases_for_games(games_to_sample)
    print(f"Found {len(cases)} candidate eval cases.")

    sampled = sample_cases(
        cases,
        game_lengths,
        games_to_sample=games_to_sample,
        per_role_per_phase=config.per_role_per_phase,
        max_samples=config.max_samples or None,
        seed=config.seed,
    )
    print(f"Sampled {len(sampled)} cases for local dataset.")

    return [
        record_from_case(
            case,
            eval_set_id=config.eval_set_id,
            created_from=config.created_from,
        )
        for case in sampled
    ]


def default_output_path(eval_set_id: str) -> Path:
    """Return the default JSONL dataset path for an eval set ID."""
    return REPO_ROOT / "eval_sets" / f"{eval_set_id}.jsonl"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a local frozen EvalCase dataset from Langfuse traces."
    )
    parser.add_argument("--config", type=Path, required=True)
    return parser.parse_args()


def read_config(path: Path) -> DatasetBuildConfig:
    """Load the dataset-builder JSON config."""
    return DatasetBuildConfig.model_validate_json(path.read_text(encoding="utf-8"))


def write_manifest(
    path: Path,
    records: list[EvalDatasetRecord],
    config: DatasetBuildConfig,
) -> None:
    """Write a small sidecar file describing how the dataset was sampled."""
    manifest = {
        "eval_set_id": config.eval_set_id,
        "created_at": datetime.now().isoformat(),
        "created_from": config.created_from,
        "dataset_path": str(path),
        "case_count": len(records),
        "seed": config.seed,
        "max_games": config.max_games,
        "per_role_per_phase": config.per_role_per_phase,
        "max_samples": config.max_samples,
    }
    manifest_path = path.with_suffix(".manifest.json")
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    args = parse_args()
    config = read_config(args.config)
    out_path = config.output or default_output_path(config.eval_set_id)
    if out_path.exists() and not config.overwrite:
        raise FileExistsError(
            f"Dataset already exists: {out_path}. Set overwrite=true in the config "
            "to replace it."
        )

    records = build_dataset_records(config)
    if not records:
        print("No records written.")
        return

    write_eval_dataset(out_path, records)
    write_manifest(out_path, records, config)
    print(f"Wrote {len(records)} EvalCase records to {out_path}")


if __name__ == "__main__":
    main()
