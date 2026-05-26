"""Build a calibration dataset for auto-dedup threshold tuning.

Loads extraction JSONL files, builds an in-memory vector store from a subset
of games, then searches each extracted item against the store.  This produces
cases across the full similarity spectrum — including low-similarity pairs
needed to calibrate the auto-keep boundary.

Usage::

    poetry run python -m evaluation.experiments.auto_dedup_dataset_builder \
        --config configs/eval/auto_dedup_build.json

Example config::

    {
        "eval_set_id": "auto_dedup_v1",
        "extraction_files": [
            "evidence/extraction_quality/model_comparison/gemini-2.5-pro_5games_per-role_20260526_121348.jsonl"
        ],
        "store_files": [
            "evidence/extraction_quality/model_comparison/gemini-3.5-flash_5games_per-role_20260526_090106.jsonl"
        ],
        "top_n": 5,
        "min_similarity": 0.0,
        "seed": 42,
        "output": "eval_sets/auto_dedup_v1.jsonl"
    }
"""

from __future__ import annotations

import argparse
import json
import random
import uuid
from datetime import datetime
from pathlib import Path

from Agents.llm_factory import create_embeddings
from Agents.schemas.memory import Observation, StrategyPoint
from evaluation.core.config_schema import AutoDedupDatasetBuildConfig
from evaluation.data.datasets import AutoDedupRecord, write_auto_dedup_dataset
from langgraph.store.memory import InMemoryStore


def _load_extractions(paths: list[Path]) -> list[dict]:
    records = []
    for path in paths:
        with path.open() as f:
            for line in f:
                stripped = line.strip()
                if stripped:
                    records.append(json.loads(stripped))
    return records


def _build_store(extraction_records: list[dict]) -> InMemoryStore:
    embeddings = create_embeddings("gemini-embedding-001", output_dimensionality=1536)
    store = InMemoryStore(
        index={"dims": 1536, "embed": embeddings, "fields": ["situation"]},
    )

    ingested = 0
    for record in extraction_records:
        game_id = record.get("game_id", "")

        for obs_dict in record.get("observations", []):
            try:
                obs = Observation.model_validate(obs_dict)
            except Exception:
                continue
            namespace = ("observations", obs.perspective, obs.action_phase)
            store.put(namespace, str(uuid.uuid4()), {
                "situation": obs.composed_situation,
                "approach": obs.approach,
                "outcome": obs.outcome,
                "observation_count": 1,
                "game_id": game_id,
            })
            ingested += 1

        for sp_dict in record.get("strategy_points", []):
            try:
                sp = StrategyPoint.model_validate(sp_dict)
            except Exception:
                continue
            namespace = ("strategy_points", sp.perspective, sp.action_phase)
            store.put(namespace, str(uuid.uuid4()), {
                "situation": sp.composed_situation,
                "action": sp.action,
                "observation_count": 1,
                "game_id": game_id,
            })
            ingested += 1

    print(f"Ingested {ingested} items into store")
    return store


def _search_and_build_records(
    extraction_records: list[dict],
    store: InMemoryStore,
    config: AutoDedupDatasetBuildConfig,
) -> list[AutoDedupRecord]:
    records: list[AutoDedupRecord] = []
    case_index = 0

    for extraction in extraction_records:
        game_id = extraction.get("game_id", "")

        for obs_dict in extraction.get("observations", []):
            try:
                obs = Observation.model_validate(obs_dict)
            except Exception:
                continue

            namespace = ("observations", obs.perspective, obs.action_phase)
            results = store.search(
                namespace,
                query=obs.composed_situation,
                limit=config.top_n,
            )

            candidates = []
            max_sim = 0.0
            for i, item in enumerate(results, 1):
                sim = item.score or 0.0
                if sim < config.min_similarity:
                    continue
                max_sim = max(max_sim, sim)
                candidates.append({
                    "candidate_number": i,
                    "key": item.key,
                    "similarity": round(sim, 4),
                    "observation_count": item.value.get("observation_count", 1),
                    "situation": item.value.get("situation", ""),
                    "approach": item.value.get("approach", ""),
                    "outcome": item.value.get("outcome", ""),
                    "game_id": item.value.get("game_id", ""),
                })

            if not candidates:
                continue

            records.append(AutoDedupRecord(
                eval_set_id=config.eval_set_id,
                case_index=case_index,
                game_id=game_id,
                item_type="observation",
                perspective=obs.perspective,
                action_phase=obs.action_phase,
                new_entry={
                    "situation": obs.composed_situation,
                    "approach": obs.approach,
                    "outcome": obs.outcome,
                },
                candidates=candidates,
                situation_sim=round(max_sim, 4),
            ))
            case_index += 1

        for sp_dict in extraction.get("strategy_points", []):
            try:
                sp = StrategyPoint.model_validate(sp_dict)
            except Exception:
                continue

            namespace = ("strategy_points", sp.perspective, sp.action_phase)
            results = store.search(
                namespace,
                query=sp.composed_situation,
                limit=config.top_n,
            )

            candidates = []
            max_sim = 0.0
            for i, item in enumerate(results, 1):
                sim = item.score or 0.0
                if sim < config.min_similarity:
                    continue
                max_sim = max(max_sim, sim)
                candidates.append({
                    "candidate_number": i,
                    "key": item.key,
                    "similarity": round(sim, 4),
                    "observation_count": item.value.get("observation_count", 1),
                    "situation": item.value.get("situation", ""),
                    "action": item.value.get("action", ""),
                    "game_id": item.value.get("game_id", ""),
                })

            if not candidates:
                continue

            records.append(AutoDedupRecord(
                eval_set_id=config.eval_set_id,
                case_index=case_index,
                game_id=game_id,
                item_type="strategy_point",
                perspective=sp.perspective,
                action_phase=sp.action_phase,
                new_entry={
                    "situation": sp.composed_situation,
                    "action": sp.action,
                },
                candidates=candidates,
                situation_sim=round(max_sim, 4),
            ))
            case_index += 1

    return records


