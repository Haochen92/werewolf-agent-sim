from __future__ import annotations

import json
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path
from typing import Any

from langgraph.store.base import BaseStore
from pydantic import BaseModel

from Agents.constants import roles
from Agents.memory import store, store_observation, store_strategy_points
from Agents.schemas import Observation, StrategyPoint

MEMORY_DATA_DIR = Path(__file__).resolve().parent / "data"
OBSERVATIONS_JSON_PATH = MEMORY_DATA_DIR / "werewolf_observations.json"
STRATEGIES_JSON_PATH = MEMORY_DATA_DIR / "werewolf_strategies.json"
STRATEGY_POINTS_JSON_PATH = MEMORY_DATA_DIR / "werewolf_strategy_points.json"
_SEEDED_STORE_IDS: set[int] = set()


def _json_safe(value: Any) -> Any:
    if isinstance(value, BaseModel):
        return _json_safe(value.model_dump())
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return value


def _read_json(path: str | Path) -> dict[str, Any]:
    path = Path(path)
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: str | Path, payload: dict[str, Any]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(_json_safe(payload), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _namespace_key(namespace: tuple[str, str]) -> str:
    return "/".join(namespace)


def _all_namespace_items(
    target_store: BaseStore,
    namespace: tuple[str, str],
) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    offset = 0
    limit = 100
    while True:
        page = target_store.search(namespace, query=None, limit=limit, offset=offset)
        if not page:
            break
        for item in page:
            items.append(
                {
                    "key": item.key,
                    "namespace": list(namespace),
                    "value": _json_safe(item.value),
                    "created_at": _json_safe(getattr(item, "created_at", None)),
                    "updated_at": _json_safe(getattr(item, "updated_at", None)),
                }
            )
        offset += len(page)
        if len(page) < limit:
            break
    return items


def _strategy_point_from_snapshot(role: str, value: dict[str, Any]) -> StrategyPoint | None:
    situation = value.get("situation") or value.get("content")
    if not situation:
        return None
    return StrategyPoint(
        perspective=value.get("perspective", role),
        situation=situation,
        action=value.get("action", ""),
    )


def seed_memory_from_json_files(
    observations_path: str | Path = OBSERVATIONS_JSON_PATH,
    strategies_path: str | Path = STRATEGIES_JSON_PATH,
    strategy_points_path: str | Path = STRATEGY_POINTS_JSON_PATH,
    target_store: BaseStore = store,
) -> dict[str, int]:
    """Seed the active memory store from JSON snapshots using current memory helpers."""
    observations_payload = _read_json(observations_path)
    strategy_points_payload = _read_json(strategy_points_path)

    observation_count = 0
    for role in roles:
        namespace_items = observations_payload.get("namespaces", {}).get(
            _namespace_key(("observations", role)),
            [],
        )
        by_game_id: dict[str, list[Observation]] = defaultdict(list)
        for item in namespace_items:
            value = item.get("value", item)
            content = value.get("content")
            if not content:
                continue
            game_id = str(value.get("game_id") or item.get("game_id") or "")
            by_game_id[game_id].append(
                Observation(perspective=value.get("perspective", role), content=content)
            )
        for game_id, observations in by_game_id.items():
            store_observation(target_store, observations, game_id=game_id)
            observation_count += len(observations)

    # Strategy records are historical monolithic notes, not retrieval memories.
    # Skip them during import-time seeding to avoid hundreds of indexed writes.
    strategy_count = 0

    strategy_point_count = 0
    for role in roles:
        namespace_items = strategy_points_payload.get("namespaces", {}).get(
            _namespace_key(("strategy_points", role)),
            [],
        )
        by_game_id: dict[str, list[StrategyPoint]] = defaultdict(list)
        for item in namespace_items:
            value = item.get("value", item)
            strategy_point = _strategy_point_from_snapshot(role, value)
            if strategy_point is None:
                continue
            game_id = str(value.get("game_id") or item.get("game_id") or "")
            by_game_id[game_id].append(strategy_point)
        for game_id, strategy_points in by_game_id.items():
            store_strategy_points(target_store, strategy_points, game_id=game_id)
            strategy_point_count += len(strategy_points)

    return {
        "observations": observation_count,
        "strategies": strategy_count,
        "strategy_points": strategy_point_count,
    }


def seed_memory_from_json_files_once(
    observations_path: str | Path = OBSERVATIONS_JSON_PATH,
    strategies_path: str | Path = STRATEGIES_JSON_PATH,
    strategy_points_path: str | Path = STRATEGY_POINTS_JSON_PATH,
    target_store: BaseStore = store,
) -> dict[str, int | bool]:
    store_id = id(target_store)
    if store_id in _SEEDED_STORE_IDS:
        return {
            "observations": 0,
            "strategies": 0,
            "strategy_points": 0,
            "skipped": True,
        }

    counts = seed_memory_from_json_files(
        observations_path=observations_path,
        strategies_path=strategies_path,
        strategy_points_path=strategy_points_path,
        target_store=target_store,
    )
    _SEEDED_STORE_IDS.add(store_id)
    return {
        **counts,
        "skipped": False,
    }


def _strategy_games_from_namespaces(payload: dict[str, Any]) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, str]] = defaultdict(dict)
    sort_keys: dict[str, str] = {}
    for role in roles:
        namespace_items = payload.get("namespaces", {}).get(
            _namespace_key(("strategy", role)),
            [],
        )
        for item in namespace_items:
            if item.get("key") == "latest":
                continue
            value = item.get("value", {})
            content = value.get("content")
            game_id = str(value.get("game_id") or item.get("key", "").removeprefix("game_"))
            if content and game_id:
                grouped[game_id][role] = content
                sort_keys.setdefault(
                    game_id,
                    str(value.get("created_at") or item.get("created_at") or game_id),
                )

    return [
        {"game_id": game_id, "strategies": strategies}
        for game_id, strategies in sorted(
            grouped.items(), key=lambda game: (sort_keys.get(game[0], ""), game[0])
        )
    ]


