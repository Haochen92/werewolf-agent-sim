"""Proxy-vs-win monotonicity check (the validation step deferred in experiment_log.md).

For each de-lucked proxy in `computed_metrics`, correlate it (point-biserial) with its
OWN faction's win across the v5 games that already exist (30 memory-off + 20 memory-on;
see evidence/memory_system/effectiveness/v5_baseline_proxy_analysis.md for arm definitions).
A proxy earns trust if its correlation sign matches the design intent in experiment_log.md;
wrong-sign or ~zero proxies should not carry win-rate narratives.

Reported twice: pooled (all 50 games — more N, but the memory treatment moves both proxy
and win, which can inflate r) and memory-OFF only (30 games, treatment-free).

    poetry run python evidence/metrics/proxy_win_monotonicity.py

Output: prints the markdown table that lives in proxy_win_monotonicity.md.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from evaluation.src.core.stats import point_biserial  # noqa: E402

OFF_FILES = ["v5_seed_b1", "v5_seed_b2", "v5_seed_b3", "v5_seed_b4", "v5_baseline_pad"]
ON_FILES = ["v5_1_b1", "v5_1_b2", "v5_1_b3", "v5_1_b4"]

# proxy -> (own faction, expected sign per the design intent in experiment_log.md).
# Sign None = descriptive/context metric, no monotonicity claim to validate.
PROXIES: dict[str, tuple[str, str | None]] = {
    # town decision quality
    "correct_elimination_rate": ("villagers", "+"),
    "mislynches": ("villagers", "-"),
    "town_mislynch_rate": ("villagers", "-"),
    "town_vote_accuracy": ("villagers", "+"),
    "serial_killer_lynched": ("villagers", "+"),
    "wolf_elimination_rate": ("villagers", "+"),
    "power_roles_killed_by_wolves": ("villagers", "-"),
    # healer
    "healer_save_rate": ("villagers", "+"),
    "healer_town_save_rate": ("villagers", "+"),
    "healer_friendly_fire_save_rate": ("villagers", "-"),
    "healer_wolf_block_rate": ("villagers", "+"),
    # investigator
    "investigator_threat_find_rate": ("villagers", "+"),
    "investigator_threat_find_lift": ("villagers", "+"),
    "investigator_wolf_find_rate": ("villagers", "+"),
    "investigator_wolves_found": ("villagers", "+"),
    "investigator_found_wolf_day": ("villagers", "-"),
    # vigilante
    "vigilante_correct_shot_rate": ("villagers", "+"),
    "vigilante_evil_shots": ("villagers", "+"),
    "vigilante_friendly_fire_shots": ("villagers", "-"),
    "vigilante_bullets_unused": ("villagers", None),
    "vigilante_shots_taken": ("villagers", None),
    # wolves
    "wolf_blending_rate": ("wolves", "+"),
    "wolf_dissent_rate": ("wolves", "-"),
    "wolf_steering_rate": ("wolves", "+"),
    "wolf_power_role_targeting_rate": ("wolves", "+"),
    "wolf_killed_healer_day": ("wolves", "-"),
    "wolf_killed_investigator_day": ("wolves", "-"),
    # serial killer
    "sk_nights_survived": ("serial_killer", "+"),
    "sk_kills_landed": ("serial_killer", None),
    # context
    "game_length": ("villagers", None),
    "tie_count": ("villagers", None),
    "no_vote_count": ("villagers", None),
}


def load(names: list[str]) -> list[dict]:
    records = []
    for name in names:
        path = REPO_ROOT / "batch_results" / f"{name}.jsonl"
        for line in path.read_text().splitlines():
            if not line.strip():
                continue
            record = json.loads(line)
            if record.get("status") == "success":
                records.append(record)
    return records


def correlate(records: list[dict], proxy: str, faction: str) -> tuple[float, float, int]:
    wins, values = [], []
    for record in records:
        value = record["computed_metrics"].get(proxy)
        if isinstance(value, bool):
            value = int(value)
        if not isinstance(value, (int, float)):
            continue
        wins.append(int(record["winner"] == faction))
        values.append(float(value))
    r, p = point_biserial(wins, values)
    return r, p, len(values)


def fmt(r: float, p: float, n: int) -> str:
    if r != r:  # nan — degenerate (constant proxy or single-class outcome)
        return f"— (n={n})"
    return f"{r:+.2f} (p={p:.3f}, n={n})"


def verdict(expected: str | None, r: float, p: float) -> str:
    if expected is None:
        return "context"
    if r != r:
        return "degenerate"
    sign = "+" if r > 0 else "-"
    if sign != expected:
        return "⚠️ WRONG SIGN" + (" (sig.)" if p < 0.05 else "")
    return "ok (sig.)" if p < 0.05 else "ok (weak)"


def main() -> None:
    off = load(OFF_FILES)
    pooled = off + load(ON_FILES)
    print("| proxy | faction | expected | pooled r (N=50) | OFF-only r (N=30) | verdict (pooled) |")
    print("|---|---|---|---|---|---|")
    for proxy, (faction, expected) in PROXIES.items():
        rp, pp, np_ = correlate(pooled, proxy, faction)
        ro, po, no = correlate(off, proxy, faction)
        print(
            f"| `{proxy}` | {faction} | {expected or '·'} | {fmt(rp, pp, np_)} "
            f"| {fmt(ro, po, no)} | {verdict(expected, rp, pp)} |"
        )


if __name__ == "__main__":
    main()
