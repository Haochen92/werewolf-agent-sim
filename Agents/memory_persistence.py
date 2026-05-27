from __future__ import annotations

import hashlib
import json
import logging
import pickle
import time
from collections import defaultdict
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Callable

from langgraph.store.base import BaseStore, Item, PutOp
from pydantic import BaseModel

from Agents.constants import ACTION_PHASES, VALID_ACTION_PHASES_BY_ROLE, roles
from Agents.memory import store

logger = logging.getLogger(__name__)

MEMORY_STORES_DIR = Path(__file__).resolve().parent / "memory_stores"
DEFAULT_MEMORY_STORE_DIR = MEMORY_STORES_DIR / "v1_post_dedup"
OBSERVATIONS_FILE_NAME = "observations.json"
STRATEGY_POINTS_FILE_NAME = "strategy_points.json"
INDEXED_CACHE_FILE_NAME = "indexed_cache.pkl"
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


class BatchDedupConfig(BaseModel):
    """Settings for post-game incremental batch dedup."""

    enabled: bool = False
    two_pass: bool = True
    triage_model: str = "gemini-3.1-flash-lite"
    triage_thinking_level: str | None = "medium"
    verify_model: str = "gemini-2.5-pro"
    verify_thinking_level: str | None = None
    prompt_variant: str = "default"


class MemoryPersistenceConfig(BaseModel):
    """Seed/dump settings for the process-global LangGraph memory store.

    Normal graph runs use the v1 post-dedup store. Batch experiments can point
    seed and dump directories at another versioned store without changing code.
    """

    seed_enabled: bool = True
    dump_enabled: bool = True
    seed_store_dir: Path = DEFAULT_MEMORY_STORE_DIR
    dump_store_dir: Path = DEFAULT_MEMORY_STORE_DIR
    batch_dedup: BatchDedupConfig = BatchDedupConfig()


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


def _namespace_key(namespace: tuple[str, ...]) -> str:
    return "/".join(namespace)


def _snapshot_namespaces(namespace: tuple[str, ...]) -> list[tuple[str, ...]]:
    """Map legacy role-only memory namespaces to current action-phase namespaces."""
    if len(namespace) == 3:
        return [namespace]
    if len(namespace) != 2:
        return []
    memory_kind, role = namespace
    if memory_kind not in {"observations", "strategy_points"}:
        return [namespace]
    phases = VALID_ACTION_PHASES_BY_ROLE.get(role, ACTION_PHASES)
    return [(memory_kind, role, phase) for phase in phases]


def _snapshot_value(value: dict[str, Any]) -> dict[str, Any] | None:
    """Normalize legacy snapshot payloads to the current store index field."""
    situation = value.get("situation") or value.get("content")
    if not situation:
        return None
    return {**value, "situation": situation}


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
    namespace: tuple[str, ...],
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


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save_indexed_store_cache(
    target_store: BaseStore,
    cache_path: str | Path,
    observations_path: str | Path,
    strategy_points_path: str | Path,
) -> None:
    """Serialize store data and embedding vectors to a cache file.

    The cache file includes SHA-256 hashes of the source JSON files so it can
    be invalidated when the source data changes.
    """
    cache_path = Path(cache_path)

    data_dict: dict[tuple[str, ...], dict[str, dict[str, Any]]] = {}
    for namespace, items in target_store._data.items():
        data_dict[namespace] = {}
        for key, item in items.items():
            data_dict[namespace][key] = {
                "value": item.value,
                "created_at": item.created_at.isoformat() if item.created_at else None,
                "updated_at": item.updated_at.isoformat() if item.updated_at else None,
            }

    vectors_dict: dict[tuple[str, ...], dict[str, dict[str, list[float]]]] = {}
    for namespace, items in target_store._vectors.items():
        vectors_dict[namespace] = {}
        for key, paths in items.items():
            vectors_dict[namespace][key] = dict(paths)

    payload = {
        "version": 1,
        "observations_sha256": _file_sha256(Path(observations_path)),
        "strategy_points_sha256": _file_sha256(Path(strategy_points_path)),
        "data": data_dict,
        "vectors": vectors_dict,
    }

    cache_path.parent.mkdir(parents=True, exist_ok=True)
    with open(cache_path, "wb") as f:
        pickle.dump(payload, f, protocol=pickle.HIGHEST_PROTOCOL)

    logger.info(
        "Saved indexed store cache to %s (%d bytes)",
        cache_path,
        cache_path.stat().st_size,
    )


