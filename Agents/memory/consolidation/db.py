"""Postgres persistence for the consolidation pipeline — the DB is the system of record.

Owner ruling 2026-07-21: pipeline state lives in PostgreSQL (the ww-postgres pgvector instance),
not in loose JSON intermediates. The memory records keep their exact JSON record shape in ``jsonb``
columns (the store schema stays the one authority on record structure); relational tables carry
the sidecars (base rates, obs generation clocks) and the tick history.

The paid store-ops (synthesis clustering, batch dedup) run on FILE-based infra (embedding cache,
dedup orchestration), so a tick MATERIALIZES the DB store into a scratch dir, runs the ops there,
and INGESTS the result back — the scratch dir is compute scratch, never a source of truth. After
each tick a frozen JSON snapshot (``demo_gen{k}``) is exported for provenance, the frontend store
changelog, and the read path's seeding; snapshots are records, nothing runs off them.
"""

from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

import psycopg
from psycopg.types.json import Jsonb

KINDS = ("strategy_points", "observations")

_DDL = """
CREATE TABLE IF NOT EXISTS memory_records (
    kind   text  NOT NULL,
    ns     text  NOT NULL,
    key    text  NOT NULL,
    record jsonb NOT NULL,
    PRIMARY KEY (kind, key)
);
CREATE INDEX IF NOT EXISTS memory_records_ns_idx ON memory_records (kind, ns);
CREATE TABLE IF NOT EXISTS base_rates (
    channel text PRIMARY KEY,
    mean    double precision NOT NULL,
    n       integer NOT NULL
);
CREATE TABLE IF NOT EXISTS obs_generations (
    key             text PRIMARY KEY,
    first_seen      integer NOT NULL,
    last_reinforced integer NOT NULL,
    count           integer NOT NULL
);
CREATE TABLE IF NOT EXISTS tick_runs (
    gen          integer PRIMARY KEY,
    ran_at       timestamptz NOT NULL DEFAULT now(),
    stats        jsonb,
    window_spec  jsonb,
    snapshot_dir text
);
"""


def connect(dsn: str | None = None) -> psycopg.Connection:
    dsn = dsn or os.environ.get("WW_POSTGRES_DSN")
    if not dsn:
        raise RuntimeError("no DSN: pass one or set WW_POSTGRES_DSN")
    return psycopg.connect(dsn)


def setup(conn: psycopg.Connection) -> None:
    conn.execute(_DDL)
    conn.commit()


def store_is_empty(conn: psycopg.Connection) -> bool:
    return conn.execute("SELECT NOT EXISTS (SELECT 1 FROM memory_records)").fetchone()[0]


def load_store(conn: psycopg.Connection, kind: str) -> dict:
    """The store in its canonical JSON shape: {"namespaces": {ns: [record, ...]}}."""
    ns_map: dict[str, list] = {}
    for ns, record in conn.execute(
            "SELECT ns, record FROM memory_records WHERE kind = %s ORDER BY ns, key", (kind,)):
        ns_map.setdefault(ns, []).append(record)
    return {"namespaces": ns_map}


def save_store(conn: psycopg.Connection, kind: str, store: dict) -> None:
    """Transactional replace — the tick's post-consolidation store state supersedes the previous
    window's wholesale (window semantics: counters are recomputed, membership is the survivors)."""
    with conn.transaction():
        conn.execute("DELETE FROM memory_records WHERE kind = %s", (kind,))
        with conn.cursor() as cur:
            for ns, recs in (store.get("namespaces") or {}).items():
                for r in recs:
                    cur.execute(
                        "INSERT INTO memory_records (kind, ns, key, record) VALUES (%s, %s, %s, %s)",
                        (kind, ns, r["key"], Jsonb(r)))


def load_base_rates(conn: psycopg.Connection) -> dict:
    return {ch: [mean, n] for ch, mean, n in
            conn.execute("SELECT channel, mean, n FROM base_rates")}


def save_base_rates(conn: psycopg.Connection, rates: dict) -> None:
    with conn.transaction():
        conn.execute("DELETE FROM base_rates")
        with conn.cursor() as cur:
            for ch, (mean, n) in rates.items():
                cur.execute("INSERT INTO base_rates (channel, mean, n) VALUES (%s, %s, %s)",
                            (ch, float(mean), int(n)))


def load_obs_sidecar(conn: psycopg.Connection) -> tuple[dict, dict, dict]:
    """(first_seen, last_reinforced, counts) per obs key — the decay clocks."""
    first_seen: dict = {}
    reinforced: dict = {}
    counts: dict = {}
    for key, fs, lr, ct in conn.execute(
            "SELECT key, first_seen, last_reinforced, count FROM obs_generations"):
        first_seen[key], reinforced[key], counts[key] = fs, lr, ct
    return first_seen, reinforced, counts


