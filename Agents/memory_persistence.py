from __future__ import annotations

import json
import logging
import time
from datetime import date, datetime
from pathlib import Path
from typing import Any, Callable

from langgraph.store.base import BaseStore, PutOp
from pydantic import BaseModel

from Agents.constants import roles
from Agents.memory import store

logger = logging.getLogger(__name__)

MEMORY_STORES_DIR = Path(__file__).resolve().parent / "memory_stores"
DEFAULT_MEMORY_STORE_DIR = MEMORY_STORES_DIR / "v1_post_dedup"
OBSERVATIONS_FILE_NAME = "observations.json"
STRATEGY_POINTS_FILE_NAME = "strategy_points.json"
_SEEDED_STORE_IDS: set[int] = set()
_TRANSIENT_MEMORY_STORE_STATUS_CODES = {408, 429, 500, 502, 503, 504}
_TRANSIENT_MEMORY_STORE_ERROR_MARKERS = (
    "408",
    "429",
    "500",
    "502",
    "503",
    "504",
    "bad gateway",
    "connection reset",
    "deadline",
    "rate limit",
    "server error",
    "service unavailable",
    "temporar",
    "timeout",
    "too many requests",
)


class MemoryPersistenceConfig(BaseModel):
    """Seed/dump settings for the process-global LangGraph memory store.

    Normal graph runs use the v1 post-dedup store. Batch experiments can point
    seed and dump directories at another versioned store without changing code.
    """

    seed_enabled: bool = True
    dump_enabled: bool = True
    seed_store_dir: Path = DEFAULT_MEMORY_STORE_DIR
    dump_store_dir: Path = DEFAULT_MEMORY_STORE_DIR


def normalize_memory_persistence_config(
    config: MemoryPersistenceConfig | dict[str, Any] | None,
) -> MemoryPersistenceConfig:
    """Return a concrete memory persistence config with project defaults."""
    if config is None:
        return MemoryPersistenceConfig()
    if isinstance(config, MemoryPersistenceConfig):
        return config
    return MemoryPersistenceConfig.model_validate(config)


def memory_persistence_config_from_runnable(
    config: dict[str, Any] | None,
) -> MemoryPersistenceConfig:
    """Read memory persistence settings from LangGraph runnable config."""
    configurable = config.get("configurable", {}) if config else {}
    return normalize_memory_persistence_config(
        configurable.get("memory_persistence_config")
    )


def memory_store_paths(store_dir: str | Path) -> tuple[Path, Path]:
    """Return observation and strategy-point paths for an episodic store dir."""
    store_dir = Path(store_dir)
    return (
        store_dir / OBSERVATIONS_FILE_NAME,
        store_dir / STRATEGY_POINTS_FILE_NAME,
    )


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


def _exception_chain(exc: BaseException) -> list[BaseException]:
    chain = [exc]
    seen = {id(exc)}
    current = exc
    while True:
        next_exc = current.__cause__ or current.__context__
        if next_exc is None or id(next_exc) in seen:
            return chain
        chain.append(next_exc)
        seen.add(id(next_exc))
        current = next_exc


def _is_transient_memory_store_error(exc: BaseException) -> bool:
    for current in _exception_chain(exc):
        status_code = getattr(current, "status_code", None)
        if status_code in _TRANSIENT_MEMORY_STORE_STATUS_CODES:
            return True

        response = getattr(current, "response", None)
        response_status = getattr(response, "status_code", None)
        if response_status in _TRANSIENT_MEMORY_STORE_STATUS_CODES:
            return True

        message = str(current).lower()
        if any(marker in message for marker in _TRANSIENT_MEMORY_STORE_ERROR_MARKERS):
            return True

    return False


