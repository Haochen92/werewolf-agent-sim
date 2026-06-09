"""Cluster-rendering helpers: prompt-entry formatting, previews, and timestamp formatting.

``_format_cluster_entries`` renders a cluster as numbered indices for the LLM (and returns the
index→UUID map needed to translate operations back); ``_cluster_preview`` builds the report-side
ClusterPreview.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from .schemas import ClusterPreview, MemoryKind


def _format_datetime(value: Any) -> str:
    if isinstance(value, datetime):
        return value.isoformat()
    if value:
        return str(value)
    return ""


def _format_cluster_entries(
    memory_kind: MemoryKind,
    cluster_keys: list[str],
    items_by_key: dict[str, Any],
) -> tuple[str, dict[str, str]]:
    """Format cluster entries for LLM prompt using numbered indices.

    Returns (formatted_text, index_to_key_map) where the map translates
    string indices ("1", "2", ...) back to real UUID keys.
    """
    lines: list[str] = []
    index_to_key: dict[str, str] = {}
    for i, key in enumerate(cluster_keys, 1):
        index_to_key[str(i)] = key
        value = items_by_key[key].value
        lines.append(f"[{i}]")
        lines.append(f"observation_count: {value.get('observation_count', 1)}")
        lines.append(f"last_observed: {_format_datetime(value.get('last_observed'))}")
        lines.append(f"situation: {value.get('situation', '')}")
        if memory_kind == "strategy_points":
            lines.append(f"action: {value.get('action', '')}")
        else:
            lines.append(f"approach: {value.get('approach', '')}")
            lines.append(f"outcome: {value.get('outcome', '')}")
        lines.append("")
    return "\n".join(lines).strip(), index_to_key


def _cluster_preview(
    memory_kind: MemoryKind,
    role: str,
    cluster_keys: list[str],
    items_by_key: dict[str, Any],
    preview_chars: int,
) -> ClusterPreview:
    previews: list[str] = []
    for key in cluster_keys:
        value = items_by_key[key].value
        situation = value.get("situation", "")
        preview = situation[:preview_chars]
        if len(situation) > preview_chars:
            preview += "..."
        previews.append(preview)
    return ClusterPreview(
        memory_kind=memory_kind,
        role=role,
        size=len(cluster_keys),
        keys=cluster_keys,
        previews=previews,
    )


def _latest_timestamp(values: list[Any]) -> str:
    raw_values = [_format_datetime(value) for value in values if value]
    if not raw_values:
        return datetime.now().isoformat()
    return max(raw_values)
