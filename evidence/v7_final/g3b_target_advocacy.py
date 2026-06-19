"""v7 Gate G3b — target-advocacy detector (the OFFENSE channel, plan §6.2 / §10a). Zero spend.

Discussion is the hardest channel to credit (diffuse/lagged/collective). G3b tests whether the cheapest
deterministic offense signal EXISTS before v7 tries to credit discussion: does ADVOCACY steer the vote,
and does it steer toward CORRECT removals? An advocacy act = a discussion message with
`addressed_targets.stance == "accusation"` (deterministic, no LLM). Scored by the downstream vote.

SCOPE: only the structured advocacy act. The richer "investigator revealed a confirmed result before
dying" needs a reveal act-detector (confirmed-read assertion) = the §6 mechanism, NOT built yet — out
of scope here.

Three reads on the 180 v6ab games:
  1. STEERING — are advocated targets lynched more than non-advocated? (does talk move the vote)
  2. OFFENSE PRECISION — of TOWN-advocated targets that got lynched, what fraction were threats
     (wolf/SK), vs the base lynch precision? (is the steering toward correct removals)
  3. OUTCOME SIGNAL — per game, does town advocacy-precision predict town_won? (offense separability,
     parallel to G2)
"""

import glob
import json
import sys

sys.path.insert(0, "evaluation/src")
sys.path.insert(0, ".")
from core.stats import compare_proportions, point_biserial  # noqa: E402

TOWN_ROLES = {"villager", "healer", "investigator", "vigilante"}
THREAT_ROLES = {"wolf", "serial_killer"}

ARMS = sorted(glob.glob("batch_results/v6ab_*.jsonl"))


def load_games():
    out = []
    for f in ARMS:
        for line in open(f):
            if line.strip():
                out.append(json.loads(line))
    return out


def main():
    games = load_games()

    # steering 2x2: was a (game,target) advocated-by-town? was it lynched?
    adv_lynched = adv_total = 0
    noadv_lynched = noadv_total = 0
    # offense precision
    town_adv_lynched_threat = town_adv_lynched_total = 0
    base_lynch_threat = base_lynch_total = 0
    # outcome signal
    g_prec, g_won = [], []

    for g in games:
        roles = g["roles"]
        winner = (g.get("computed_metrics") or {}).get("winner") or g.get("winner")
        town_won = int(winner == "villagers")
        players = set(roles)

        # who did TOWN players accuse (advocacy), per target
        town_advocated = set()
        for e in g["day_channel"]:
            if roles.get(e.get("player")) not in TOWN_ROLES:
                continue
            for a in e.get("addressed_targets") or []:
                if a.get("stance") == "accusation" and a.get("target") in players:
                    town_advocated.add(a["target"])

        lynched = {d["voted_player"]: d.get("voted_player_role")
                   for d in g["day_resolutions"] if d.get("voted_player")}
        lynched_set = set(lynched)

        for p in players:
            is_lyn = p in lynched_set
            if p in town_advocated:
                adv_total += 1
                adv_lynched += int(is_lyn)
            else:
                noadv_total += 1
                noadv_lynched += int(is_lyn)

        # base lynch precision + town-advocacy lynch precision
        gp_t = gp_n = 0
        for tgt, role in lynched.items():
            base_lynch_total += 1
            base_lynch_threat += int(role in THREAT_ROLES)
            if tgt in town_advocated:
                town_adv_lynched_total += 1
                town_adv_lynched_threat += int(role in THREAT_ROLES)
                gp_n += 1
                gp_t += int(role in THREAT_ROLES)
        if gp_n:
            g_prec.append(gp_t / gp_n)
            g_won.append(town_won)

    print("=== 1. STEERING — does advocacy move the vote? ===")
    ar = adv_lynched / adv_total if adv_total else 0
    nr = noadv_lynched / noadv_total if noadv_total else 0
    cmp = compare_proportions(adv_lynched, adv_total, noadv_lynched, noadv_total)
    print(f"  town-advocated player lynched: {adv_lynched}/{adv_total}={ar:.2f}  "
          f"vs not-advocated: {noadv_lynched}/{noadv_total}={nr:.2f}  Δ={ar - nr:+.2f} p={cmp.fisher_p:.1e}")

    print("\n=== 2. OFFENSE PRECISION — town-advocated lynches hit threats? ===")
    tp = town_adv_lynched_threat / town_adv_lynched_total if town_adv_lynched_total else 0
    bp = base_lynch_threat / base_lynch_total if base_lynch_total else 0
    cmp2 = compare_proportions(town_adv_lynched_threat, town_adv_lynched_total,
                               base_lynch_threat, base_lynch_total)
    print(f"  town-advocated & lynched were threats: {town_adv_lynched_threat}/{town_adv_lynched_total}"
          f"={tp:.2f}  vs ALL lynches: {base_lynch_threat}/{base_lynch_total}={bp:.2f}  "
          f"Δ={tp - bp:+.2f} p={cmp2.fisher_p:.2f}")

    print("\n=== 3. OUTCOME SIGNAL — per-game town advocacy-precision vs town_won ===")
    if len(g_prec) >= 8:
        r, p = point_biserial(g_won, g_prec)
        print(f"  n={len(g_prec)} games r={r:+.3f} p={p:.2e}")
    else:
        print(f"  n={len(g_prec)} — too few")

    print("\n=== interpretation ===")
    print("  steering Δ>0 + precision≥base → advocacy is a real, creditable offense signal for v7.")
    print("  precision≈base → talk moves the vote but not toward correct removals (offense is noisy).")


if __name__ == "__main__":
    main()
