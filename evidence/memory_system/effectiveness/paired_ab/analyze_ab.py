"""Paired memory A/B analysis — McNemar win-rate + validated-proxy comparison.

Reuses evaluation/src/core/stats.py (binomial_ci, point_biserial) and scipy.
McNemar/Wilcoxon are implemented locally here; per stats.py's own docstring they
belong in that module — promote them once stats.py is committed (kept out for now
to avoid editing a concurrently-edited uncommitted file).

Pairing (by game_id):
  - 20 recovered baseline ids -> winner from seed_set.json (WIN only; their
    computed_metrics aren't game_id-linkable -> proxies unpaired for these).
  - 10 fresh ids -> full record (winner + proxies) from the ab_baseline run.

Win-rate: paired McNemar over all 30. Proxies (validated basket only): unpaired
arm-vs-baseline distribution (Mann-Whitney, full N=30 each) + paired on the 10 fresh.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from scipy import stats as sp

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO))
from evaluation.src.core.stats import binomial_ci, mcnemar_exact  # noqa: E402

HERE = Path(__file__).resolve().parent
ARMS = {
    "wolf_only": ("wolves", REPO / "batch_results/ab_arms_wolf.jsonl"),
    "serial_killer_only": ("serial_killer", REPO / "batch_results/ab_arms_sk.jsonl"),
    "town_only": ("villagers", REPO / "batch_results/ab_arms_town.jsonl"),
}
BASELINE_FRESH = REPO / "batch_results/ab_baseline.jsonl"
# Established memory-off baseline (the 30 off games) for the unpaired proxy distribution.
BASELINE_OFF_FILES = [REPO / f"batch_results/v5_seed_b{i}.jsonl" for i in (1, 2, 3, 4)] + [
    REPO / "batch_results/v5_baseline_pad.jsonl"
]
SEED_SET = HERE / "seed_set.json"

# Validated proxies (evidence/metrics/proxy_win_monotonicity.md). Sign = expected
# direction vs villager/town win; SK proxy keyed to SK. Investigator rate proxies
# are intentionally EXCLUDED (failed monotonicity).
VALIDATED_PROXIES = [
    ("town_vote_accuracy", "+"),
    ("town_mislynch_rate", "-"),
    ("mislynches", "-"),
    ("correct_elimination_rate", "+"),
    ("serial_killer_lynched", "+"),
    ("sk_nights_survived", "+"),  # SK arm's core proxy
    ("healer_town_save_rate", "+"),
    ("vigilante_friendly_fire_shots", "-"),
]


def load(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(l) for l in path.read_text().splitlines() if l.strip()]


def main() -> int:
    seed = json.loads(SEED_SET.read_text())
    baseline_winner = {r["game_id"]: r["baseline_winner"] for r in seed["recovered"]}
    fresh_records = {r["game_id"]: r for r in load(BASELINE_FRESH)}
    for gid, rec in fresh_records.items():
        baseline_winner[gid] = rec.get("winner")
    baseline_off_metrics = [
        r["computed_metrics"] for f in BASELINE_OFF_FILES for r in load(f)
        if r.get("computed_metrics")
    ]

    lines = ["# Paired memory A/B — results", ""]
    lines.append(
        f"Baseline winners available for {len(baseline_winner)} game_ids "
        f"(20 recovered + {len(fresh_records)} fresh). Off proxy distribution: "
        f"N={len(baseline_off_metrics)} (established memory-off games).\n"
    )

    for arm, (faction, path) in ARMS.items():
        arm_recs = load(path)
        if not arm_recs:
            lines.append(f"## {arm} — no games yet\n")
            continue
        # Pair WIN by game_id (only games whose baseline winner we know).
        off_win, on_win, paired_gids = [], [], []
        for r in arm_recs:
            gid = r.get("game_id")
            if gid in baseline_winner and baseline_winner[gid] is not None:
                off_win.append(int(baseline_winner[gid] == faction))
                on_win.append(int(r.get("winner") == faction))
                paired_gids.append(gid)
        n = len(on_win)
        on_rate = sum(on_win) / n if n else 0.0
        off_rate = sum(off_win) / n if n else 0.0
        on_lo, on_hi = binomial_ci(sum(on_win), n) if n else (0, 0)
        off_lo, off_hi = binomial_ci(sum(off_win), n) if n else (0, 0)
        mc = mcnemar_exact(off_win, on_win)

        lines.append(f"## {arm} (faction = {faction}), N_paired = {n}\n")
        lines.append(
            f"- **Win rate:** off {off_rate:.0%} [{off_lo:.0%},{off_hi:.0%}] -> "
            f"on {on_rate:.0%} [{on_lo:.0%},{on_hi:.0%}]  (delta {on_rate-off_rate:+.0%})"
        )
        lines.append(
            f"- **McNemar (paired):** b(off-only)={mc.b_off_only}, "
            f"c(on-only)={mc.c_on_only}, discordant={mc.b_off_only + mc.c_on_only}, "
            f"**p={mc.p_value:.3f}**"
        )

        # Proxies: unpaired arm vs baseline-off distribution (Mann-Whitney).
        lines.append("- **Validated proxies (arm mean vs off mean, Mann-Whitney p):**")
        arm_metrics = [r["computed_metrics"] for r in arm_recs if r.get("computed_metrics")]
        for proxy, sign in VALIDATED_PROXIES:
            a = [m[proxy] for m in arm_metrics if m.get(proxy) is not None]
            o = [m[proxy] for m in baseline_off_metrics if m.get(proxy) is not None]
            if len(a) < 3 or len(o) < 3:
                continue
            am, om = sum(a) / len(a), sum(o) / len(o)
            try:
                u_p = sp.mannwhitneyu(a, o, alternative="two-sided").pvalue
            except ValueError:
                u_p = float("nan")
            lines.append(
                f"  - `{proxy}` ({sign}): on {am:.3f} vs off {om:.3f} "
                f"(delta {am-om:+.3f}, p={u_p:.3f}, n_on={len(a)})"
            )
        lines.append("")

    out = HERE / "report.md"
    out.write_text("\n".join(lines))
    print("\n".join(lines))
    print(f"\nWritten to {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
