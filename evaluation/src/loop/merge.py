"""Fold parallel games' new observations into the run store via FREEZE-OLD dedup.

Within a generation the games run concurrently, each seeding READ-ONLY from a gen-start SNAPSHOT and
dumping to its OWN temp store (no shared-store write race). This merge then:
  1. collects each game's NEW obs = record keys present in a temp store but ABSENT from the snapshot
     (each game already deduped #1 its own obs against the snapshot), and appends them to the store; then
  2. runs the FREEZE-OLD batch dedup (#2, run_batch_memory_dedup) so CROSS-GAME duplicates collapse into
     observation_count reinforcement while the snapshot stays frozen (old obs never re-litigated).

Old obs are retired separately by the age×frequency decay pass — never here. The freeze-old dedup core is
the production-reusable piece (it's exactly production_design's sampled-games→dedup step); only the
temp-store key-diff is experiment glue (production extracts from sampled games instead of temp stores).
"""

from __future__ import annotations

import json
from pathlib import Path


def _load_obs(store_dir: str | Path) -> dict:
    return json.loads((Path(store_dir) / "observations.json").read_text())


def collect_new_obs(snapshot_dir: str | Path, temp_dirs: list) -> dict:
    """New obs records per namespace across the parallel games: keys present in a temp store but not in
    the gen-start snapshot, de-duplicated by key across temps (so a key emitted by two games is taken
    once — the freeze-old dedup then collapses genuine near-duplicates by content)."""
    snap = _load_obs(snapshot_dir)
    seen = {r["key"] for recs in snap.get("namespaces", {}).values() for r in recs if r.get("key")}
    new_by_ns: dict = {}
    for temp in temp_dirs:
        t = _load_obs(temp)
        for ns, recs in t.get("namespaces", {}).items():
            for r in recs:
                k = r.get("key")
                if k and k not in seen:
                    seen.add(k)
                    new_by_ns.setdefault(ns, []).append(r)
    return new_by_ns


def merge_new_obs(store_dir: str | Path, snapshot_dir: str | Path, temp_dirs: list,
                  dedup: bool = True) -> dict:
    """Append the parallel games' new obs into store_dir (which equals the snapshot at call time), then
    freeze-old dedup. Returns {"new_obs": n, "deduped": bool}. The dedup self-advances last_dedup_at, so
    each generation's new obs are the 'new' set and the prior store is frozen (cold gen-1 dedups all)."""
    store_dir = Path(store_dir)
    new_by_ns = collect_new_obs(snapshot_dir, temp_dirs)
    obs = _load_obs(store_dir)
    ns_map = obs.setdefault("namespaces", {})
    n = 0
    for ns, recs in new_by_ns.items():
        ns_map.setdefault(ns, []).extend(recs)
        n += len(recs)
    (store_dir / "observations.json").write_text(json.dumps(obs, indent=2))

    if dedup and n:
        # lazy import: keep the key-diff offline-testable without pulling the LLM dedup stack
        from Agents.memory.batch_deduplication.config import BatchDedupRunConfig
        from Agents.memory.batch_deduplication.orchestration import run_batch_memory_dedup
        cfg = BatchDedupRunConfig(
            seed_store_dir=store_dir, dump_store_dir=store_dir,
            incremental=True, apply=True, memory_kinds=["observations"],
        )
        run_batch_memory_dedup(cfg)  # freeze-old: only new-key clusters touched; old frozen
    return {"new_obs": n, "deduped": bool(dedup and n)}
