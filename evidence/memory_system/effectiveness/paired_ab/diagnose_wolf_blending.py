"""Blending follow-up (experiment_log.md "Interpreting the wolf/SK null" — user's qualitative
pushback, 2026-06-12): the stock `wolf_blending_rate` null is a METRIC ARTIFACT.

The stock metric (compute_metrics.py) is conditioned on wolf-elimination days only — a game where
wolves blend perfectly and are never caught contributes ZERO observations; it samples disaster
states exclusively. This script measures UNCONDITIONED blending from raw `day_resolutions`
(fraction of a living wolf's votes aligned with the day's eventual lynch, across ALL lynch days)
and tests the micro-mechanism behind the metric's design intent ("a wolf who dissents to protect
a piled partner is removed almost immediately the next day").

Promoted from /tmp 2026-06-12 after the first run; read-only over batch_results/ab_*.jsonl.

Findings on first run (2026-06-12):
- Unconditioned blending VALIDATES vs wolf win: r=+0.43 p=0.024 baseline-only; +0.20 p=0.003
  pooled n=220.
- Micro-mechanism confirmed: dissent on a wolf-elim day -> lynched next day 49% (32/65) vs
  31% (11/35) when blended.
- THE LEAK IS VISIBLE IN VOTES: wolf-memory arms blend WORSE (baseline 0.838 -> arms_wolf 0.643,
  rr_wolf 0.649). Anomalies kept honest: allon=0.761 (wolves also hold memory there) and a
  general dip across all arms vs baseline (some environment noise).
- Candidate metric promotion (freeze-safe, measurement-only): unconditioned blending into
  compute_metrics; sharp behavioral secondary for a night-only-memory arm.

    poetry run python evidence/memory_system/effectiveness/paired_ab/diagnose_wolf_blending.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO_ROOT))
from evaluation.src.core.stats import point_biserial  # noqa: E402

FILES = ["ab_baseline", "ab_baseline_recovered", "ab_arms_wolf", "ab_arms_town",
         "ab_arms_sk", "ab_rr_wolf", "ab_rr_town", "ab_rr_sk", "ab_allon"]


def load(name):
    out = []
    for line in (REPO_ROOT / "batch_results" / f"{name}.jsonl").read_text().splitlines():
        if line.strip():
            r = json.loads(line)
            if r.get("status") == "success":
                r["_arm"] = name
                out.append(r)
    return out


def wolf_ids(r):
    return {p for p, role in r["roles"].items() if role == "wolf"}


def unconditioned_blend(r):
    """Fraction of wolf votes aligned with the day's lynch, across ALL lynch days."""
    wolves = wolf_ids(r)
    aligned = total = 0
    for day in r["day_resolutions"]:
        target = day.get("voted_player")
        if target is None:
            continue
        for v in day["votes"]:
            if v["voter"] in wolves and v["voter"] != target:
                total += 1
                aligned += v["votee"] == target
    return aligned / total if total else None


def main() -> None:
    arms = {n: load(n) for n in FILES}
    pooled, seen = [], set()
    for recs in arms.values():
        for r in recs:
            key = ("baseline" if r["_arm"].startswith("ab_baseline") else r["_arm"],
                   r["game_id"])
            if key not in seen:
                seen.add(key)
                pooled.append(r)

    # --- 1a. validation: unconditioned blending vs wolf win ---
    base = [r for r in pooled if r["_arm"].startswith("ab_baseline")]
    for label, recs in [("pooled", pooled), ("baseline-only", base)]:
        wins, vals = [], []
        for r in recs:
            b = unconditioned_blend(r)
            if b is not None:
                wins.append(int(r["winner"] == "wolves"))
                vals.append(b)
        rr, pp = point_biserial(wins, vals)
        print(f"unconditioned blending vs wolf win ({label}): r={rr:+.2f} p={pp:.4f} n={len(vals)}")

    # --- 1b. per-arm means ---
    print("\nper-arm unconditioned blending:")
    groups = {"baseline": base}
    for n in FILES[2:]:
        groups[n] = arms[n]
    for name, recs in groups.items():
        bs = [b for b in (unconditioned_blend(r) for r in recs) if b is not None]
        ww = sum(r["winner"] == "wolves" for r in recs)
        print(f"  {name:14s} blend={sum(bs)/len(bs):.3f} (n={len(bs)})  wolf_wins={ww}/{len(recs)}")

    # --- 2. micro-mechanism: dissent on a wolf-elim day -> lynched next day? ---
    next_day_fate = {"dissent": [0, 0], "blend": [0, 0]}  # [lynched_next, total]
    for r in pooled:
        wolves = wolf_ids(r)
        by_day = {d["day"]: d for d in r["day_resolutions"]}
        for d in r["day_resolutions"]:
            target = d.get("voted_player")
            if target is None or d.get("voted_player_role") != "wolf":
                continue
            nxt = by_day.get(d["day"] + 1)
            for v in d["votes"]:
                voter = v["voter"]
                if voter not in wolves or voter == target:
                    continue
                kind = "blend" if v["votee"] == target else "dissent"
                next_day_fate[kind][1] += 1
                if nxt is not None and nxt.get("voted_player") == voter:
                    next_day_fate[kind][0] += 1
    print("\nmicro-mechanism: surviving wolf's vote on a wolf-elim day -> lynched next day?")
    for kind, (lynched, total) in next_day_fate.items():
        pct = lynched / total if total else float("nan")
        print(f"  {kind:8s}: {lynched}/{total} lynched next day ({pct:.0%})")


if __name__ == "__main__":
    main()
