# ── FROZEN RECORD (stamped 2026-07-05) ──────────────────────────
# Dated evidence artifact, NOT maintained code. It answered its question once
# (verdict: ../../README.md); it is kept runnable-as-of last touch (1a0a9bc) but is
# not import-safe against future refactors. Standing apparatus lives in
# evaluation/src/instrument_validation/.
# ────────────────────────────────────────────────────────────────────────────
"""v2_full REPOSITIONED — all-factions-memory-ON paired A/B (NOT the town-only test it was meant to be).

v2 ran `configs=all_enabled` (EVERY faction had memory) vs `all_disabled`, instead of the intended
`town_only`. That makes it INVALID for isolating TOWN memory (arms-race confound: ON-arm town faced
memory-improved wolves, and the de-luck vote proxy is opponent-sensitive — better-concealed wolves
mechanically depress town vote accuracy). But the SAME run IS a valid PAIRED A/B for each faction's
own memory (game_id-matched ON vs OFF). This script extracts that, at zero spend:

  1. per-faction on-off (paired) per generation + slope  -- the standard vote+night de-luck proxy
  2. the same on a DISCUSSION-INCLUSIVE proxy -- day_discussion added via the FREE day-vote-endpoint
     FLOOR (deterministic, valid for BOTH arms). NOT the omniscient tagger: ON and OFF games share a
     game_id, tags are cached per game_id from the ON arm only, so tagging the OFF arm would silently
     reuse ON transcripts' tags (a real collision found 2026-06-23). The floor avoids that AND avoids
     the halo of a tagger-base-0 "gain" that was never differenced against no-memory.

  poetry run python evidence/v7_final/runs/v2_full/v2_salvage.py
"""

from __future__ import annotations

import glob
import json
import os
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from evaluation.src.loop.credit_backfill import (
    VERDICT_VALUE, _decision_credit, _majority_vote, _vote_credit)

RUN = Path(__file__).resolve().parent
TOWN = {"villager", "investigator", "healer", "vigilante"}
GENS = range(1, 7)


def _faction(role: str) -> str:
    return "town" if role in TOWN else role


def gen_scores(gen: int, include_discussion: bool) -> dict:
    """Mean de-luck value per (arm, faction) for one generation. include_discussion adds day_discussion
    turns scored by the FREE day-vote-endpoint floor (the day's lynch outcome, faction-relative) — the
    same deterministic proxy the loop's `_discussion_ledger` uses, valid for BOTH arms (no tagger cache)."""
    sums: dict[str, float] = defaultdict(float)
    ns: dict[str, int] = defaultdict(int)
    for dump in sorted(glob.glob(str(RUN / f"gen{gen}_*.jsonl"))):
        for line in open(dump):
            if not line.strip():
                continue
            g = json.loads(line)
            roles, path = g.get("roles"), g.get("eval_cases_path")
            if not roles or not path or not os.path.exists(path):
                continue
            blend = {dr.get("day"): _majority_vote(dr) for dr in g.get("day_resolutions", [])}
            lynch = {dr.get("day"): dr.get("voted_player") for dr in g.get("day_resolutions", [])}
            for cl in open(path):
                if not cl.strip():
                    continue
                ec = (json.loads(cl).get("output") or {}).get("eval_case")
                if not ec:
                    continue
                phase, role = ec.get("action_phase"), ec.get("player_role", "?")
                if phase == "day_discussion" and include_discussion:
                    val = VERDICT_VALUE[_vote_credit(role, lynch.get(ec.get("day")), roles)]
                else:
                    verdict = _decision_credit(ec, roles, blend)
                    if verdict is None:
                        continue
                    val = VERDICT_VALUE[verdict]
                arm = "on" if ec.get("memory_enabled") else "off"
                fac = _faction(role)
                for key in (f"{arm}/overall", f"{arm}/{fac}"):
                    sums[key] += val
                    ns[key] += 1
    return {k: sums[k] / ns[k] for k in ns} | {f"n_{k}": ns[k] for k in ns}


def _slope(deltas: list[float]) -> float:
    """OLS slope of on-off across generations (the compounding signal)."""
    xs = list(range(len(deltas)))
    n = len(xs)
    mx = sum(xs) / n
    my = sum(deltas) / n
    denom = sum((x - mx) ** 2 for x in xs)
    return sum((x - mx) * (y - my) for x, y in zip(xs, deltas)) / denom if denom else 0.0


def report(include_discussion: bool) -> None:
    label = "DISCUSSION-INCLUSIVE (free floor)" if include_discussion else "STANDARD (vote+night only)"
    print(f"\n{'='*78}\n{label} proxy — per-faction on-off, paired by game_id\n{'='*78}")
    scores = {g: gen_scores(g, include_discussion) for g in GENS}
    for fac in ("overall", "town", "wolf", "serial_killer"):
        deltas, line = [], []
        for g in GENS:
            s = scores[g]
            on, off = s.get(f"on/{fac}"), s.get(f"off/{fac}")
            if on is None or off is None:
                line.append("   --  ")
                continue
            d = on - off
            deltas.append(d)
            line.append(f"{d:+.2f}")
        mean = sum(deltas) / len(deltas) if deltas else 0.0
        sl = _slope(deltas) if len(deltas) > 1 else 0.0
        # gen-1 = empty-seed bootstrap; also report mean/slope over gens 2-6
        d26 = deltas[1:]
        m26 = sum(d26) / len(d26) if d26 else 0.0
        sl26 = _slope(d26) if len(d26) > 1 else 0.0
        print(f"  {fac:14s} on-off/gen: {' '.join(line)}  | mean26={m26:+.3f} slope26={sl26:+.3f}")


if __name__ == "__main__":
    print(__doc__)
    report(include_discussion=False)
    report(include_discussion=True)
