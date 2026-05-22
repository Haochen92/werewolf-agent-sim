"""Build a local frozen dedup eval dataset from Langfuse traces."""

from __future__ import annotations

import argparse
import json
import random
from datetime import datetime
from pathlib import Path

from evaluation.core.config_schema import DedupDatasetBuildConfig
from evaluation.core.settings import REPO_ROOT, load_project_env
from evaluation.data.datasets import (
    DedupDatasetRecord,
    dedup_record_from_case,
    write_dedup_dataset,
)
from evaluation.data.langfuse import (
    fetch_dedup_cases,
    fetch_trace_ids_for_session_id,
    fetch_trace_ids_for_session_ids,
    fetch_trace_ids_for_session_prefix,
    read_session_ids_from_batch_results,
)

load_project_env()


def resolve_trace_ids(config: DedupDatasetBuildConfig) -> list[str]:
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
    if max_games <= 0 or len(trace_ids) <= max_games:
        return trace_ids
    step = len(trace_ids) / max_games
    return [trace_ids[int(i * step)] for i in range(max_games)]


def build_records(config: DedupDatasetBuildConfig) -> list[DedupDatasetRecord]:
    trace_ids = resolve_trace_ids(config)
    if not trace_ids:
        return []

    games = select_games(trace_ids, config.max_games)
    print(f"Found {len(trace_ids)} traces; sampling from {len(games)} games.")

    records: list[DedupDatasetRecord] = []
    for trace_id in games:
        cases = fetch_dedup_cases(trace_id)
        for case in cases:
            if config.filter_auto and case.auto:
                continue
            records.append(
                dedup_record_from_case(
                    case,
                    eval_set_id=config.eval_set_id,
                    created_from=config.created_from,
                )
            )
    print(f"Found {len(records)} dedup cases.")

    if config.max_samples and len(records) > config.max_samples:
        rng = random.Random(config.seed)
        records = rng.sample(records, config.max_samples)
        print(f"Sampled {config.max_samples} cases.")

    return records


def default_output_path(eval_set_id: str) -> Path:
    return REPO_ROOT / "eval_sets" / f"{eval_set_id}.jsonl"


def write_manifest(
    path: Path,
    records: list[DedupDatasetRecord],
    config: DedupDatasetBuildConfig,
) -> None:
    manifest = {
        "eval_set_id": config.eval_set_id,
        "created_at": datetime.now().isoformat(),
        "created_from": config.created_from,
        "dataset_path": str(path),
        "case_count": len(records),
        "seed": config.seed,
        "max_games": config.max_games,
        "max_samples": config.max_samples,
        "filter_auto": config.filter_auto,
    }
    manifest_path = path.with_suffix(".manifest.json")
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a frozen dedup eval dataset from Langfuse traces."
    )
    parser.add_argument("--config", type=Path, required=True)
    return parser.parse_args()


def read_config(path: Path) -> DedupDatasetBuildConfig:
    return DedupDatasetBuildConfig.model_validate_json(
        path.read_text(encoding="utf-8")
    )


def main() -> None:
    args = parse_args()
    config = read_config(args.config)
    out_path = config.output or default_output_path(config.eval_set_id)
    if out_path.exists() and not config.overwrite:
        raise FileExistsError(
            f"Dataset already exists: {out_path}. Set overwrite=true to replace."
        )

    records = build_records(config)
    if not records:
        print("No records written.")
        return

    write_dedup_dataset(out_path, records)
    write_manifest(out_path, records, config)
    print(f"Wrote {len(records)} dedup records to {out_path}")


if __name__ == "__main__":
    main()
