"""v7 (d) — two FREE deterministic measurements (zero spend) to size the design before tagger spend.

M1 — DAY-VOTE ENDPOINT credit + DEFENSE-HEAT coverage. Credits EVERY followed discussion SP by the day's
faction-relative lynch outcome (the team-aware consensus endpoint — covers all turns, not just
accusatory). Reports coverage, separation, held-out reproduction. Plus: what fraction of discussion turns
are 'under heat' (player received accusations) = the defense axis's reach.

M2 — PART-3 FREQUENCY. How often is a player NIGHT-TARGETED (investigator/vigilante/SK/wolf) while drawing
LOW visible day-heat = the upper-bound size of the vote-invisible 'hidden read' exposure (a read formed
on a player, acted on at night, never voiced in discussion). By target-role-class + targeter. Tells us if
the night-exposure axis (A3) is worth wiring or a rare edge case. (Deterministic upper bound; the agent
night-reasoning (A4) would refine attribution.)

  poetry run python evidence/v7_final/discussion_coverage_check.py
"""

import glob
import json
import os
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from evaluation.src.experiments.credit_backfill import VERDICT_VALUE, _vote_credit  # noqa: E402

DUMPS = "batch_results/*v6ab*.jsonl"
SHRINK_K = 5
POWER = {"investigator", "healer", "vigilante"}
DECEIVER = {"wolf", "serial_killer"}


def _heat_map(day_channel) -> dict:
    """(day, player) -> count of accusations RECEIVED."""
    h = defaultdict(int)
    for m in day_channel or []:
        for t in m.get("addressed_targets") or []:
            if t.get("stance") == "accusation" and t.get("target"):
                h[(m.get("day"), t["target"])] += 1
    return h


def _spoke(day_channel) -> set:
    return {(m.get("day"), m.get("player")) for m in day_channel or [] if not m.get("passed")}


def _pearson(xs, ys):
    n = len(xs)
    if n < 3:
        return float("nan")
    mx, my = sum(xs) / n, sum(ys) / n
    cov = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    vx = sum((x - mx) ** 2 for x in xs) ** 0.5
    vy = sum((y - my) ** 2 for y in ys) ** 0.5
    return cov / (vx * vy) if vx and vy else float("nan")


