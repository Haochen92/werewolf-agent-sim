"""Inspect the SITUATION DIMENSIONS the synthesizer assigns — the retrieval key.

Re-synthesizes SK day_vote cluster 1 (the clean conditioned-directive cluster) on the credit arm and
prints the obs-cluster regime vs the H/D SPs' assigned situation dims, so we can see whether a
CROSS-REGIME conditioned directive gets tagged to a SINGLE regime (retrieval misalignment) or broadened.

  poetry run python evidence/v7_final/inspect_synth_dims.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from Agents.memory.batch_deduplication.config import BatchDedupRunConfig
from Agents.memory.persistence import memory_store_paths, seed_memory_from_json_files_cached
from Agents.memory.store import store
from Agents.memory.strategy_synthesis import cluster_observations_for_synth, synthesize_cluster_sps
from evaluation.src.studies.synth_deluck_ab import _credited_for_cell, _track_record

ROLE, PHASE = "serial_killer", "day_vote"
DIM_KEYS = ("players_alive", "is_swing", "criticality", "heat", "consensus", "consensus_texture",
            "target_landscape", "alive_bucket", "consensus_direction")


def _dims(d: dict) -> str:
    return "  ".join(f"{k}={d[k]!r}" for k in DIM_KEYS if k in d)


def main() -> int:
    obs_path, sp_path = memory_store_paths(Path("memory_stores/v6_1"))
    seed_memory_from_json_files_cached(observations_path=obs_path, strategy_points_path=sp_path,
                                       target_store=store, cache_dir=Path("memory_stores/v6_1"))
    config = BatchDedupRunConfig(similarity_threshold=0.70, cluster_mode="bounded", max_cluster_size=15)
    items, clusters = cluster_observations_for_synth(store, ("observations", ROLE, PHASE), config)
    live = [c for c in ([k for k in cl if k in items] for cl in clusters) if c]
    ckeys = live[0]
    tr = _track_record(_credited_for_cell(f"{ROLE}/{PHASE}"))

    print(f"=== CLUSTER 1 obs regimes ({len(ckeys)} obs) — what gate_key/regime this cluster is ===")
    for k in ckeys:
        v = items[k].value
        print(" obs:", _dims(v))

    for arm, trk in (("H halo", ""), ("D credit-aware", tr)):
        sps = synthesize_cluster_sps(ROLE, PHASE, ckeys, items, max_retries=1, track_record=trk)
        print(f"\n=== {arm}: {len(sps)} SP(s) ===")
        for sp in sps:
            d = sp.model_dump(mode="json")
            print(" SITUATION DIMS:", _dims(d))
            print(" composed_situation:", getattr(sp, "composed_situation", "")[:300])
            print(" ACTION:", sp.action[:240])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
