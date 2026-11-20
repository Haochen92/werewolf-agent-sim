# ── FROZEN RECORD (stamped 2026-07-05) ──────────────────────────
# Dated evidence artifact, NOT maintained code. It answered its question once
# (verdict: ../../README.md); it is kept runnable-as-of last touch (fde7045) but is
# not import-safe against future refactors. Standing apparatus lives in
# evaluation/src/instrument_validation/.
# ────────────────────────────────────────────────────────────────────────────
"""Graduated 2026-07-02 → evaluation/src/instrument_validation/tagger/tagger_validation.py (mode=deleak); this file is the frozen original apparatus.

2x2 ablation — does WITHHOLDING the day's outcome actually reduce the tagger's leak, or was the leak
just the (mechanical) silent-player effect? The one-armed re-tag couldn't tell these apart: speakers-only
mechanically drops the silent tail that produced the v1 coupling, so "coupling drops" was foregone.

Design (both axes isolated; reasoning-quality base held CONSTANT across the outcome axis):
  outcome in/out  = tag_game(show_outcome=True/False)   -- 2 fresh passes, same base, only the vote/deaths differ
  all / speakers  = deterministic post-filter on EACH pass (a player spoke that day or not)
=> 4 cells from 2 passes. Metric per cell = Pearson(disc_verdict|credibility, DAY-lynch-favorability), where
favorability is computed analysis-side from the game record (independent of what the tagger saw).

Reading the cells:
  (in,all) vs (in,speakers)  -> the MECHANICAL silent-player effect (foregone; not the question).
  (in,all) vs (out,all)      -> THE POINT-1 TEST: does removing the outcome shrink coupling among ALL players?
                                Since (out) tagger is blind to the result, (in)-(out) ~ the leak component.
                                If ~0, the outcome wasn't leaking where people actually talk.

NOTE: claims about leak magnitude are HELD until this returns. A single coupling can't separate leak from
legitimate silence-skill; this 2x2 is what makes each number diagnostic instead of confounded.

COST: 2 flash-lite passes over 6 games (~60 day-calls); tags cached to tags_ablation/ so re-analysis is free.
Model PINNED to flash-lite below (never pro-2.5).

  poetry run python evidence/v7_final/runs/v2_full/tagger_deleak_ablation.py
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

# ⭐COST GUARD: pin every paid slot to flash-lite BEFORE importing the tagger (get_llm_pro reads these).
os.environ["GOOGLE_GENAI_PRO_MODEL"] = "gemini-3.1-flash-lite"
os.environ["GOOGLE_GENAI_PRO_BACKUP_MODEL"] = "gemini-3.1-flash-lite"

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO))

from evaluation.src.loop.discussion_tagger import tag_game  # noqa: E402

RUN = Path(__file__).resolve().parent
ABL = RUN / "tags_ablation"
TOWN = {"villager", "investigator", "healer", "vigilante"}
VV = {"positive": 1.0, "neutral": 0.0, "negative": -1.0}
CRED = {"low": 0, "medium": 1, "high": 2}
N_GAMES = 6


def _fac(r: str) -> str:
    return "town" if r in TOWN else r


def _favor(faction: str, lynch_role: str | None) -> int:
    if not lynch_role:
        return 0
    if faction == "town":
        return 1 if lynch_role in ("wolf", "serial_killer") else -1
    if faction == "wolf":
        return 1 if lynch_role != "wolf" else -1
    if faction == "serial_killer":
        return 1 if lynch_role != "serial_killer" else -1
    return 0


def _pearson(xs, ys):
    n = len(xs)
    if n < 3:
        return None, n
    mx, my = mean(xs), mean(ys)
    sx = sum((x - mx) ** 2 for x in xs) ** 0.5
    sy = sum((y - my) ** 2 for y in ys) ** 0.5
    if not sx or not sy:
        return None, n
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / (sx * sy), n


def _load_records():
    recs = []
    for dump in sorted(glob.glob(str(RUN / "gen*_on.jsonl"))):
        for line in open(dump):
            if line.strip():
                g = json.loads(line)
                if g.get("roles") and g.get("eval_cases_path") and os.path.exists(g["eval_cases_path"]):
                    recs.append(g)
    recs.sort(key=lambda g: g.get("game_id", ""))
    step = max(1, len(recs) // N_GAMES)
    return recs[::step][:N_GAMES]


def _tag_cached(record, mode):
    """tag_game with show_outcome per `mode`, speakers_only=False (all players; filter in analysis).
    Cached per (game_id, mode) so the paid passes run once. Returns disc dict {(day,player): tag}, n_calls."""
    ABL.mkdir(exist_ok=True)
    p = ABL / f"{record['game_id']}.{mode}.json"
    if p.exists():
        d = json.load(open(p))
        return {(int(k.split("|")[0]), k.split("|")[1]): v for k, v in d["disc"].items()}, 0
    disc, _night = tag_game(record, show_outcome=(mode == "in"), speakers_only=False)
    n_days = len({d for d, _ in disc})
    p.write_text(json.dumps({"disc": {f"{d}|{pl}": v for (d, pl), v in disc.items()}}))
    return disc, n_days


def _cell_rows(records, mode):
    """All disc tags for `mode` joined to (faction, day-favorability, spoke?). Returns rows per faction."""
    rows = defaultdict(list)  # faction -> [(verdict, cred, favor, spoke_bool)]
    calls = 0
    for g in records:
        roles = g["roles"]
        lynch_role = {dr.get("day"): dr.get("voted_player_role") for dr in g.get("day_resolutions", [])}
        spoke = defaultdict(set)
        for m in g.get("day_channel") or []:
            if not m.get("passed") and (m.get("message") or "").strip():
                spoke[m.get("day")].add(m.get("player"))
        disc, n = _tag_cached(g, mode)
        calls += n
        for (day, p), t in disc.items():
            f = _fac(roles.get(p, "?"))
            rows[f].append((VV[t["verdict"]], CRED.get(t.get("credibility"), 1),
                            _favor(f, lynch_role.get(day)), p in spoke[day]))
    return rows, calls


def _coupling(rows, speakers_only):
    """Pearson(disc_verdict|credibility, favor) per faction, optionally restricted to speakers."""
    out = {}
    for f, rs in rows.items():
        rs2 = [r for r in rs if r[3]] if speakers_only else rs
        rv, n = _pearson([r[0] for r in rs2], [r[2] for r in rs2])
        rc, _ = _pearson([r[1] for r in rs2], [r[2] for r in rs2])
        out[f] = (rv, rc, n)
    return out


def main():
    records = _load_records()
    print(f"6-game 2x2 ablation on {[g['game_id'] for g in records]}\n")
    t0 = time.time()
    rows_in, c1 = _cell_rows(records, "in")
    rows_out, c2 = _cell_rows(records, "out")
    elapsed = time.time() - t0
    calls = c1 + c2

    cells = {
        ("in", "all"): _coupling(rows_in, False), ("in", "speakers"): _coupling(rows_in, True),
        ("out", "all"): _coupling(rows_out, False), ("out", "speakers"): _coupling(rows_out, True),
    }
    print("coupling = Pearson(score, day-lynch-favorability). disc_verdict / credibility / N_tags\n")
    for f in ("town", "wolf", "serial_killer"):
        print(f"=== {f} ===")
        for outc in ("in", "out"):
            for who in ("all", "speakers"):
                rv, rc, n = cells[(outc, who)].get(f, (None, None, 0))
                fmt = lambda x: f"{x:+.2f}" if x is not None else "  -  "
                print(f"   outcome-{outc:3s} / {who:8s}:  disc={fmt(rv)}  cred={fmt(rc)}  (N={n})")
        # the two diagnostic contrasts (disc_verdict)
        ia = cells[("in", "all")].get(f, (None,))[0]; ip = cells[("in", "speakers")].get(f, (None,))[0]
        oa = cells[("out", "all")].get(f, (None,))[0]
        mech = (ia - ip) if (ia is not None and ip is not None) else None
        leak = (ia - oa) if (ia is not None and oa is not None) else None
        print(f"   -> mechanical silent-player effect (in,all)-(in,speakers) = {mech:+.2f}" if mech is not None else "   -> mech n/a")
        print(f"   -> OUTCOME-LEAK among all players (in,all)-(out,all)      = {leak:+.2f}" if leak is not None else "   -> leak n/a")
        print()

    rate = "~$0.10/1M in, ~$0.40/1M out (assumed flash-lite)"
    print(f"COST: {calls} fresh flash-lite day-calls ({elapsed:.0f}s wall). Est ~$0.02-0.06 ({rate}); "
          f"0 if fully cached. Exact realized cost: pull Langfuse over this window if a receipt is needed.")

    # Persist the load-bearing numbers as a durable artifact (was stdout-only). Additive:
    # the stats above are unchanged; this just serializes `cells` + the two contrasts.
    artifact = {
        "game_ids": [g["game_id"] for g in records],
        "n_games": len(records),
        "fresh_day_calls": calls,
        "coupling": {
            f: {
                f"{outc}/{who}": {
                    "disc_verdict": cells[(outc, who)].get(f, (None, None, 0))[0],
                    "credibility": cells[(outc, who)].get(f, (None, None, 0))[1],
                    "n": cells[(outc, who)].get(f, (None, None, 0))[2],
                }
                for outc in ("in", "out")
                for who in ("all", "speakers")
            }
            for f in ("town", "wolf", "serial_killer")
        },
        "contrasts": {
            f: {
                "mechanical_silent_player_effect": (
                    (cells[("in", "all")].get(f, (None,))[0] - cells[("in", "speakers")].get(f, (None,))[0])
                    if cells[("in", "all")].get(f, (None,))[0] is not None
                    and cells[("in", "speakers")].get(f, (None,))[0] is not None
                    else None
                ),
                "outcome_leak_all_players": (
                    (cells[("in", "all")].get(f, (None,))[0] - cells[("out", "all")].get(f, (None,))[0])
                    if cells[("in", "all")].get(f, (None,))[0] is not None
                    and cells[("out", "all")].get(f, (None,))[0] is not None
                    else None
                ),
            }
            for f in ("town", "wolf", "serial_killer")
        },
    }
    out_path = RUN / "tagger_deleak_ablation_results.json"
    out_path.write_text(json.dumps(artifact, indent=2))
    print(f"Wrote results artifact: {out_path}")


if __name__ == "__main__":
    raise SystemExit(main())
