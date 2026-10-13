"""The strategy-point dedup run dry on the 40-game store, under different pre-splits, against the readers'
duplicate groups (2026-10-13).

Record: evidence/memory_system/v8/experiment_log.md. The point dedup (batch dedup over each cell:
embedding clusters, then a KEEP/DISCARD call per cluster) splits a cell's points by the labels
synthesis gives them, (direction, honesty), before comparing any; 37 of the readers' 65 duplicate
groups crossed those labels. This runs it without writing, on a copy of the working store's 605
points, under each split, and records every group it would collapse; then compares the points it
would drop with the readers' 78.

  poetry run python evaluation/experiments/v8_sp_dedup_dry_run.py
"""

from __future__ import annotations

import glob
import json
import shutil
from pathlib import Path

MAIN = Path(__file__).resolve().parents[2]
WORKING = MAIN / "memory_stores/v8_reextract_synth"
READS = MAIN / "evidence/memory_system/v8/data/reextract/points"
OUT = MAIN / "evidence/memory_system/v8/data/reextract/dedup_dry_run"
SPLITS = {"direction_honesty": ("direction", "honesty"), "honesty": ("honesty",)}


def _readers() -> tuple[dict[str, str], list[dict]]:
    groups = [json.loads(line) for f in sorted(glob.glob(str(READS / "dups_part_*.jsonl")))
              for line in Path(f).read_text().splitlines()]
    drop = {k: g["keep"] for g in groups for k in g["keys"] if k != g["keep"]}
    return drop, groups


def run(split: tuple[str, ...], scratch: Path) -> list[dict]:
    """The groups the dedup would collapse under ``split``: {cell, survivor, dropped}."""
    from langgraph.store.memory import InMemoryStore

    from Agents.memory import dedup_gate
    from Agents.memory.consolidation.config import TickConfig
    from Agents.memory.batch_deduplication import operations
    from Agents.memory.batch_deduplication.config import BatchDedupRunConfig
    from Agents.memory.batch_deduplication.orchestration import run_batch_memory_dedup
    from Agents.memory.store import store as indexed

    if scratch.exists():
        shutil.rmtree(scratch)
    scratch.mkdir(parents=True)
    for name in ("observations.json", "strategy_points.json"):
        shutil.copy(WORKING / name, scratch / name)

    recorded: list[dict] = []
    original = operations._commit_survivor

    def record(target_store, namespace, survivor_key, value, source_keys, items_by_key, apply):
        recorded.append({"cell": f"{namespace[1]}/{namespace[2]}", "survivor": survivor_key,
                         "dropped": [k for k in source_keys if k != survivor_key]})
        return original(target_store, namespace, survivor_key, value, source_keys, items_by_key, False)

    saved_fields = dedup_gate._SP_SIGNATURE_FIELDS
    dedup_gate._SP_SIGNATURE_FIELDS = split
    operations._commit_survivor = record
    try:
        # the judge synthesis's own dedup uses (TickConfig.dedup_model), not the batch default (2.5 Pro)
        run_batch_memory_dedup(BatchDedupRunConfig(
            seed_store_dir=scratch, dump_store_dir=scratch, apply=False, incremental=False,
            memory_kinds=["strategy_points"], model=TickConfig().dedup_model),
            target_store=InMemoryStore(index=indexed.index_config))
    finally:
        dedup_gate._SP_SIGNATURE_FIELDS = saved_fields
        operations._commit_survivor = original
    return recorded


def main() -> None:
    reader_drop, reader_groups = _readers()
    OUT.mkdir(parents=True, exist_ok=True)
    summary = {}
    for name, split in SPLITS.items():
        groups = run(split, OUT / f"_scratch_{name}")
        shutil.rmtree(OUT / f"_scratch_{name}")
        dropped = {k for g in groups for k in g["dropped"]}
        caught = [g for g in reader_groups if len(set(g["keys"]) - dropped) <= 1]
        summary[name] = {"groups": len(groups), "points_dropped": len(dropped),
                         "of_readers_78": len(dropped & set(reader_drop)),
                         "not_in_readers": len(dropped - set(reader_drop)),
                         "reader_groups_fully_caught": len(caught)}
        (OUT / f"{name}.jsonl").write_text("".join(json.dumps(g) + "\n" for g in groups))
        print(name, summary[name])
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