def save_obs_sidecar(conn: psycopg.Connection, first_seen: dict, reinforced: dict, counts: dict) -> None:
    with conn.transaction():
        conn.execute("DELETE FROM obs_generations")
        with conn.cursor() as cur:
            for key, fs in first_seen.items():
                cur.execute(
                    "INSERT INTO obs_generations (key, first_seen, last_reinforced, count) "
                    "VALUES (%s, %s, %s, %s)",
                    (key, int(fs), int(reinforced.get(key, fs)), int(counts.get(key, 1))))


def next_gen(conn: psycopg.Connection) -> int:
    row = conn.execute("SELECT COALESCE(MAX(gen), 0) FROM tick_runs").fetchone()
    return row[0] + 1


def last_snapshot_dir(conn: psycopg.Connection) -> str | None:
    row = conn.execute(
        "SELECT snapshot_dir FROM tick_runs WHERE snapshot_dir IS NOT NULL "
        "ORDER BY gen DESC LIMIT 1").fetchone()
    return row[0] if row else None


def record_tick(conn: psycopg.Connection, gen: int, stats: dict, window_spec: dict,
                snapshot_dir: str | None) -> None:
    conn.execute(
        "INSERT INTO tick_runs (gen, stats, window_spec, snapshot_dir) VALUES (%s, %s, %s, %s)",
        (gen, Jsonb(stats), Jsonb(window_spec), snapshot_dir))
    conn.commit()


def bootstrap_from_dir(conn: psycopg.Connection, store_dir: str | Path) -> dict:
    """Seed an EMPTY database from a promoted store artifact (memory_stores/v7_fixed): SP +
    observation records and base rates. Refuses to overwrite a non-empty store — bootstrap is a
    birth event, not a sync."""
    if not store_is_empty(conn):
        raise RuntimeError("memory_records is not empty — bootstrap would overwrite live state")
    store_dir = Path(store_dir)
    for kind, fname in (("strategy_points", "strategy_points.json"),
                        ("observations", "observations.json")):
        p = store_dir / fname
        save_store(conn, kind, json.loads(p.read_text()) if p.exists() else {"namespaces": {}})
    br = store_dir / "base_rates.json"
    if br.exists():
        save_base_rates(conn, json.loads(br.read_text()))
    conn.commit()
    return {"bootstrapped_from": str(store_dir)}


def materialize(conn: psycopg.Connection, scratch_dir: str | Path) -> Path:
    """DB -> scratch dir (observations.json / strategy_points.json / base_rates.json) so the
    file-based store-ops can run. The scratch dir is disposable compute state."""
    scratch_dir = Path(scratch_dir)
    scratch_dir.mkdir(parents=True, exist_ok=True)
    for kind, fname in (("strategy_points", "strategy_points.json"),
                        ("observations", "observations.json")):
        (scratch_dir / fname).write_text(json.dumps(load_store(conn, kind), indent=2))
    (scratch_dir / "base_rates.json").write_text(json.dumps(load_base_rates(conn), indent=2))
    return scratch_dir


def ingest(conn: psycopg.Connection, scratch_dir: str | Path) -> None:
    """Scratch dir -> DB after the store-ops ran: the post-tick store + the sidecar base rates the
    credit pass persisted next to it."""
    scratch_dir = Path(scratch_dir)
    for kind, fname in (("strategy_points", "strategy_points.json"),
                        ("observations", "observations.json")):
        save_store(conn, kind, json.loads((scratch_dir / fname).read_text()))
    br = scratch_dir / "base_rates.json"
    if br.exists():
        save_base_rates(conn, json.loads(br.read_text()))
    conn.commit()


def export_snapshot(scratch_dir: str | Path, snapshot_dir: str | Path, manifest: dict) -> Path:
    """Freeze the post-tick store as a read-only generation snapshot (demo_gen{k}) + manifest —
    provenance, the frontend changelog's diff source, and the read path's seed files."""
    scratch_dir, snapshot_dir = Path(scratch_dir), Path(snapshot_dir)
    if snapshot_dir.exists():
        raise RuntimeError(f"snapshot dir already exists: {snapshot_dir} (snapshots are immutable)")
    snapshot_dir.mkdir(parents=True)
    for fname in ("observations.json", "strategy_points.json", "base_rates.json"):
        src = scratch_dir / fname
        if src.exists():
            shutil.copy2(src, snapshot_dir / fname)
    (snapshot_dir / "manifest.json").write_text(json.dumps(manifest, indent=2))
    return snapshot_dir
