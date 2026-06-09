from __future__ import annotations

import hashlib
import json
from datetime import date, datetime
from pathlib import Path
from typing import Any

from langgraph.store.base import BaseStore
from pydantic import BaseModel

from Agents.constants import ACTION_PHASES, VALID_ACTION_PHASES_BY_ROLE


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
