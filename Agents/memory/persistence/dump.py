from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from langgraph.store.base import BaseStore

from Agents.constants import ACTION_PHASES, VALID_ACTION_PHASES_BY_ROLE, roles
from Agents.memory.store import store

from .config import (
    DEFAULT_MEMORY_STORE_DIR,
    memory_store_paths,
    normalize_memory_persistence_config,
    MemoryPersistenceConfig,
)
from .serialization import _all_namespace_items, _namespace_key, _write_json


def dump_memory_to_json_files(
    observations_path: str | Path | None = None,
    strategy_points_path: str | Path | None = None,
    target_store: BaseStore = store,
) -> dict[str, int]:
    """Dump all role-scoped memory namespaces to JSON snapshots."""
    default_observations, default_strategy_points = memory_store_paths(
        DEFAULT_MEMORY_STORE_DIR
    )
    observations_path = observations_path or default_observations
    strategy_points_path = strategy_points_path or default_strategy_points

    observation_namespaces = {
        _namespace_key(("observations", role, phase)): _all_namespace_items(
            target_store, ("observations", role, phase)
        )
        for role in roles
        for phase in VALID_ACTION_PHASES_BY_ROLE.get(role, ACTION_PHASES)
    }
    strategy_point_namespaces = {
        _namespace_key(("strategy_points", role, phase)): _all_namespace_items(
            target_store, ("strategy_points", role, phase)
        )
        for role in roles
        for phase in VALID_ACTION_PHASES_BY_ROLE.get(role, ACTION_PHASES)
    }

    observations_payload = {
        "schema_version": "werewolf_observations.v2",
        "description": "Episodic-memory snapshot with action-phase namespaces. Situation field is used for semantic search; approach and outcome are payload.",
        "updated_at": datetime.now().isoformat(),
        "namespaces": observation_namespaces,
    }
    strategy_points_payload = {
        "schema_version": "werewolf_strategy_points.v3",
        "description": "Strategy-point memory snapshot with action-phase namespaces. Situation field is used for semantic search; action stores the recommended move.",
        "updated_at": datetime.now().isoformat(),
        "namespaces": strategy_point_namespaces,
    }

    _write_json(observations_path, observations_payload)
    _write_json(strategy_points_path, strategy_points_payload)

    return {
        "observations": sum(len(items) for items in observation_namespaces.values()),
        "strategies": 0,
        "strategy_points": sum(len(items) for items in strategy_point_namespaces.values()),
    }


def dump_memory_to_json_files_from_config(
    config: MemoryPersistenceConfig | dict[str, Any] | None = None,
    target_store: BaseStore = store,
) -> dict[str, int]:
    """Dump memory to the directory configured for the current run."""
    memory_config = normalize_memory_persistence_config(config)
    if not memory_config.dump_enabled:
        return {
            "observations": 0,
            "strategies": 0,
            "strategy_points": 0,
        }
    observations_path, strategy_points_path = memory_store_paths(
        memory_config.dump_store_dir
    )
    return dump_memory_to_json_files(
        observations_path=observations_path,
        strategy_points_path=strategy_points_path,
        target_store=target_store,
    )


def run_batch_dedup_from_config(
    config: MemoryPersistenceConfig | dict[str, Any] | None = None,
    target_store: BaseStore = store,
) -> dict[str, Any] | None:
    """Run incremental batch dedup if enabled in config.

    Must be called AFTER dump_memory_to_json_files_from_config so the JSON
    files reflect the latest state including newly extracted entries.
    """
    from Agents.memory.batch_deduplication import (
        TwoPassConfig,
        run_batch_memory_dedup,
    )

    memory_config = normalize_memory_persistence_config(config)
    dedup_cfg = memory_config.batch_dedup
    if not dedup_cfg.enabled:
        return None

    store_dir = memory_config.dump_store_dir

    two_pass = None
    if dedup_cfg.two_pass:
        two_pass = TwoPassConfig(
            triage_model=dedup_cfg.triage_model,
            triage_thinking_level=dedup_cfg.triage_thinking_level,
            verify_model=dedup_cfg.verify_model,
            verify_thinking_level=dedup_cfg.verify_thinking_level,
        )

    report = run_batch_memory_dedup(
        target_store=target_store,
        seed_store_dir=store_dir,
        dump_store_dir=store_dir,
        apply=True,
        incremental=True,
        two_pass=two_pass,
        prompt_variant=dedup_cfg.prompt_variant,
    )
    return report.model_dump(mode="json")
