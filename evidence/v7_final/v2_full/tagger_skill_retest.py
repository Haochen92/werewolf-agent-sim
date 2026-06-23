"""Foundation test for the deceiver-metric thread: is the wolf game-level signal (Check C partial
r(disc_verdict, won | deluck) = +0.60) REAL SKILL, or leak / a verbosity confounder?

Three numbers per faction, over the 24 v2 ON games:
  (A) partial r(disc_IN , won | deluck)            -- reproduces Check C off the v1 (outcome-IN) tags  (sanity)
  (B) partial r(disc_OUT, won | deluck)            -- BLINDED: re-tagged outcome-out. Survives => not leak,
                                                      on the game-level metric that matters (not just day-local)
  (C) partial r(disc_OUT, won | deluck, verbosity) -- BLINDED + the live confounder partialled out. Survives
                                                      => moves from "consistent with skill" to "skill".
(Model is NOT a control here: every agent in every v2 game is the same model, so it has no variance.)

Collapses anywhere => the premise was leak/confounder and the powered deceiver-metric run has no floor.
Partial r via dependency-free recursive formula. COST: re-tag the ~18 games not already cached
outcome-out (the 6 ablation games are reused), flash-lite-PINNED, ~90 day-calls, ~cents.

  poetry run python evidence/v7_final/v2_full/tagger_skill_retest.py
"""

from __future__ import annotations

import glob
import json
import os
import sys
import time
from collections import defaultdict
from pathlib import Path
from statistics import mean

os.environ["GOOGLE_GENAI_PRO_MODEL"] = "gemini-3.1-flash-lite"          # cost guard
os.environ["GOOGLE_GENAI_PRO_BACKUP_MODEL"] = "gemini-3.1-flash-lite"

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))
from evaluation.src.loop.credit_backfill import VERDICT_VALUE, _decision_credit, _majority_vote  # noqa: E402
from evaluation.src.loop.discussion_tagger import tag_game  # noqa: E402

RUN = Path(__file__).resolve().parent
ABL = RUN / "tags_ablation"          # reuse the ablation's outcome-out cache ({gid}.out.json)
V1 = RUN / "tags"                    # the original outcome-in tags ({gid}.v1.json)
TOWN = {"villager", "investigator", "healer", "vigilante"}
VV = {"positive": 1.0, "neutral": 0.0, "negative": -1.0}
WIN = {"villagers": "town", "wolves": "wolf", "serial_killer": "serial_killer"}


def _fac(r): return "town" if r in TOWN else r


def _pear(x, y):
    n = len(x)
    if n < 3:
        return None
    mx, my = mean(x), mean(y)
    sx = sum((a - mx) ** 2 for a in x) ** 0.5
    sy = sum((b - my) ** 2 for b in y) ** 0.5
    return sum((a - mx) * (b - my) for a, b in zip(x, y)) / (sx * sy) if sx and sy else None


def _pcorr1(x, y, z):
    rxy, rxz, ryz = _pear(x, y), _pear(x, z), _pear(y, z)
    if None in (rxy, rxz, ryz):
        return None
    d = ((1 - rxz ** 2) * (1 - ryz ** 2)) ** 0.5
    return (rxy - rxz * ryz) / d if d else None


def _pcorr2(x, y, z1, z2):
    a, b, c = _pcorr1(x, y, z1), _pcorr1(x, z2, z1), _pcorr1(y, z2, z1)
    if None in (a, b, c):
        return None
    d = ((1 - b ** 2) * (1 - c ** 2)) ** 0.5
    return (a - b * c) / d if d else None


def _load_v1(gid):
    p = V1 / f"{gid}.v1.json"
    if not p.exists():
        return {}
    d = json.load(open(p))
    return {(int(k.split("|")[0]), k.split("|")[1]): v for k, v in d["disc"].items()}


