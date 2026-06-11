"""Regenerate the statistical appendix in report.md / v5_baseline_proxy_analysis.md.

Every p-value and CI cited in those documents comes from this script — run it after
any batch data change and paste the output, so no stat in the record is hand-typed.

    poetry run python evidence/memory_system/effectiveness/regenerate_stats.py

Batch A/B data is colocated (batch_results/ here); the v5 arms live in the repo-root
batch_results/ data plane (classified by memory_config, not filename — see
v5_baseline_proxy_analysis.md).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from evaluation.src.core.stats import compare_proportions  # noqa: E402

BATCH_FILES = {
    "A (v3_deduped)": [
        HERE / "batch_results/werewolf_flashlite_3_v1.jsonl",
        HERE / "batch_results/werewolf_flashlite_3_v1_deduped.jsonl",
    ],
    "B (v4_action_phase)": [
        HERE / "batch_results/v4_action_phase_v2.jsonl",
        HERE / "batch_results/v4_action_phase_v2_wolf_only_all_enabled.jsonl",
        HERE / "batch_results/v4_action_phase_v2_all_enabled_remainder.jsonl",
    ],
}

V5_FILES = {
    "OFF": ["v5_seed_b1", "v5_seed_b2", "v5_seed_b3", "v5_seed_b4", "v5_baseline_pad"],
    "ON": ["v5_1_b1", "v5_1_b2", "v5_1_b3", "v5_1_b4"],
}


def load_records(paths: list[Path]) -> list[dict]:
    records = []
    for path in paths:
        for line in path.read_text().splitlines():
            if not line.strip():
                continue
            record = json.loads(line)
            if record.get("status") == "success":
                records.append(record)
    return records


def classify_condition(memory_config: dict) -> str:
    values = set(memory_config.values())
    if values == {False}:
        return "no_memory"
    if values == {True}:
        return "all_enabled"
    if memory_config.get("wolf") and not any(v for k, v in memory_config.items() if k != "wolf"):
        return "wolf_only"
    return "mixed"


def win_counts(records: list[dict], faction: str = "villagers") -> dict[str, tuple[int, int]]:
    counts: dict[str, list[int]] = {}
    for record in records:
        condition = classify_condition(record["memory_config"])
        wins, n = counts.setdefault(condition, [0, 0])
        counts[condition] = [wins + (record["winner"] == faction), n + 1]
    return {condition: (wins, n) for condition, (wins, n) in counts.items()}


def main() -> None:
    print("## Batch A/B (villager win rate, Fisher exact, 95% Clopper–Pearson CIs)\n")
    batch_counts = {}
    for batch, paths in BATCH_FILES.items():
        batch_counts[batch] = win_counts(load_records(paths))
    for batch, counts in batch_counts.items():
        baseline = counts["no_memory"]
        for condition in ("wolf_only", "all_enabled"):
            cmp = compare_proportions(*counts[condition], *baseline)
            print(f"{batch} {condition} vs no_memory — {cmp.row(condition, 'no_memory')}")
    a, b = batch_counts.values()
    print(f"baselines A vs B — {compare_proportions(*a['no_memory'], *b['no_memory']).row('A', 'B')}")
    print(
        "all_enabled A vs B — "
        f"{compare_proportions(*a['all_enabled'], *b['all_enabled']).row('A', 'B')}"
    )

    print("\n## v5 pilot (per-faction win rate, memory-ON vs memory-OFF)\n")
    arms = {
        arm: load_records([REPO_ROOT / "batch_results" / f"{name}.jsonl" for name in names])
        for arm, names in V5_FILES.items()
    }
    for arm, records in arms.items():
        conditions = {classify_condition(r["memory_config"]) for r in records}
        print(f"{arm}: N={len(records)} memory_config conditions={sorted(conditions)}")
    for faction in ("villagers", "serial_killer", "wolves"):
        on = sum(r["winner"] == faction for r in arms["ON"])
        off = sum(r["winner"] == faction for r in arms["OFF"])
        cmp = compare_proportions(on, len(arms["ON"]), off, len(arms["OFF"]))
        print(f"{faction}: {cmp.row('ON', 'OFF')}")


if __name__ == "__main__":
    main()
