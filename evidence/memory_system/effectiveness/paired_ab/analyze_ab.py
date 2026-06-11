"""Paired memory A/B analysis — McNemar win-rate + validated-proxy comparison.

Reuses evaluation/src/core/stats.py (binomial_ci, mcnemar_exact, wilcoxon_paired).

All baseline games are run FRESH in the SAME epoch as the arms. The original
baseline was a different epoch — model drift / variance shifted its win
distribution (Fisher p=0.0028 vs the fresh baseline), so it is NOT used here.
Every baseline game carries game_id + winner + computed_metrics, so both win and
proxies pair on game_id (identical role draw, verified).

Win-rate: paired McNemar over matched game_ids. Proxies (monotonicity-validated
basket only): paired delta + Wilcoxon signed-rank on the same matched pairs.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO))

from evaluation.src.core.stats import binomial_ci, mcnemar_exact, wilcoxon_paired  # noqa: E402

HERE = Path(__file__).resolve().parent
ARMS = {
    "wolf_only": ("wolves", REPO / "batch_results/ab_arms_wolf.jsonl"),
    "serial_killer_only": ("serial_killer", REPO / "batch_results/ab_arms_sk.jsonl"),
    "town_only": ("villagers", REPO / "batch_results/ab_arms_town.jsonl"),
}
# Same-epoch fresh baseline = 10 fresh + 20 recovered-id reruns (both current epoch).
BASELINE_FILES = [
    REPO / "batch_results/ab_baseline.jsonl",
    REPO / "batch_results/ab_baseline_recovered.jsonl",
]

# Validated proxies (evidence/metrics/proxy_win_monotonicity.md). Sign = expected
# direction vs the town/villager win; sk_nights_survived keyed to SK. Investigator
# rate proxies are intentionally EXCLUDED (failed monotonicity).
VALIDATED_PROXIES = [
    ("town_vote_accuracy", "+"),
    ("town_mislynch_rate", "-"),
    ("mislynches", "-"),
    ("correct_elimination_rate", "+"),
    ("serial_killer_lynched", "+"),
    ("sk_nights_survived", "+"),
    ("healer_town_save_rate", "+"),
    ("vigilante_friendly_fire_shots", "-"),
]


def load(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def main() -> int:
    baseline = {
        r["game_id"]: r
        for f in BASELINE_FILES
        for r in load(f)
        if r.get("game_id")
    }

    lines = ["# Paired memory A/B — results", ""]
    lines.append(
        f"Same-epoch fresh baseline: {len(baseline)} games (game_id-matched, full proxies).\n"
    )

    for arm, (faction, path) in ARMS.items():
        arm_recs = [r for r in load(path) if r.get("game_id") in baseline]
        if not arm_recs:
            lines.append(f"## {arm} — no matched games yet\n")
            continue

        off_win = [int(baseline[r["game_id"]].get("winner") == faction) for r in arm_recs]
        on_win = [int(r.get("winner") == faction) for r in arm_recs]
        n = len(on_win)
        on_rate, off_rate = sum(on_win) / n, sum(off_win) / n
        on_ci, off_ci = binomial_ci(sum(on_win), n), binomial_ci(sum(off_win), n)
        mc = mcnemar_exact(off_win, on_win)

        lines.append(f"## {arm} (faction = {faction}), N_paired = {n}\n")
        lines.append(
            f"- **Win rate:** off {off_rate:.0%} [{off_ci[0]:.0%},{off_ci[1]:.0%}] -> "
            f"on {on_rate:.0%} [{on_ci[0]:.0%},{on_ci[1]:.0%}] (delta {on_rate-off_rate:+.0%})"
        )
        lines.append(
            f"- **McNemar (paired):** b(off-only)={mc.b_off_only}, c(on-only)={mc.c_on_only}, "
            f"discordant={mc.b_off_only + mc.c_on_only}, **p={mc.p_value:.3f}**"
        )

        lines.append("- **Validated proxies (paired off->on mean, Wilcoxon p):**")
        for proxy, sign in VALIDATED_PROXIES:
            off_vals, on_vals = [], []
            for r in arm_recs:
                ov = baseline[r["game_id"]].get("computed_metrics", {}).get(proxy)
                nv = (r.get("computed_metrics") or {}).get(proxy)
                if ov is not None and nv is not None:
                    off_vals.append(ov)
                    on_vals.append(nv)
            if len(on_vals) < 3:
                continue
            om, am = sum(off_vals) / len(off_vals), sum(on_vals) / len(on_vals)
            _, w_p = wilcoxon_paired(off_vals, on_vals)
            lines.append(
                f"  - `{proxy}` ({sign}): off {om:.3f} -> on {am:.3f} "
                f"(delta {am-om:+.3f}, Wilcoxon p={w_p:.3f}, n={len(on_vals)})"
            )
        lines.append("")

    out = HERE / "report.md"
    out.write_text("\n".join(lines))
    print("\n".join(lines))
    print(f"\nWritten to {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
