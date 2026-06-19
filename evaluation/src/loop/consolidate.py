"""Compounding loop — (b) CONSOLIDATION: prune/evict by realized credit + credit-aware synthesis.

Runs on a credited store (after credit.credit_apply). Three levers, all toggleable:
  PRUNE   drop SPs whose de-luck lift < tau with enough follows (b1 — the stably-harmful ones).
  EVICT   drop SPs surfaced >= R times but NEVER followed (the agent consistently rejects them = dead).
  SYNTH   credit-aware synthesis (CREDIT_SYNTH_PROMPT, realized track record) for cells with NEW obs —
          adds fresh SPs; existing SPs PERSIST so their credit accumulates across generations.

Existing SPs keep their keys (credit history intact); prune/evict cull, synth grows. Dedup of overlaps is
left to the existing batch-dedup pass (toggled in run_batch). Pure prune/evict is LLM-free → testable
offline; synth is the only paid step (flash-lite).
"""

from __future__ import annotations

import json
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

from evaluation.src.loop.config import LoopConfig
from evaluation.src.loop.credit import sp_lift


def _cell_of(ns_key: str) -> str:
    return "/".join(ns_key.split("/")[1:])  # "strategy_points/role/phase" -> "role/phase"


def prune_and_evict(sp_namespaces: dict, base_rates: dict, cfg: LoopConfig) -> dict:
    """Mutate sp_namespaces in place: drop harmful (lift<tau, follow>=N) + rejected (retrieved>=R,
    follow==0) SPs. Never drops a positive-lift SP. Returns {pruned, evicted, kept}."""
    pruned = evicted = kept = 0
    for ns_key, recs in list(sp_namespaces.items()):
        base = base_rates.get(_cell_of(ns_key), [0.0])[0]
        survivors = []
        for r in recs:
            v = r["value"]
            lift = sp_lift(v, base)
            follow = v.get("follow_count", 0)
            retrieved = v.get("retrieved_count", 0)
            if cfg.prune and lift is not None and lift < cfg.prune_tau and follow >= cfg.prune_min_follow:
                pruned += 1
                continue
            if cfg.evict and follow == 0 and retrieved >= cfg.evict_min_retrieved:
                evicted += 1
                continue
            survivors.append(r)
            kept += 1
        sp_namespaces[ns_key] = survivors
    return {"pruned": pruned, "evicted": evicted, "kept": kept}


def _track_record(sp_recs: list, base: float, min_follow: int = 5) -> str:
    rows = [(sp_lift(r["value"], base), r["value"].get("follow_count", 0), r["value"].get("action", ""))
            for r in sp_recs]
    rows = [(lf, f, a) for lf, f, a in rows if lf is not None and f >= min_follow]
    if not rows:
        return ""
    return "\n".join(f"- realized lift {lf:+.2f} (followed {f}x): {a}"
                     for lf, f, a in sorted(rows, reverse=True))


def synthesize(store_dir: Path, sp_namespaces: dict, base_rates: dict, cfg: LoopConfig,
               prev_obs_counts: dict | None = None) -> tuple[dict, dict]:
    """Credit-aware synthesis for cells with NEW obs since prev tick (incremental). Appends fresh SPs to
    sp_namespaces. Returns ({added, cells_synthed}, current_obs_counts). LLM step (model via cfg.env())."""
    # imported lazily so pure prune/evict stays import-light + LLM-free
    from Agents.memory.batch_deduplication.config import BatchDedupRunConfig
    from Agents.memory.persistence import memory_store_paths, seed_memory_from_json_files_cached
    from Agents.memory.store import store
    from Agents.memory.strategy_synthesis import cluster_observations_for_synth, synthesize_cluster_sps
    from Agents.schemas.roles import VALID_ACTION_PHASES_BY_ROLE, roles as ALL_ROLES

    obs_path, sp_path = memory_store_paths(store_dir)
    seed_memory_from_json_files_cached(observations_path=obs_path, strategy_points_path=sp_path,
                                       target_store=store, cache_dir=store_dir)
    cfgd = BatchDedupRunConfig(similarity_threshold=0.70, cluster_mode="bounded", max_cluster_size=15)
    prev = prev_obs_counts or {}
    obs_counts: dict[str, int] = {}
    tasks = []
    for role in ALL_ROLES:
        for phase in VALID_ACTION_PHASES_BY_ROLE.get(role, []):
            cell = f"{role}/{phase}"
            items, clusters = cluster_observations_for_synth(store, ("observations", role, phase), cfgd)
            obs_counts[cell] = len(items)
            if cfg.incremental and obs_counts[cell] == prev.get(cell):
                continue  # no new obs → skip (the production-cost requirement)
            tr = _track_record(sp_namespaces.get(f"strategy_points/{cell}", []),
                               base_rates.get(cell, [0.0])[0])
            for cl in clusters:
                live = [k for k in cl if k in items]
                if live:
                    tasks.append((role, phase, live, items, tr))

    now = datetime.now(timezone.utc)
    added = 0

    def _run(t):
        role, phase, live, items, tr = t
        return role, synthesize_cluster_sps(role, phase, live, items, max_retries=1, track_record=tr)

    if tasks:
        with ThreadPoolExecutor(max_workers=12) as pool:
            for role, sps in pool.map(_run, tasks):
                for sp in sps:
                    ns = f"strategy_points/{role}/{sp.action_phase}"
                    sp_namespaces.setdefault(ns, []).append({
                        "created_at": now.isoformat(), "key": str(uuid.uuid4()),
                        "namespace": ["strategy_points", role, sp.action_phase],
                        "updated_at": now.isoformat(),
                        "value": {"observation_count": 1, "last_observed": now.isoformat(), "game_id": "",
                                  "situation": sp.composed_situation, "action": sp.action,
                                  "direction": sp.direction, "honesty": sp.honesty,
                                  "follow_count": 0, "retrieved_count": 0, "positive_count": 0,
                                  "neutral_count": 0, "negative_count": 0,
                                  "dimensions": sp.model_dump(mode="json")},
                    })
                    added += 1
    return {"added": added, "cells_synthed": len({(r, p) for r, p, *_ in tasks})}, obs_counts


def consolidate(store_dir: str | Path, cfg: LoopConfig, prev_obs_counts: dict | None = None) -> dict:
    """Full consolidation tick on a (credited) store dir. Returns stats + obs_counts (for next tick)."""
    store_dir = Path(store_dir)
    _, sp_path = memory_store_paths_local(store_dir)
    base_rates = json.loads((store_dir / "base_rates.json").read_text()) \
        if (store_dir / "base_rates.json").exists() else {}
    store = json.loads(sp_path.read_text())
    ns = store.setdefault("namespaces", {})

    pe = prune_and_evict(ns, base_rates, cfg) if (cfg.prune or cfg.evict) else {}
    syn, obs_counts = ({}, prev_obs_counts or {})
    if cfg.synthesize:
        syn, obs_counts = synthesize(store_dir, ns, base_rates, cfg, prev_obs_counts)
    sp_path.write_text(json.dumps(store, indent=2))
    return {"prune_evict": pe, "synth": syn, "obs_counts": obs_counts}


def memory_store_paths_local(store_dir: Path):
    """Avoid importing Agents (LLM-heavy) for the pure prune/evict path."""
    return store_dir / "observations.json", store_dir / "strategy_points.json"