def load_indexed_store_cache(
    cache_path: str | Path,
    target_store: BaseStore,
    observations_path: str | Path,
    strategy_points_path: str | Path,
) -> bool:
    """Load store data and vectors from a cache file.

    Returns True if the cache was valid and loaded successfully,
    False if the cache is missing, stale, or corrupt.
    """
    cache_path = Path(cache_path)
    if not cache_path.exists():
        return False

    try:
        with open(cache_path, "rb") as f:
            payload = pickle.load(f)  # noqa: S301
    except Exception:
        logger.warning("Corrupt cache file %s, will re-seed", cache_path)
        return False

    if payload.get("version") != 1:
        return False

    obs_sha = _file_sha256(Path(observations_path))
    sp_sha = _file_sha256(Path(strategy_points_path))
    if (
        payload.get("observations_sha256") != obs_sha
        or payload.get("strategy_points_sha256") != sp_sha
    ):
        logger.info("Cache stale (source files changed), will re-seed")
        return False

    now = datetime.now(timezone.utc)
    for namespace, items in payload["data"].items():
        for key, item_data in items.items():
            target_store._data[namespace][key] = Item(
                value=item_data["value"],
                key=key,
                namespace=namespace,
                created_at=datetime.fromisoformat(item_data["created_at"]) if item_data["created_at"] else now,
                updated_at=datetime.fromisoformat(item_data["updated_at"]) if item_data["updated_at"] else now,
            )

    for namespace, items in payload["vectors"].items():
        for key, paths in items.items():
            target_store._vectors[namespace][key] = paths

    logger.info(
        "Loaded indexed store from cache: %d namespaces, %d vectors",
        len(payload["data"]),
        sum(len(v) for v in payload["vectors"].values()),
    )
    return True


def seed_memory_from_json_files_cached(
    observations_path: str | Path | None = None,
    strategy_points_path: str | Path | None = None,
    target_store: BaseStore = store,
    cache_dir: str | Path | None = None,
) -> dict[str, Any]:
    """Seed the store from cache if available, otherwise from API + save cache."""
    default_observations, default_strategy_points = memory_store_paths(
        DEFAULT_MEMORY_STORE_DIR
    )
    observations_path = Path(observations_path or default_observations)
    strategy_points_path = Path(strategy_points_path or default_strategy_points)

    if cache_dir is None:
        cache_dir = observations_path.parent
    cache_path = Path(cache_dir) / INDEXED_CACHE_FILE_NAME

    if load_indexed_store_cache(
        cache_path, target_store, observations_path, strategy_points_path
    ):
        return {"from_cache": True}

    counts = seed_memory_from_json_files(
        observations_path=observations_path,
        strategy_points_path=strategy_points_path,
        target_store=target_store,
    )

    save_indexed_store_cache(
        target_store, cache_path, observations_path, strategy_points_path
    )
    return {**counts, "from_cache": False}


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
            raw_namespace = tuple(namespace_key.split("/"))
            namespaces = _snapshot_namespaces(raw_namespace)
            if not namespaces:
                continue
            if raw_namespace[0] == "observations":
                count_key = "observations"
            elif raw_namespace[0] == "strategy_points":
                count_key = "strategy_points"
            else:
                continue
            for item in namespace_items:
                key = item.get("key")
                value = _snapshot_value(item.get("value", item))
                if not key or value is None:
                    continue
                for namespace in namespaces:
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
    from Agents.memory_batch_deduplication import (
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
