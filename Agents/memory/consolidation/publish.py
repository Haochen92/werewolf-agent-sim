"""The step after a tick writes its records: mirror them into the served game's lesson store
(``persistence/postgres.py``), so the next memory-on game reads what the pass left. The same
database holds both: the tick's ``memory_records`` (its record) and LangGraph's ``store`` tables
(the index with the vectors)."""

from __future__ import annotations

from typing import Any

import psycopg

import Agents.memory.consolidation.db as db
from Agents.memory.persistence.postgres import open_store, publish


def publish_from_db(conn: psycopg.Connection, dsn: str | None = None, *, force: bool = False,
                    source: dict[str, Any] | None = None) -> dict[str, Any]:
    """Read every kind from ``memory_records`` and publish it. ``force`` re-embeds everything."""
    stores = {kind: db.load_store(conn, kind) for kind in db.KINDS}
    store, pool = open_store(db.resolve_dsn(dsn))
    try:
        return publish(store, stores, source=source, force=force)
    finally:
        pool.close()
