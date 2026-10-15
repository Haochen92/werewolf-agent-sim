"""The served game's lesson store: LangGraph's PostgresStore on the ww-postgres pgvector
instance, with the index the in-memory store uses (the embedder, its size, the situation field).

The tick's tables stay its system of record (``consolidation/db.py``: records as jsonb, replaced
wholesale each pass). This store is the READ INDEX the engine searches, and it is where the vectors
live, so a server process never seeds anything: it opens the store and searches it. ``publish``
mirrors the records into the index, embedding only what changed, and signs the index with the
embedder that built it, so a process on another embedder refuses vectors that mean nothing to it
(ruled 2026-07-21: "yes pgvectordb"; built 2026-10-14 after the file cache broke the served game).
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from langgraph.store.base import BaseStore, PutOp
from langgraph.store.postgres import PostgresStore
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from Agents.llm_factory import DEFAULT_EMBEDDING_DIMS, DEFAULT_EMBEDDING_MODEL

from .retries import _batch_with_retries
from .serialization import _snapshot_namespaces, _snapshot_value

logger = logging.getLogger(__name__)

MARKER_NAMESPACE = ("index",)
MARKER_KEY = "embedding"
# One OpenRouter embedding call per batch; a Gemini embedder collapses a batch into one vector.
PUBLISH_BATCH_SIZE = 64 if "/" in DEFAULT_EMBEDDING_MODEL else 1
_PAGE = 500


def embedding_signature() -> dict[str, Any]:
    """The embedder this process searches with. Vectors from another one are meaningless to it."""
    return {"embedding_model": DEFAULT_EMBEDDING_MODEL, "embedding_dims": DEFAULT_EMBEDDING_DIMS}


def index_config() -> dict[str, Any]:
    """The same index as ``Agents.memory.store``: cosine over the situation field."""
    from Agents.memory.store import embeddings

    return {"dims": DEFAULT_EMBEDDING_DIMS, "embed": embeddings, "fields": ["situation"]}


def open_store(dsn: str, *, min_size: int = 1, max_size: int = 4) -> tuple[PostgresStore, ConnectionPool]:
    """Open the store on a connection pool (graph nodes are sync and run on worker threads, so
    the pool is what lets several seats search at once) and create its tables if missing. The
    caller closes the pool."""
    pool = ConnectionPool(
        dsn, open=True, min_size=min_size, max_size=max_size,
        kwargs={"autocommit": True, "prepare_threshold": 0, "row_factory": dict_row},
    )
    store = PostgresStore(pool, index=index_config())  # type: ignore[arg-type]
    store.setup()
    return store, pool


def read_marker(store: BaseStore) -> dict[str, Any] | None:
    """What the last publish wrote: the embedder, when, how many records, from which source."""
    item = store.get(MARKER_NAMESPACE, MARKER_KEY)
    return dict(item.value) if item is not None else None


def unready_reason(store: BaseStore) -> str | None:
    """Why a memory-on game must not read this store right now, or None when it may."""
    marker = read_marker(store)
    if marker is None:
        return "no lessons have been published to the database yet"
    built = {"embedding_model": marker.get("embedding_model"), "embedding_dims": marker.get("embedding_dims")}
    if built != embedding_signature():
        return (f"the lessons were embedded with {built['embedding_model']} at {built['embedding_dims']} "
                f"dimensions; this server embeds with {DEFAULT_EMBEDDING_MODEL} at {DEFAULT_EMBEDDING_DIMS}")
    if not (marker.get("counts") or {}).get("strategy_points"):
        return "the published store holds no strategy points"
    return None


def _desired(stores: dict[str, dict]) -> dict[tuple[str, ...], dict[str, dict]]:
    """{namespace: {key: value}} the index should hold, from stores in the canonical JSON shape
    ``{"namespaces": {"kind/role/phase": [record, ...]}}`` (the tick's and the snapshots')."""
    desired: dict[tuple[str, ...], dict[str, dict]] = {}
    for kind, payload in stores.items():
        for ns_key, records in (payload.get("namespaces") or {}).items():
            raw = tuple(ns_key.split("/"))
            if raw[0] != kind:
                continue
            for namespace in _snapshot_namespaces(raw):
                for record in records:
                    key = record.get("key")
                    value = _snapshot_value(record.get("value", record))
                    if key and value is not None:
                        desired.setdefault(namespace, {})[key] = value
    return desired


def _existing(store: BaseStore, kinds: list[str]) -> dict[tuple[str, ...], dict[str, dict]]:
    existing: dict[tuple[str, ...], dict[str, dict]] = {}
    for kind in kinds:
        for namespace in store.list_namespaces(prefix=(kind,)):
            items: dict[str, dict] = {}
            offset = 0
            while True:
                page = store.search(namespace, limit=_PAGE, offset=offset)
                items.update({item.key: item.value for item in page})
                if len(page) < _PAGE:
                    break
                offset += _PAGE
            existing[namespace] = items
    return existing


def publish(store: BaseStore, stores: dict[str, dict], *, source: dict[str, Any] | None = None,
            force: bool = False) -> dict[str, Any]:
    """Make the index hold exactly ``stores``: put what is new or changed (the only embedding
    cost), delete what is gone, leave the rest. Everything is re-embedded when the index was built
    by another embedder (or ``force``). The marker is written last, so a publish that dies
    half-way leaves the old signature and the next one finishes the job."""
    marker = read_marker(store)
    signature = embedding_signature()
    rebuild = force or marker is None or any(marker.get(k) != v for k, v in signature.items())
    desired = _desired(stores)
    existing = _existing(store, list(stores))

    puts: list[PutOp] = []
    deletes: list[PutOp] = []
    unchanged = 0
    for namespace, records in desired.items():
        held = existing.get(namespace, {})
        for key, value in records.items():
            if not rebuild and held.get(key) == value:
                unchanged += 1
            else:
                puts.append(PutOp(namespace, key, value))
    for namespace, held in existing.items():
        for key in held:
            if key not in desired.get(namespace, {}):
                deletes.append(PutOp(namespace, key, None))

    for start in range(0, len(puts), PUBLISH_BATCH_SIZE):
        _batch_with_retries(store, puts[start:start + PUBLISH_BATCH_SIZE],
                            retry_attempts=5, retry_initial_delay=1.0, retry_max_delay=30.0)
    for start in range(0, len(deletes), _PAGE):
        store.batch(deletes[start:start + _PAGE])

    counts = {kind: sum(len(r) for ns, r in desired.items() if ns[0] == kind) for kind in stores}
    store.put(MARKER_NAMESPACE, MARKER_KEY, {
        **signature,
        "published_at": datetime.now(timezone.utc).isoformat(),
        "counts": counts,
        "source": source or {},
    }, index=False)
    stats = {"put": len(puts), "deleted": len(deletes), "unchanged": unchanged,
             "reembedded_all": rebuild, "counts": counts}
    logger.info("published the lesson store: %s", stats)
    return stats
