"""v7 Gate G2 — separability / signal-above-luck (the PRECONDITION, plan §1b.0 / §5-G2).

The v7 compounding loop rests on one assumption: a decision's quality is attributable to the decision,
ABOVE the luck (role draw, other agents, RNG) that also moves the outcome. If decision-level outcomes
are pure noise, no credit can be assigned and the loop has nothing to compound on → STOP. Screened
deterministically on the 180 v6ab games we already have. Zero spend.

G2 is channel-agnostic, but "is there signal" must be answered PER ROLE/FACTION — that's what decides
which channels v7 can actually compound on (and where the town-helps / deceiver-null asymmetry lives).
Each channel: a role's de-luck decision proxy vs ITS faction's outcome, at the GAME grain, against a
permutation luck-null (shuffle which games that faction won — "if the proxy were unrelated to outcome").
Town day-vote also gets the single-DECISION grain (the grain a memory is credited at).

Proxies (all ground-truthed by roles, no LLM):
  town day-vote   hit_threat (voted a wolf/SK)              -> town_won
  investigator N  found an evil (target in THREAT)          -> town_won   [transmission cap lives here]
  vigilante N     shot landed on an evil                    -> town_won
  healer N        save blocked a kill (healer_saved)        -> town_won
  wolf N          hit a town POWER role                     -> wolves_won
  wolf day-blend  vote aligned with the eventual lynch      -> wolves_won
  SK N (landed)   night kill landed                         -> sk_won
  SK N (anti-wolf)night target was a wolf                   -> sk_won
"""

import glob
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))  # repo root, for `evaluation.src.*`

from evaluation.src.core.stats import point_biserial  # noqa: E402
from evaluation.src.loop.decision_scoring import (  # noqa: E402
    POWER_ROLES, THREAT_ROLES, score_vote,
)

TOWN_ROLES = {"villager", "healer", "investigator", "vigilante"}
N_PERM = 20000
random.seed(20260618)

ARMS = sorted(glob.glob("batch_results/v6ab_*.jsonl"))


def load_games():
    games = []
    for f in ARMS:
        for line in open(f):
            if line.strip():
                games.append(json.loads(line))
    return games


def _perm_p(won, proxy, observed):
    pool = list(won)
    hits = 0
    for _ in range(N_PERM):
        random.shuffle(pool)
        r, _ = point_biserial(pool, proxy)
        if abs(r) >= abs(observed):
            hits += 1
    return (hits + 1) / (N_PERM + 1)


