"""v7 — leverage-anchor separation (extraction-selection viability, plan §2/§3D/§4). Zero spend.

Extraction must SELECT which moments to mine. Today: flat 4–8/role quota + `net_verdict`, which is an
OUTCOME HALO (knows "your side won", not "this move mattered") → can't select pivotal moments. v7's fix:
anchor selection on a DETERMINISTIC, outcome-independent LEVERAGE signal (is_swing / distance_to_parity)
— mine the turns that mattered, not a flat quota.

This tests whether leverage SEPARATES pivotal from incidental: does the decision→outcome coupling
CONCENTRATE at high-leverage boards? Operationalized on town day-votes (clean proxy): the coupling =
P(town wins | vote HIT a threat) − P(town wins | vote MISSED), measured WITHIN leverage strata
(is_swing, distance_to_parity, alive-bucket). If the gap is large at high-leverage and ~0 at
low-leverage, leverage identifies the decisive turns → anchor viable. Flat across strata → anchor adds
nothing.

Board reconstruction + query_criticality reused from the gating-efficacy screen. 180 v6ab games.
"""

import glob
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))  # repo root, for `evaluation.src.*`

from evaluation.src.loop.decision_scoring import query_criticality, score_vote  # noqa: E402

TOWN_ROLES = {"villager", "healer", "investigator", "vigilante"}
ARMS = sorted(glob.glob("batch_results/v6ab_*.jsonl"))


def alive_entering_day(g, day):
    dead = set()
    for d in g["day_resolutions"]:
        if d.get("day", 0) < day and d.get("voted_player"):
            dead.add(d["voted_player"])
    for n in g["night_resolutions"]:
        if n.get("day", 0) < day:
            dead.update(n.get("deaths") or [])
    return [p for p in g["roles"] if p not in dead]


def gap(rows):
    """rows = list of (hit_threat 0/1, town_won 0/1). Returns (P(win|hit), P(win|miss), Δ, n)."""
    hits = [w for h, w in rows if h]
    miss = [w for h, w in rows if not h]
    if not hits or not miss:
        return None
    ph, pm = sum(hits) / len(hits), sum(miss) / len(miss)
    return ph, pm, ph - pm, len(rows)


def report(label, rows):
    g = gap(rows)
    if g is None:
        print(f"  {label:22s} n={len(rows):4d} — one side empty, skip")
        return
    ph, pm, d, n = g
    print(f"  {label:22s} n={n:4d}  P(win|hit)={ph:.2f}  P(win|miss)={pm:.2f}  Δ={d:+.2f}")


def main():
    rows = []  # (hit, won, is_swing, dist, alive)
    for f in ARMS:
        for line in open(f):
            if not line.strip():
                continue
            g = json.loads(line)
            roles = g["roles"]
            winner = (g.get("computed_metrics") or {}).get("winner") or g.get("winner")
            town_won = int(winner == "villagers")
            for d in g["day_resolutions"]:
                day = d.get("day", 0)
                alive = alive_entering_day(g, day)
                if len(alive) < 2:
                    continue
                _, dist, swing = query_criticality(alive, roles)
                n_alive = len(alive)
                for v in d.get("votes", []):
                    if roles.get(v["voter"]) not in TOWN_ROLES:
                        continue
                    ov = score_vote(v["votee"], roles)
                    if ov.is_abstain:
                        continue
                    rows.append((int(ov.hit_threat), town_won, bool(swing), dist, n_alive))

    print(f"town day-votes: {len(rows)}\n")
    print("=== overall coupling (the G2 baseline) ===")
    report("ALL", [(h, w) for h, w, *_ in rows])

    print("\n=== by is_swing leverage (one elimination flips the winner) ===")
    report("is_swing=True (HIGH)", [(h, w) for h, w, s, *_ in rows if s])
    report("is_swing=False (low)", [(h, w) for h, w, s, *_ in rows if not s])

    print("\n=== by distance_to_parity (near parity = high leverage) ===")
    report("dist<=1 (HIGH)", [(h, w) for h, w, s, dist, a in rows if dist <= 1])
    report("dist==2 (mid)", [(h, w) for h, w, s, dist, a in rows if dist == 2])
    report("dist>=3 (low)", [(h, w) for h, w, s, dist, a in rows if dist >= 3])

    print("\n=== by alive-bucket (late = high leverage) ===")
    report("late <=4 (HIGH)", [(h, w) for h, w, s, dist, a in rows if a <= 4])
    report("mid 5-7", [(h, w) for h, w, s, dist, a in rows if 5 <= a <= 7])
    report("early 8-9 (low)", [(h, w) for h, w, s, dist, a in rows if a >= 8])

    print("\n=== read (two notions of 'pivotal') ===")
    print("  (a) MARGINAL Δ (how much a good vote ADDS): if flat across strata, leverage does NOT rank")
    print("      town-votes by impact — they're uniformly pivotal-by-Δ.")
    print("  (b) DECISIVENESS = the P(win|miss) FLOOR: if it drops toward 0 at high leverage, a MISS is")
    print("      fatal there → leverage separates DO-OR-DIE turns (the decision determined the game).")
    print("  Anchor viability lives in (b): mine the low-miss-floor turns (decisive), independent of who")
    print("  won → fixes the net_verdict halo in the irreversibility sense, even if (a) is flat.")


if __name__ == "__main__":
    main()