def build_dataset(config: AutoDedupDatasetBuildConfig) -> list[AutoDedupRecord]:
    store_records = _load_extractions(config.store_files)
    print(f"Loaded {len(store_records)} extraction records for store")

    store = _build_store(store_records)

    search_records = _load_extractions(config.extraction_files)
    print(f"Loaded {len(search_records)} extraction records to search")

    records = _search_and_build_records(search_records, store, config)
    print(f"Built {len(records)} calibration cases")

    if config.max_samples and len(records) > config.max_samples:
        rng = random.Random(config.seed)
        records = rng.sample(records, config.max_samples)
        for i, r in enumerate(records):
            r.case_index = i
        print(f"Sampled down to {len(records)} cases (seed={config.seed})")

    return records


def write_manifest(
    path: Path,
    records: list[AutoDedupRecord],
    config: AutoDedupDatasetBuildConfig,
) -> None:
    from collections import Counter
    type_counts = Counter(r.item_type for r in records)
    sim_ranges = {}
    for item_type in type_counts:
        sims = [r.situation_sim for r in records if r.item_type == item_type]
        sim_ranges[item_type] = {
            "count": len(sims),
            "min_sim": round(min(sims), 4) if sims else 0,
            "max_sim": round(max(sims), 4) if sims else 0,
            "mean_sim": round(sum(sims) / len(sims), 4) if sims else 0,
        }

    manifest = {
        "eval_set_id": config.eval_set_id,
        "created_at": datetime.now().isoformat(),
        "extraction_files": [str(p) for p in config.extraction_files],
        "store_files": [str(p) for p in config.store_files],
        "top_n": config.top_n,
        "min_similarity": config.min_similarity,
        "case_count": len(records),
        "per_type": sim_ranges,
        "seed": config.seed,
        "max_samples": config.max_samples,
    }
    manifest_path = path.with_suffix(".manifest.json")
    manifest_path.write_text(
        json.dumps(manifest, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote manifest to {manifest_path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build auto-dedup threshold calibration dataset."
    )
    parser.add_argument("--config", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = AutoDedupDatasetBuildConfig.model_validate_json(
        args.config.read_text(encoding="utf-8"),
    )

    out_path = config.output or Path(f"eval_sets/{config.eval_set_id}.jsonl")
    if out_path.exists() and not config.overwrite:
        raise FileExistsError(
            f"Dataset already exists: {out_path}. Set overwrite=true to replace."
        )

    records = build_dataset(config)
    if not records:
        print("No records built.")
        return

    write_auto_dedup_dataset(out_path, records)
    write_manifest(out_path, records, config)
    print(f"Wrote {len(records)} records to {out_path}")

    from collections import Counter
    type_counts = Counter(r.item_type for r in records)
    for item_type, count in sorted(type_counts.items()):
        sims = [r.situation_sim for r in records if r.item_type == item_type]
        print(f"  {item_type}: {count} cases, "
              f"sit_sim range [{min(sims):.3f}, {max(sims):.3f}]")


if __name__ == "__main__":
    main()
