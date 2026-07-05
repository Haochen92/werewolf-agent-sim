"""v7 (d) — effectiveness of the EXTENDED tagger: discussion (holistic, framing/credibility/role-reveal)
+ night read-quality. Two de-luck tests.

DISCUSSION:
  H1 corr(disc_verdict, faction_won)    — halo (net_verdict ≈ +0.45; lower = de-luck).
  H2 corr(disc_verdict, day-vote floor) — redundancy with the FREE signal (was +0.55 on the merit-only
                                          verdict; should DROP now that framing/credibility/role-reveal
                                          are weighed in — the unique axes the floor can't see).
NIGHT (does it de-luck `_night_credit`'s outcome-luck?):
  cross-tab the tagger's read_quality against `_night_credit`'s outcome verdict — it earns its keep if it
  reassigns credit: LUCKY hits (det positive, read blind) demoted, SKILLED misses (det not-positive, read
  skilled) credited. + corr(night_verdict, faction_won) halo.

  GOOGLE_GENAI_PRO_MODEL=gemini-3.1-flash-lite GOOGLE_GENAI_PRO_BACKUP_MODEL=gemini-3.1-flash-lite \
    poetry run python -m evaluation.src.instrument_validation.tagger.tagger_effectiveness
"""

import glob
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from evaluation.src.loop.credit_backfill import VERDICT_VALUE, _night_credit, _vote_credit  # noqa: E402
from evaluation.src.loop.discussion_tagger import _night_actions_by_day, tag_game  # noqa: E402

N_GAMES = 8
FACTION = {"wolf": "wolves", "serial_killer": "serial_killer"}


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
    games, seen = [], set()
    for f in sorted(glob.glob("batch_results/*v6ab*.jsonl")):
        for line in open(f):
            g = json.loads(line)
            if g.get("day_channel") and len(g["day_channel"]) > 8 and g.get("roles") and g.get("winner"):
                games.append(g)
                seen.add(g["winner"])
            if len(games) >= N_GAMES:
                break
        if len(games) >= N_GAMES:
            break
    print(f"tagging {len(games)} games | winners: {Counter(g['winner'] for g in games)}\n")

    dv, dwon, dfloor = [], [], []                 # discussion: verdict, faction_won, day-floor
    nv, nwon = [], []                             # night: verdict, faction_won
    crosstab = defaultdict(Counter)               # read_quality -> Counter(det_verdict)
    for g in games:
        roles, winner = g["roles"], FACTION.get(g["winner"], "villagers") if g["winner"] in FACTION else g["winner"]
        winner = g["winner"]
        lynch = {dr.get("day"): dr.get("voted_player") for dr in g.get("day_resolutions", [])}
        disc, night = tag_game(g)
        for (day, player), t in disc.items():
            role = roles.get(player)
            if role is None:
                continue
            dv.append(VERDICT_VALUE[t["verdict"]])
            dwon.append(1 if FACTION.get(role, "villagers") == winner else 0)
            dfloor.append(VERDICT_VALUE[_vote_credit(role, lynch.get(day), roles)])
        nacts = {(day, p): (r, tgt) for day, lst in _night_actions_by_day(g).items() for p, r, tgt in lst}
        for (day, player), t in night.items():
            role = roles.get(player)
            rt = nacts.get((day, player))
            if role is None or rt is None:
                continue
            det = _night_credit(rt[0], rt[1], roles)            # outcome-based
            nv.append(VERDICT_VALUE[t["verdict"]])
            nwon.append(1 if FACTION.get(role, "villagers") == winner else 0)
            crosstab[t["read_quality"]][det] += 1

    print("=== DISCUSSION (enriched verdict) ===")
    print(f"  H1 corr(verdict, faction_won) = {_pearson(dv, dwon):+.2f}  (net_verdict halo ≈ +0.45)")
    print(f"  H2 corr(verdict, day-floor)   = {_pearson(dv, dfloor):+.2f}  (merit-only was +0.55; lower = "
          f"now adds beyond the free floor)   [n={len(dv)}]")
    print("\n=== NIGHT (read-quality vs _night_credit outcome) ===")
    print(f"  corr(night_verdict, faction_won) = {_pearson(nv, nwon):+.2f}  (halo)   [n={len(nv)}]")
    print(f"  {'read_quality':16}{'det:positive':>13}{'det:neutral':>12}{'det:negative':>13}")
    for rq in ("skilled", "reasonable", "blind_or_lucky", "misread"):
        c = crosstab.get(rq, Counter())
        print(f"  {rq:16}{c['positive']:>13}{c['neutral']:>12}{c['negative']:>13}")
    lucky = sum(crosstab[r]["positive"] for r in ("blind_or_lucky", "misread"))
    skilled_miss = crosstab["skilled"]["neutral"] + crosstab["skilled"]["negative"]
    print(f"  -> de-luck reassignment: LUCKY hits demoted (det+ but read blind/misread) = {lucky}; "
          f"SKILLED misses credited (read skilled but det not+) = {skilled_miss}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
