"""Group sizes of the lesson (strategy point) dedup partition, before and after stage joined the key
(2026-10-28; no model calls).

The point dedup groups a cell's lessons by a key before the judge sees any pair. The old key was the
lesson's move labels (direction, honesty); the new one adds the stage facts the live stage filter
compares (alive bucket, pack partner lost, limited ability has a use left). This counts, per store, the
partitions under each key, their sizes and the singletons (a lesson alone in its partition can never be
deduplicated), how many lessons lack each stage fact, and how many of the readers' 65 duplicate groups
(2026-10-13) the new key splits by stage, and whether those really span stages. It also counts how many
of the judge's dry-run drops (2026-10-13) crossed stages.

Record: evidence/dedup/report.md (layers 2 and 5, notes of 2026-10-28).

Run: poetry run python evaluation/experiments/sp_dedup_stage_partition_check.py
"""

from __future__ import annotations

import glob
import json
from collections import Counter, defaultdict
from pathlib import Path

from Agents.memory.dedup_gate import _SP_SIGNATURE_FIELDS, sp_gate_key
from Agents.memory.retrieval.dimension_gating import stage_facts

MAIN = Path(__file__).resolve().parents[2]
STORES = {
    "v8_reextract_synth (605, the dry run's store)": MAIN / "memory_stores/v8_reextract_synth/strategy_points.json",
    "ten_seat_v2 (published)": MAIN / "memory_stores/ten_seat_v2/strategy_points.json",
}
READERS = MAIN / "evidence/memory_system/v8/data/reextract/points"
DRY_RUN = MAIN / "evidence/memory_system/v8/data/reextract/dedup_dry_run/direction_honesty.jsonl"
FACTS = ("alive", "partner", "uses")


def main() -> None:
    """Print the group-size table for each store, then the readers'-groups and dry-run counts."""
    for name, path in STORES.items():
        lessons = load_lessons(path)
        print(f"\n== {name}: {len(lessons)} lessons, {len({l['cell'] for l in lessons.values()})} cells")
        print_partition_table(lessons)
        print_missing_facts(lessons)
    lessons = load_lessons(STORES["v8_reextract_synth (605, the dry run's store)"])
    print_readers_groups(lessons)
    print_dry_run_drops(lessons)


def load_lessons(path: Path) -> dict[str, dict]:
    """Read a store dump into {key: {cell, value}}.

    Args:
        path: a ``strategy_points.json`` store dump.

    Returns:
        Each lesson's cell ("role/phase") and stored value, by key.
    """
    dump = json.loads(path.read_text())
    return {item["key"]: {"cell": "/".join(item["namespace"][1:]), "value": item["value"]}
            for items in dump["namespaces"].values() for item in items}


def old_key(value: dict) -> tuple:
    """The partition key before 2026-10-28: the move labels only."""
    return tuple(value.get(field) for field in _SP_SIGNATURE_FIELDS)


def partitions(lessons: dict[str, dict], key_fn) -> list[list[str]]:
    """Group lesson keys by (cell, key_fn(value)) — the batch dedup's per-cell pre-partition.

    Args:
        lessons: {key: {cell, value}} from ``load_lessons``.
        key_fn: the partition key on a stored value.

    Returns:
        The partitions, each a list of lesson keys.
    """
    groups: dict[tuple, list[str]] = defaultdict(list)
    for key, lesson in lessons.items():
        groups[(lesson["cell"], key_fn(lesson["value"]))].append(key)
    return list(groups.values())


def print_partition_table(lessons: dict[str, dict]) -> None:
    """One row per key: partitions, size distribution, singletons, lessons in a partition of 2+."""
    print(f"  {'key':<6}{'partitions':>11}{'singletons':>11}{'in 2+':>7}{'max':>5}{'median':>8}  sizes (size:count)")
    for label, key_fn in (("old", old_key), ("new", sp_gate_key)):
        sizes = sorted(len(p) for p in partitions(lessons, key_fn))
        dist = Counter(sizes)
        singles = dist[1]
        median = sizes[len(sizes) // 2]
        shown = " ".join(f"{s}:{dist[s]}" for s in sorted(dist))
        print(f"  {label:<6}{len(sizes):>11}{singles:>11}{len(lessons) - singles:>7}{sizes[-1]:>5}{median:>8}  {shown}")


def print_missing_facts(lessons: dict[str, dict]) -> None:
    """How many lessons lack each stage fact: in all, and in a cell where another lesson has it (the
    partial case, where the missing lesson now sits apart from the ones that have it)."""
    facts = {key: stage_facts(lesson["value"].get("dimensions") or {}) for key, lesson in lessons.items()}
    cell_has = defaultdict(set)
    for key, lesson in lessons.items():
        for fact, value in zip(FACTS, facts[key]):
            if value is not None:
                cell_has[lesson["cell"]].add(fact)
    for i, fact in enumerate(FACTS):
        missing = [key for key in lessons if facts[key][i] is None]
        partial = [key for key in missing if fact in cell_has[lessons[key]["cell"]]]
        print(f"  lacks {fact:<8} {len(missing):>4}   of them in a cell where others have it: {len(partial)}")


def print_readers_groups(lessons: dict[str, dict]) -> None:
    """How many of the readers' duplicate groups the new key splits, and whether by a real stage
    difference (both sides carry the fact and it differs) or only by a fact one side lacks."""
    groups = [json.loads(line) for f in sorted(glob.glob(str(READERS / "dups_part_*.jsonl")))
              for line in Path(f).read_text().splitlines() if line.strip()]
    split_old = split_new = by_stage_only = real_stage = 0
    differing, newly_differing = Counter(), Counter()
    for group in groups:
        values = [lessons[k]["value"] for k in group["keys"] if k in lessons]
        old_split = len({old_key(v) for v in values}) > 1
        new_split = len({sp_gate_key(v) for v in values}) > 1
        split_old += old_split
        split_new += new_split
        stages = [stage_facts(v.get("dimensions") or {}) for v in values]
        crosses = [f for i, f in enumerate(FACTS) if len({s[i] for s in stages if s[i] is not None}) > 1]
        if len(set(stages)) > 1:
            real_stage += bool(crosses)
            differing.update(crosses or ["missing only"])
        if new_split and not old_split:
            by_stage_only += 1
            newly_differing.update(crosses or ["missing only"])
    print(f"\n== readers' duplicate groups: {len(groups)}")
    print(f"  split by the old key (labels): {split_old}")
    print(f"  split by the new key:          {split_new}  (newly split, by stage alone: {by_stage_only})")
    print(f"  span stages on a fact both sides carry: {real_stage}; facts that differ: {dict(differing)}")
    print(f"  the newly split groups' differing facts: {dict(newly_differing)}")


def print_dry_run_drops(lessons: dict[str, dict]) -> None:
    """Of the judge's dry-run drops under the old key, how many the new key would never show it."""
    rows = [json.loads(line) for line in DRY_RUN.read_text().splitlines() if line.strip()]
    drops = [(r["survivor"], k) for r in rows for k in r["dropped"]]
    crossing = [d for d in drops
                if sp_gate_key(lessons[d[0]]["value"]) != sp_gate_key(lessons[d[1]]["value"])]
    print(f"\n== dry-run drops (2026-10-13, labels key): {len(drops)}; across the new key's partitions: {len(crossing)}")


if __name__ == "__main__":
    main()
