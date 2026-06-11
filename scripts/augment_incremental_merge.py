"""Incremental-merge inspection for an augmented store — measures keep-inflation.

The online dedup that lands augment items is KEEP/DISCARD-only (no merge), so its
"kept" count over-states distinctness: a near-duplicate that should merge into an
existing item is kept as a SEPARATE entry instead. This script measures how much
of that inflation a merge pass would remove — using the INCREMENTAL guard, not a
full batch dedup: only clusters that contain a NEW (augment-added) key are
litigated; clusters of only old v5_0 items stay frozen (so v5_0 is never
re-litigated against itself — avoids the non-convergent erosion).

It does NOT modify any production code or any production store. It seeds the
augmented store into an in-memory store, derives the new keys by diffing the
augmented namespace against the base (v5_0) namespace (online dedup only ADDS
keys, so the difference is exactly the augment additions), and calls the existing
`dedup_namespace(..., new_keys=...)`. Default is a DRY RUN (apply=False): it
reports the merges that WOULD happen and writes nothing. With --apply it dumps to
a NEW throwaway dir you can delete to revert.

  poetry run python scripts/augment_incremental_merge.py --cells investigator:day_vote
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from Agents.memory.batch_deduplication import dedup_namespace
from Agents.memory.batch_deduplication.config import BatchDedupRunConfig
from Agents.memory.persistence import (
    dump_memory_to_json_files,
    memory_store_paths,
    seed_memory_from_json_files_cached,
)
from Agents.memory.store import store

DEFAULT_BASE = "memory_stores/v5_0"
DEFAULT_AUGMENTED = "memory_stores/v5_0_augmented"
DEFAULT_OUTPUT = "memory_stores/v5_0_augmented_merged"
KINDS = ("observations", "strategy_points")


def namespace_keys_from_json(store_dir: Path, kind: str, role: str, phase: str) -> set[str]:
    """Read the item keys of one namespace straight from a dumped store JSON."""
    obs_path, sp_path = memory_store_paths(store_dir)
    path = obs_path if kind == "observations" else sp_path
    payload = json.loads(Path(path).read_text())
    ns_key = f"{kind}/{role}/{phase}"
    return {item.get("key") for item in payload.get("namespaces", {}).get(ns_key, []) if item.get("key")}


def parse_cells(raw: list[str]) -> list[tuple[str, str]]:
    out = []
    for tok in raw:
        role, phase = tok.split(":", 1)
        out.append((role.strip(), phase.strip()))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cells", nargs="+", required=True, help="role:phase tokens")
    ap.add_argument("--base-store-dir", default=DEFAULT_BASE)
    ap.add_argument("--augmented-store-dir", default=DEFAULT_AUGMENTED)
    ap.add_argument("--apply", action="store_true",
                    help="persist the merged store to --output-store-dir (revertible: rm the dir)")
    ap.add_argument("--output-store-dir", default=DEFAULT_OUTPUT)
    ap.add_argument("--similarity-threshold", type=float, default=None,
                    help="override batch similarity threshold")
    args = ap.parse_args()

    cells = parse_cells(args.cells)
    base_dir = Path(args.base_store_dir)
    aug_dir = Path(args.augmented_store_dir)

    # Seed the augmented store into the in-memory store; clusters form over it.
    obs_path, sp_path = memory_store_paths(aug_dir)
    print(f"Seeding augmented store from {aug_dir} ...")
    info = seed_memory_from_json_files_cached(
        observations_path=obs_path, strategy_points_path=sp_path,
        target_store=store, cache_dir=aug_dir,
    )
    print(f"  seeded ({'cache' if info.get('from_cache') else 'api'})")

    cfg_kwargs = dict(
        seed_store_dir=aug_dir,
        dump_store_dir=Path(args.output_store_dir),
        apply=args.apply,
        incremental=True,
    )
    if args.similarity_threshold is not None:
        cfg_kwargs["similarity_threshold"] = args.similarity_threshold

    report: dict[str, dict] = {}
    for role, phase in cells:
        label = f"{role}/{phase}"
        report[label] = {}
        for kind in KINDS:
            base_keys = namespace_keys_from_json(base_dir, kind, role, phase)
            aug_keys = namespace_keys_from_json(aug_dir, kind, role, phase)
            new_keys = aug_keys - base_keys
            print(f"\n{label} [{kind}]: base={len(base_keys)} augmented={len(aug_keys)} "
                  f"new(augment-added)={len(new_keys)}")
            config = BatchDedupRunConfig(
                memory_kinds=[kind], selected_roles=[role], **cfg_kwargs,
            )
            stats = dedup_namespace(store, kind, role, phase, config, new_keys=new_keys)
            s = stats.model_dump(mode="json")
            report[label][kind] = {
                "base": len(base_keys),
                "augmented_online_kept": len(aug_keys),
                "new_keys": len(new_keys),
                "stats": s,
            }
            print(f"  clusters touching a new key: {s.get('clusters')} | "
                  f"merged: {s.get('merged')} | discarded: {s.get('discarded')} | "
                  f"items: {s.get('items')} | dry_run: {s.get('dry_run')}")

    if args.apply:
        out_dir = Path(args.output_store_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        out_obs, out_sp = memory_store_paths(out_dir)
        dump_memory_to_json_files(observations_path=out_obs, strategy_points_path=out_sp,
                                  target_store=store)
        print(f"\n[--apply] merged store dumped to {out_dir} (rm to revert)")

    out_json = Path("evidence/memory_system/augmentation/incremental_merge_report.json")
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(report, indent=2))

    print("\n================ INCREMENTAL MERGE INSPECTION ================")
    print(f"{'cell':24} {'kind':14} {'base':>5} {'online':>6} {'new':>4} {'merged':>6} {'true_net_new':>12}")
    for label, kinds in report.items():
        for kind, r in kinds.items():
            merged = r["stats"].get("merged") or 0
            true_net = r["new_keys"] - merged
            print(f"{label:24} {kind:14} {r['base']:>5} {r['augmented_online_kept']:>6} "
                  f"{r['new_keys']:>4} {merged:>6} {true_net:>12}")
    print("\n'online' kept inflates net-new; 'merged' = augment keeps a merge pass "
          "would absorb; 'true_net_new' ≈ new_keys - merged is the real variety added.")
    if not args.apply:
        print("[dry run] nothing written to any store; rm nothing needed.")
    print(f"Report: {out_json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
