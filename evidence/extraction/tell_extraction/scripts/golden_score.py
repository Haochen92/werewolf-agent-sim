"""Score detector vs temp-golden verdicts — PROBE SCAFFOLDING (experiment_log.md §5).

Consumes outputs/adjudication_cases.json + outputs/golden_verdicts.json (adjudicated days per
case, post Fable-review). Positive cases score PRECISION at (tell, day) grain; negative cases
score RECALL on the sampled head-tell cells (a negative cell where the golden finds days = a
detector miss). Day-slip (right tell, adjacent day) is reported separately — it corrupts the
day-level denominator less than a full phantom.

The golden cells are detector-independent (game, player, channel, tell), so a later prompt
version rescoreable on the same cells: pass its detections file as argv[1] and each case's
detector_days are recomputed from it. Caveat: positives were originally sampled FROM v1's
detections, so a new version's detections OUTSIDE these 40 cells are unscored.

  PYTHONPATH=. poetry run python evidence/extraction/tell_extraction/golden_score.py \
      [outputs/detector_det_v2.jsonl]
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "outputs"

cases = {c["case_id"]: c for c in json.load(open(OUT / "adjudication_cases.json"))}
verdicts = {v["case_id"]: v for v in json.load(open(OUT / "golden_verdicts.json"))}

if len(sys.argv) > 1:  # rescore another detector version on the same golden cells
    det_rows = [json.loads(l) for l in open(OUT.parent / sys.argv[1]
                                            if not Path(sys.argv[1]).exists() else sys.argv[1])]
    for c in cases.values():
        c["detector_days"] = sorted({r["day"] for r in det_rows
                                     if (r["game_id"], r["player"], r["channel"], r["tell_id"]) ==
                                        (c["game_id"], c["player"], c["channel"], c["tell_id"])})
    print(f"rescored against {sys.argv[1]}")

stats = {ch: {"tp": 0, "fp": 0, "slip": 0, "miss_cells": 0, "clean_neg": 0, "extra_days": 0}
         for ch in ("vote", "discussion")}
for cid, c in sorted(cases.items()):
    v = verdicts.get(cid)
    if v is None:
        print(f"UNJUDGED: {cid}")
        continue
    ch, det, gold = c["channel"], set(c["detector_days"]), set(v["days"])
    s = stats[ch]
    if c["kind"] == "positive":
        s["tp"] += len(det & gold)
        for d in det - gold:
            (s.__setitem__("slip", s["slip"] + 1) if any(abs(d - g) == 1 for g in gold)
             else s.__setitem__("fp", s["fp"] + 1))
        s["extra_days"] += len(gold - det)   # detector under-reported extra days of a real tell
    else:
        if gold and not (det & gold):
            s["miss_cells"] += 1      # golden found days; detector (still) reports none of them
        elif gold:
            s["tp"] += len(det & gold)  # a rescored version recovered the miss
        else:
            s["clean_neg"] += 1
            s["fp"] += len(det)         # rescored version detects in a golden-empty cell

for ch, s in stats.items():
    n_pos = s["tp"] + s["fp"] + s["slip"]
    n_neg = s["miss_cells"] + s["clean_neg"]
    prec = s["tp"] / n_pos if n_pos else float("nan")
    print(f"{ch:10s} precision(tell,day)={prec:.2f}  [tp={s['tp']} fp={s['fp']} slip={s['slip']}] "
          f"| neg cells clean {s['clean_neg']}/{n_neg} (missed {s['miss_cells']}) "
          f"| golden extra days on positives: {s['extra_days']}")