def channel(name, rows):
    """rows = list of (proxy_value_in_[0,1], faction_won_0_or_1) at the game grain."""
    rows = [(float(p), int(w)) for p, w in rows]
    if len(rows) < 8:
        print(f"  {name:22s} n={len(rows)} — too few, skip")
        return
    proxy = [p for p, _ in rows]
    won = [w for _, w in rows]
    if len(set(won)) < 2 or len(set(proxy)) < 2:
        print(f"  {name:22s} n={len(rows)} won-rate={sum(won)/len(won):.2f} — degenerate, skip")
        return
    r, pa = point_biserial(won, proxy)
    pp = _perm_p(won, proxy, r)
    # win-rate split at the proxy median
    med = sorted(proxy)[len(proxy) // 2]
    hi = [w for p, w in rows if p > med]
    lo = [w for p, w in rows if p <= med]
    split = ""
    if hi and lo:
        split = f"  win@hi={sum(hi)/len(hi):.2f} win@lo={sum(lo)/len(lo):.2f}"
    flag = "PASS" if pp < 0.01 else ("weak" if pp < 0.05 else "NULL")
    print(f"  {name:22s} n={len(rows):3d} r={r:+.3f} perm_p={pp:.1e} [{flag}]{split}")


def main():
    games = load_games()
    print(f"games: {len(games)}")
    won_counts = {"villagers": 0, "wolves": 0, "serial_killer": 0}
    for g in games:
        w = (g.get("computed_metrics") or {}).get("winner") or g.get("winner")
        won_counts[w] = won_counts.get(w, 0) + 1
    print(f"outcomes: {won_counts}\n")

    # collectors: name -> list[(proxy, won)]
    ch = {k: [] for k in (
        "town_dayvote", "investigator_night", "vigilante_night", "healer_night",
        "wolf_night_power", "wolf_dayblend", "sk_night_landed", "sk_night_antiwolf",
    )}
    # town decision grain
    dec_hit, dec_gi, game_won_town = [], [], []

    for gi, g in enumerate(games):
        roles = g["roles"]
        winner = (g.get("computed_metrics") or {}).get("winner") or g.get("winner")
        town_won = int(winner == "villagers")
        wolves_won = int(winner == "wolves")
        sk_won = int(winner == "serial_killer")
        game_won_town.append(town_won)

        # --- town day-vote (game + decision grain) + wolf day-blend ---
        thits = ttot = 0
        for d in g["day_resolutions"]:
            vp = d.get("voted_player")
            wolf_votes = [v for v in d.get("votes", []) if roles.get(v["voter"]) == "wolf"]
            for v in d.get("votes", []):
                r = roles.get(v["voter"])
                if r in TOWN_ROLES:
                    ov = score_vote(v["votee"], roles)
                    if ov.is_abstain:
                        continue
                    ttot += 1
                    h = int(ov.hit_threat)
                    thits += h
                    dec_hit.append(h)
                    dec_gi.append(gi)
            # wolf day-blend: living wolves' votes aligning with the eventual lynch (excl self)
            if vp is not None:
                al = tot = 0
                for v in wolf_votes:
                    if v["voter"] == vp:
                        continue
                    tot += 1
                    al += int(v["votee"] == vp)
                if tot:
                    ch["wolf_dayblend"].append((al / tot, wolves_won))
        if ttot:
            ch["town_dayvote"].append((thits / ttot, town_won))

        # --- night channels ---
        inv_h = inv_n = 0
        vig_h = vig_n = 0
        heal_h = heal_n = 0
        wolf_h = wolf_n = 0
        sk_land_h = sk_land_n = 0
        sk_aw_h = sk_aw_n = 0
        for n in g["night_resolutions"]:
            if n.get("investigator_target"):
                inv_n += 1
                inv_h += int(n.get("investigator_target_role") in THREAT_ROLES)
            if n.get("vigilante_target"):
                vig_n += 1
                vig_h += int(bool(n.get("vigilante_kill_landed"))
                             and n.get("vigilante_target_role") in THREAT_ROLES)
            if n.get("healer_target"):
                heal_n += 1
                heal_h += int(bool(n.get("healer_saved")))
            if n.get("wolves_target"):
                wolf_n += 1
                wolf_h += int(n.get("wolf_target_role") in POWER_ROLES)
            if n.get("serial_killer_target"):
                sk_land_n += 1
                sk_land_h += int(bool(n.get("serial_killer_kill_landed")))
                sk_aw_n += 1
                sk_aw_h += int(n.get("serial_killer_target_role") == "wolf")
        if inv_n:
            ch["investigator_night"].append((inv_h / inv_n, town_won))
        if vig_n:
            ch["vigilante_night"].append((vig_h / vig_n, town_won))
        if heal_n:
            ch["healer_night"].append((heal_h / heal_n, town_won))
        if wolf_n:
            ch["wolf_night_power"].append((wolf_h / wolf_n, wolves_won))
        if sk_land_n:
            ch["sk_night_landed"].append((sk_land_h / sk_land_n, sk_won))
            ch["sk_night_antiwolf"].append((sk_aw_h / sk_aw_n, sk_won))

    print("=== per-channel separability (game grain, permutation luck-null) ===")
    for name in ch:
        channel(name, ch[name])

    # town decision grain
    dec_won = [game_won_town[gi] for gi in dec_gi]
    r_d, _ = point_biserial(dec_won, [float(h) for h in dec_hit])
    perm = list(game_won_town)
    obs = abs(r_d)
    hp = 0
    for _ in range(N_PERM):
        random.shuffle(perm)
        dp = [perm[gi] for gi in dec_gi]
        r, _ = point_biserial(dp, [float(h) for h in dec_hit])
        if abs(r) >= obs:
            hp += 1
    pp_d = (hp + 1) / (N_PERM + 1)
    p_hit = sum(w for w, h in zip(dec_won, dec_hit) if h) / max(1, sum(dec_hit))
    p_miss = sum(w for w, h in zip(dec_won, dec_hit) if not h) / max(1, len(dec_hit) - sum(dec_hit))
    print("\n=== town day-vote, single-DECISION grain ===")
    print(f"  n={len(dec_hit)} votes r={r_d:+.3f} game-perm_p={pp_d:.1e} | "
          f"P(win|hit)={p_hit:.2f} vs P(win|miss)={p_miss:.2f} Δ={p_hit - p_miss:+.2f}")


if __name__ == "__main__":
    main()
