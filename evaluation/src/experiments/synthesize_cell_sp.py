"""cluster_synth strategy points (step 3 of the v6 SP build): synthesize strategy points from CLUSTERS
of observations in a deduped v6 store, rather than per game.

For each (role, action_phase) namespace: cluster the observations by situation regime (gate_key only —
verdict-agnostic, so a cluster spans mixed outcomes) and synthesize 1-N strategy points per cluster
(the outcome spread is the weighting). Writes the SP store to --output-store-dir/strategy_points.json.

This is the SP path that justifies SPs existing (generalization across games); per_run
(reextract_cells --with-sp) is the cheap single-game baseline. Compare them — and "both" = run both into
separate stores, then dedup the SPs together.

  poetry run python evaluation/src/experiments/synthesize_cell_sp.py \
      --obs-store-dir memory_stores/v6_0 --output-store-dir memory_stores/v6_0_sp_cluster
"""

from __future__ import annotations

import argparse
import json
import sys
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from logging import getLogger
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from Agents.memory.batch_deduplication.config import BatchDedupRunConfig
from Agents.memory.persistence import memory_store_paths, seed_memory_from_json_files
from Agents.memory.store import store
from Agents.memory.strategy_synthesis import cluster_observations_for_synth, synthesize_cluster_sps
from Agents.schemas.memory import StoredStrategyPoint
from Agents.schemas.roles import VALID_ACTION_PHASES_BY_ROLE, roles as ALL_ROLES_TUPLE
from evaluation.src.core.manifest import build_manifest
from evaluation.src.experiments.reextract_villager_day import SCHEMA_VERSION

logger = getLogger(__name__)

DEFAULT_OBS = "memory_stores/v6_0"
DEFAULT_OUTPUT = "memory_stores/v6_0_sp_cluster"


def _synth_namespace(role: str, action_phase: str, config: BatchDedupRunConfig, max_retries: int):
    """Cluster + synthesize one (role, action_phase) namespace. Returns a list of SP cell objects."""
    namespace = ("observations", role, action_phase)
    items, clusters = cluster_observations_for_synth(store, namespace, config)
    out = []
    for cluster_keys in clusters:
        live = [k for k in cluster_keys if k in items]
        if not live:
            continue
        out.extend(synthesize_cluster_sps(role, action_phase, live, items, max_retries=max_retries))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--obs-store-dir", default=DEFAULT_OBS, help="deduped v6 observation store to read")
    ap.add_argument("--output-store-dir", default=DEFAULT_OUTPUT, help="where to write the SP store")
    ap.add_argument("--roles", nargs="+", default=list(ALL_ROLES_TUPLE))
    ap.add_argument("--similarity-threshold", type=float, default=0.70)
    ap.add_argument("--cluster-mode", default="bounded", choices=["bounded", "connected", "agglomerative"])
    ap.add_argument("--max-cluster-size", type=int, default=15)
    ap.add_argument("--max-retries", type=int, default=2)
    ap.add_argument("--max-workers", type=int, default=8)
    args = ap.parse_args()

    obs_path, obs_sp_path = memory_store_paths(Path(args.obs_store_dir))
    if not obs_path.exists():
        raise SystemExit(f"{obs_path} not found — build the v6 observation store first.")
    # obs_sp_path is this store's own SP file (absent for an obs-only store → tolerated); pointing here
    # rather than None avoids seeding the unrelated global-default SP store into the in-memory store.
    seed_memory_from_json_files(observations_path=obs_path, strategy_points_path=obs_sp_path, target_store=store)

    config = BatchDedupRunConfig(
        similarity_threshold=args.similarity_threshold,
        cluster_mode=args.cluster_mode,
        max_cluster_size=args.max_cluster_size,
    )

    units = [
        (role, ap_)
        for role in args.roles
        for ap_ in VALID_ACTION_PHASES_BY_ROLE.get(role, [])
        if ap_ != "night_action" or role != "villager"
    ]
    print(f"Synthesizing SPs over {len(args.roles)} roles = {len(units)} namespaces -> {args.output_store_dir}",
          flush=True)

    now = datetime.now(timezone.utc)
    sp_namespaces: dict[str, list[dict]] = {}
    with ThreadPoolExecutor(max_workers=args.max_workers) as pool:
        futs = {pool.submit(_synth_namespace, role, ap_, config, args.max_retries): (role, ap_)
                for role, ap_ in units}
        for fut in as_completed(futs):
            role, ap_ = futs[fut]
            sps = fut.result()
            for sp in sps:
                ns = f"strategy_points/{role}/{sp.action_phase}"
                sp_namespaces.setdefault(ns, []).append({
                    "created_at": now.isoformat(), "key": str(uuid.uuid4()),
                    "namespace": ["strategy_points", role, sp.action_phase],
                    "updated_at": now.isoformat(),
                    "value": StoredStrategyPoint(
                        observation_count=1, last_observed=now, game_id="",
                        situation=sp.composed_situation, action=sp.action,
                        direction=sp.direction, honesty=sp.honesty,
                        dimensions=sp.model_dump(mode="json"),
                    ).model_dump(mode="json"),
                })
            print(f"  {role}/{ap_}: synthesized {len(sps)} sp", flush=True)

    out_dir = Path(args.output_store_dir)
    _, sp_path = memory_store_paths(out_dir)
    sp_path.parent.mkdir(parents=True, exist_ok=True)
    total = sum(len(v) for v in sp_namespaces.values())
    sp_path.write_text(json.dumps({
        "description": "v6 cluster_synth strategy points (RAW, no dedup). Synthesized per observation "
                       "cluster (gate_key regime, mixed verdicts). Built by synthesize_cell_sp.py.",
        "namespaces": sp_namespaces, "schema_version": SCHEMA_VERSION, "updated_at": now.isoformat(),
    }, indent=2))
    manifest = build_manifest(
        artifact=sp_path,
        config={"obs_store": args.obs_store_dir, "roles": args.roles, "sp_source": "cluster_synth",
                "cluster_mode": args.cluster_mode, "similarity_threshold": args.similarity_threshold},
        inputs=[str(obs_path)], created_from="synthesize_cell_sp.py", case_count=total,
        extra={"namespace_counts": {k: len(v) for k, v in sorted(sp_namespaces.items())}},
    )
    (out_dir / "manifest_sp.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(f"\nSP store has {total} strategy points across {len(sp_namespaces)} namespaces:", flush=True)
    for k in sorted(sp_namespaces):
        print(f"  {k}: {len(sp_namespaces[k])}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