def _load_out(record):
    """outcome-out disc tags (all players), reusing the ablation cache; tag fresh + cache on miss."""
    gid = record["game_id"]
    p = ABL / f"{gid}.out.json"
    if p.exists():
        d = json.load(open(p))
        return {(int(k.split("|")[0]), k.split("|")[1]): v for k, v in d["disc"].items()}, 0
    disc, _ = tag_game(record, show_outcome=False, speakers_only=False)
    ABL.mkdir(exist_ok=True)
    p.write_text(json.dumps({"disc": {f"{dd}|{pl}": v for (dd, pl), v in disc.items()}}))
    return disc, len({dd for dd, _ in disc})


def main():
    records = []
    for dump in sorted(glob.glob(str(RUN / "gen*_on.jsonl"))):
        for line in open(dump):
            if line.strip():
                g = json.loads(line)
                if g.get("roles") and g.get("eval_cases_path") and os.path.exists(g["eval_cases_path"]):
                    records.append(g)
    # per faction: parallel arrays over games
    cols = {f: defaultdict(list) for f in ("town", "wolf", "serial_killer")}
    calls = 0
    t0 = time.time()
    for g in records:
        roles = g["roles"]
        winf = WIN.get(g.get("winner"))
        blend = {dr.get("day"): _majority_vote(dr) for dr in g.get("day_resolutions", [])}
        v1 = _load_v1(g["game_id"])
        out, n = _load_out(g)
        calls += n
        # de-luck skill proxy (vote+night) per faction; verbosity = faction spoken-message count
        dl = defaultdict(list)
        for cl in open(g["eval_cases_path"]):
            if not cl.strip():
                continue
            ec = (json.loads(cl).get("output") or {}).get("eval_case") or {}
            v = _decision_credit(ec, roles, blend)
            if v is not None:
                dl[_fac(ec.get("player_role"))].append(VERDICT_VALUE[v])
        verb = defaultdict(int)
        for m in g.get("day_channel") or []:
            if not m.get("passed") and (m.get("message") or "").strip():
                verb[_fac(roles.get(m.get("player"), "?"))] += 1
        for f in cols:
            players = {p for p, r in roles.items() if _fac(r) == f}
            din = [VV[t["verdict"]] for (d, p), t in v1.items() if p in players]
            dout = [VV[t["verdict"]] for (d, p), t in out.items() if p in players]
            if not din or not dout or not dl[f]:
                continue
            cols[f]["din"].append(mean(din))
            cols[f]["dout"].append(mean(dout))
            cols[f]["deluck"].append(mean(dl[f]))
            cols[f]["verb"].append(float(verb[f]))
            cols[f]["won"].append(1.0 if winf == f else 0.0)
    elapsed = time.time() - t0

    print(f"Wolf game-level skill retest over {len(records)} v2 ON games "
          f"({calls} fresh outcome-out day-calls, {elapsed:.0f}s)\n")
    print(f"{'faction':14s} {'N':>3}  (A) in|deluck   (B) OUT|deluck   (C) OUT|deluck,verbosity")
    for f in ("wolf", "serial_killer", "town"):
        c = cols[f]
        n = len(c["won"])
        A = _pcorr1(c["din"], c["won"], c["deluck"])
        B = _pcorr1(c["dout"], c["won"], c["deluck"])
        C = _pcorr2(c["dout"], c["won"], c["deluck"], c["verb"])
        fmt = lambda x: f"{x:+.2f}" if x is not None else "  -  "
        print(f"{f:14s} {n:>3}     {fmt(A):>8}        {fmt(B):>8}         {fmt(C):>8}")
    print("\n(A) reproduces Check C (~+0.60 wolf). (B) blinded: signal not from outcome-leak if it holds.")
    print("(C) blinded + verbosity partialled: holds => 'skill'; collapses => verbosity confounder.")
    print(f"\nCOST: {calls} fresh flash-lite day-calls (~$0.0{max(1, calls//30)}); 0 if fully cached. "
          "Exact via Langfuse if a receipt is needed.")


if __name__ == "__main__":
    raise SystemExit(main())