def main() -> int:
    # accumulators
    base_sum, base_n = defaultdict(float), defaultdict(int)           # M1 day-vote baseline per role
    led = {0: defaultdict(lambda: [0, 0.0]), 1: defaultdict(lambda: [0, 0.0])}
    cov = {"disc_turns": 0, "under_heat": 0}                          # M1 defense coverage
    night = defaultdict(lambda: defaultdict(lambda: [0, 0]))          # M2: targeter -> class -> [total, no_heat]

    for dump in sorted(glob.glob(DUMPS)):
        for line in open(dump):
            if not line.strip():
                continue
            g = json.loads(line)
            roles, path = g.get("roles"), g.get("eval_cases_path")
            if not roles:
                continue
            gid = str(g.get("game_id"))
            lynch = {dr.get("day"): dr.get("voted_player") for dr in g.get("day_resolutions", [])}
            heat = _heat_map(g.get("day_channel"))
            spoke = _spoke(g.get("day_channel"))

            # ---- M2: night targetings ----
            for nr in g.get("night_resolutions", []):
                d = nr.get("day")
                for targeter, tgt in (("investigator", nr.get("investigator_target")),
                                      ("vigilante", nr.get("vigilante_target")),
                                      ("serial_killer", nr.get("serial_killer_target")),
                                      ("wolves", nr.get("wolves_target"))):
                    if not tgt or tgt in ("hold_fire", "abstain") or tgt not in roles:
                        continue
                    if (d, tgt) not in spoke:   # only players with discussion presence that day
                        continue
                    role = roles[tgt]
                    cls = "power" if role in POWER else "deceiver" if role in DECEIVER else "villager"
                    night[targeter][cls][0] += 1
                    if heat.get((d, tgt), 0) == 0:
                        night[targeter][cls][1] += 1

            # ---- M1: day-vote endpoint credit over discussion eval-cases ----
            if not path or not os.path.exists(path):
                continue
            for cl in open(path):
                if not cl.strip():
                    continue
                env = json.loads(cl)
                if env.get("kind") != "agent_action_eval":
                    continue
                ec = (env.get("output") or {}).get("eval_case")
                if not ec or ec.get("action_phase") != "day_discussion":
                    continue
                d, R, P = ec.get("day"), ec["player_role"], ec.get("player_id")
                v = VERDICT_VALUE[_vote_credit(R, lynch.get(d), roles)]   # team-aware day-vote outcome
                if not ec.get("memory_enabled"):
                    base_sum[R] += v
                    base_n[R] += 1
                    continue
                cov["disc_turns"] += 1
                if heat.get((d, P), 0) >= 1:
                    cov["under_heat"] += 1
                if not ec.get("strategy_verdicts"):
                    continue
                b = base_sum[R] / base_n[R] if base_n[R] else 0.0
                h, idx = _half(gid), ec.get("strategy_index_to_key") or {}
                for sv in ec["strategy_verdicts"]:
                    if sv.get("verdict") == "follow":
                        key = idx.get(str(sv.get("strategy_index")))
                        if key:
                            led[h][key][0] += 1
                            led[h][key][1] += v - b

    # ---- M1 report ----
    print("=== M1: DAY-VOTE ENDPOINT credit (team-aware, covers ALL discussion turns) ===")
    print(f"  defense-axis reach: {cov['under_heat']}/{cov['disc_turns']} discussion turns are UNDER HEAT "
          f"({cov['under_heat']/max(cov['disc_turns'],1):.0%}) <- where a defense/heat signal can apply")
    comb = defaultdict(lambda: [0, 0.0])
    for hh in (0, 1):
        for k, (f, s) in led[hh].items():
            comb[k][0] += f
            comb[k][1] += s
    def shr(f, s):
        return (s / f) * f / (f + SHRINK_K) if f else 0.0
    deep = [(f, s) for f, s in comb.values() if f >= 3]
    lifts = [shr(f, s) for f, s in deep]
    pos = sum(1 for x in lifts if x > 0.1)
    neg = sum(1 for x in lifts if x < -0.1)
    print(f"  credited discussion SPs (>=3 follows): {len(deep)} "
          f"(vs advocacy-only slice's 41 -> day-vote endpoint covers far more)")
    print(f"  shrunk-lift split:  >+0.1: {pos}   mid: {len(deep)-pos-neg}   <-0.1: {neg}")
    both = [(led[0][k], led[1][k]) for k in set(led[0]) & set(led[1])
            if led[0][k][0] >= 3 and led[1][k][0] >= 3]
    if len(both) >= 3:
        la = [shr(a[0], a[1]) for a, _ in both]
        lb = [shr(b[0], b[1]) for _, b in both]
        print(f"  held-out Pearson(lift_A, lift_B) = {_pearson(la, lb):+.2f} (n={len(both)})")
    else:
        print(f"  held-out underpowered (n={len(both)})")

    # ---- M2 report ----
    print("\n=== M2: PART-3 — night-targetings on players who SPOKE, by visible day-heat ===")
    print(f"  {'targeter':14}{'target-class':12}{'total':>7}{'no-day-heat':>13}{'(= vote-invisible)':>20}")
    for targeter in ("investigator", "vigilante", "serial_killer", "wolves"):
        for cls in ("power", "deceiver", "villager"):
            tot, nh = night[targeter][cls]
            if tot:
                print(f"  {targeter:14}{cls:12}{tot:>7}{nh:>13}{nh/tot:>19.0%}")
    print("  ⭐ vigilante/investigator → deceiver = CONFIRM-OUT; wolves/SK → power = reveal-risk kill.")
    print("  no-day-heat = the read wasn't visible in discussion (hidden-read UPPER BOUND; reasoning refines).")
    return 0


def _half(gid: str) -> int:
    return sum(ord(c) for c in gid) % 2


if __name__ == "__main__":
    raise SystemExit(main())
