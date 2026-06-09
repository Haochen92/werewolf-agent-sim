"""Incremental-mode helpers: last-dedup timestamp persistence + new-key collection.

Reads/writes the ``.last_dedup_at`` marker in a store dir and scans the JSON store for keys
created after that timestamp, so incremental runs only touch clusters with new entries.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from .config import DEDUP_TIMESTAMP_FILE


def _read_last_dedup_at(store_dir: Path) -> datetime | None:
    ts_path = store_dir / DEDUP_TIMESTAMP_FILE
    if not ts_path.exists():
        return None
    text = ts_path.read_text().strip()
    if not text:
        return None
    return datetime.fromisoformat(text)


def _write_last_dedup_at(store_dir: Path, ts: datetime | None = None) -> None:
    ts = ts or datetime.now(timezone.utc)
    (store_dir / DEDUP_TIMESTAMP_FILE).write_text(ts.isoformat() + "\n")


def _collect_new_keys(store_dir: Path, since: datetime) -> set[str]:
    """Return keys from the JSON store whose created_at is after *since*."""
    new_keys: set[str] = set()
    for filename in ("observations.json", "strategy_points.json"):
        path = store_dir / filename
        if not path.exists():
            continue
        with open(path) as f:
            data = json.load(f)
        for entries in data.get("namespaces", {}).values():
            for entry in entries:
                created = entry.get("created_at")
                if not created:
                    new_keys.add(entry["key"])
                    continue
                entry_ts = datetime.fromisoformat(created)
                if entry_ts > since:
                    new_keys.add(entry["key"])
    return new_keys