def _memory_store_call_with_retries(
    call: Callable[[], Any],
    *,
    operation_name: str,
    retry_attempts: int,
    retry_initial_delay: float,
    retry_max_delay: float,
    sleep: Callable[[float], None] = time.sleep,
) -> Any:
    attempts = max(1, retry_attempts)
    for attempt in range(1, attempts + 1):
        try:
            return call()
        except Exception as exc:
            if attempt >= attempts or not _is_transient_memory_store_error(exc):
                raise

            delay = min(retry_max_delay, retry_initial_delay * (2 ** (attempt - 1)))
            logger.warning(
                "Memory store %s failed with a transient error; "
                "retrying in %.1fs (attempt %s/%s): %s",
                operation_name,
                delay,
                attempt + 1,
                attempts,
                exc,
            )
            sleep(delay)

    raise RuntimeError(f"Memory store {operation_name} retry loop exited unexpectedly")


def _batch_with_retries(
    target_store: BaseStore,
    ops: list[PutOp],
    *,
    retry_attempts: int,
    retry_initial_delay: float,
    retry_max_delay: float,
    sleep: Callable[[float], None] = time.sleep,
) -> None:
    _memory_store_call_with_retries(
        lambda: target_store.batch(ops),
        operation_name="batch",
        retry_attempts=retry_attempts,
        retry_initial_delay=retry_initial_delay,
        retry_max_delay=retry_max_delay,
        sleep=sleep,
    )


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


def seed_memory_from_json_files(
    observations_path: str | Path | None = None,
    strategy_points_path: str | Path | None = None,
    target_store: BaseStore = store,
    batch_size: int = 1,
    retry_attempts: int = 5,
    retry_initial_delay: float = 1.0,
    retry_max_delay: float = 30.0,
) -> dict[str, int]:
    """Seed the active memory store from JSON snapshots.

    Snapshot entries are already deduped. Load them directly to preserve keys,
    counts, and text while indexing them in batches.
    """
    default_observations, default_strategy_points = memory_store_paths(
        DEFAULT_MEMORY_STORE_DIR
    )
    observations_path = observations_path or default_observations
    strategy_points_path = strategy_points_path or default_strategy_points

    put_ops: list[PutOp] = []
    counts = {
        "observations": 0,
        "strategies": 0,
        "strategy_points": 0,
    }
    for path in (observations_path, strategy_points_path):
        payload = _read_json(path)
        for namespace_key, namespace_items in payload.get("namespaces", {}).items():
            namespace = tuple(namespace_key.split("/"))
            if len(namespace) != 2:
                continue
            if namespace[0] == "observations":
                count_key = "observations"
            elif namespace[0] == "strategy_points":
                count_key = "strategy_points"
            else:
                continue
            for item in namespace_items:
                key = item.get("key")
                value = item.get("value", item)
                if not key or not value.get("content"):
                    continue
                put_ops.append(PutOp(namespace, key, value))
                counts[count_key] += 1

    for start in range(0, len(put_ops), batch_size):
        _batch_with_retries(
            target_store,
            put_ops[start : start + batch_size],
            retry_attempts=retry_attempts,
            retry_initial_delay=retry_initial_delay,
            retry_max_delay=retry_max_delay,
        )

    return counts


def seed_memory_from_json_files_once(
    observations_path: str | Path | None = None,
    strategy_points_path: str | Path | None = None,
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
        strategy_points_path=strategy_points_path,
        target_store=target_store,
    )
    _SEEDED_STORE_IDS.add(store_id)
    return {
        **counts,
        "skipped": False,
    }


def seed_memory_from_config(
    config: MemoryPersistenceConfig | dict[str, Any] | None = None,
    target_store: BaseStore = store,
) -> dict[str, int | bool]:
    """Seed the memory store once using a memory persistence config."""
    memory_config = normalize_memory_persistence_config(config)
    if not memory_config.seed_enabled:
        return {
            "observations": 0,
            "strategies": 0,
            "strategy_points": 0,
            "skipped": True,
        }
    observations_path, strategy_points_path = memory_store_paths(
        memory_config.seed_store_dir
    )
    return seed_memory_from_json_files_once(
        observations_path=observations_path,
        strategy_points_path=strategy_points_path,
        target_store=target_store,
    )


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
        _namespace_key(("observations", role)): _all_namespace_items(
            target_store, ("observations", role)
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
    strategy_points_payload = {
        "schema_version": "werewolf_strategy_points.v2",
        "description": "Temporary strategy-point memory snapshot. Content stores situation text for embeddings; action stores the recommended move.",
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