def dump_memory_to_json_files(
    observations_path: str | Path = OBSERVATIONS_JSON_PATH,
    strategies_path: str | Path = STRATEGIES_JSON_PATH,
    strategy_points_path: str | Path = STRATEGY_POINTS_JSON_PATH,
    target_store: BaseStore = store,
) -> dict[str, int]:
    """Dump all role-scoped memory namespaces to JSON snapshots."""
    observation_namespaces = {
        _namespace_key(("observations", role)): _all_namespace_items(
            target_store, ("observations", role)
        )
        for role in roles
    }
    strategy_namespaces = {
        _namespace_key(("strategy", role)): _all_namespace_items(
            target_store, ("strategy", role)
        )
        for role in roles
    }
    strategy_point_namespaces = {
        _namespace_key(("strategy_points", role)): _all_namespace_items(
            target_store, ("strategy_points", role)
        )
        for role in roles
    }

    observations_payload = {
        "schema_version": "werewolf_observations.v1",
        "description": "Temporary episodic-memory snapshot. Seed through store_observation so embeddings and dedup use the active memory.py store configuration.",
        "updated_at": datetime.now().isoformat(),
        "namespaces": observation_namespaces,
    }
    strategies_payload = {
        "schema_version": "werewolf_strategies.v1",
        "description": "Temporary strategy-memory snapshot. Seed through store_strategy so latest and historical keys are rebuilt by the active memory.py implementation.",
        "updated_at": datetime.now().isoformat(),
        "namespaces": strategy_namespaces,
        "games": _strategy_games_from_namespaces({"namespaces": strategy_namespaces}),
    }
    strategy_points_payload = {
        "schema_version": "werewolf_strategy_points.v2",
        "description": "Temporary strategy-point memory snapshot. Content stores situation text for embeddings; action stores the recommended move.",
        "updated_at": datetime.now().isoformat(),
        "namespaces": strategy_point_namespaces,
    }

    _write_json(observations_path, observations_payload)
    _write_json(strategies_path, strategies_payload)
    _write_json(strategy_points_path, strategy_points_payload)

    return {
        "observations": sum(len(items) for items in observation_namespaces.values()),
        "strategies": sum(len(items) for items in strategy_namespaces.values()),
        "strategy_points": sum(len(items) for items in strategy_point_namespaces.values()),
    }
