"""Temp-golden case sampler — PROBE SCAFFOLDING (experiment_log.md §5).

Builds the adjudication case set for the detector's TEMPORARY golden (owner-sanctioned
stand-in 2026-07-12: strong-LLM adjudication + Fable review; the owner's own adjudication
remains the run-gating golden later). Stratification:

- POSITIVE cases: detector rows, spread across channels / distinct tells / games
  (unflagged rows preferred) — adjudicated for precision.
- NEGATIVE cases: (game, player, channel, tell) cells the detector scanned but reported
  nothing for, weighted toward head tells — adjudicated for recall.

Also dumps each sampled game's role-blind public transcript to outputs/transcripts/ so the
adjudicating agents read exactly what the detector saw (plus true roles NOWHERE).

  PYTHONPATH=. poetry run python evidence/extraction/tell_extraction/golden_sampler.py
"""

from __future__ import annotations

import json
import random
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from tell_mining_probe import DEFAULT_DUMPS, _game_days, _render_day, load_games

PROBE_DIR = Path(__file__).resolve().parent.parent
OUT = PROBE_DIR / "outputs"
N_POS, N_NEG = 20, 20
HEAD_PER_CHANNEL = 12  # negatives drawn from the top of the checklist ordering

rng = random.Random(20260712)

rows = [json.loads(l) for l in open(OUT / "detector_det_v1.jsonl")]
scanned = json.load(open(OUT / "detector_det_v1_scanned.json"))
checklist = json.load(open(OUT / "checklist_v0.json"))
tell_text = {t["tell_id"]: t["text"] for ch in checklist for t in checklist[ch]}

# ---- positives: one row per (tell, game) first, round-robin channels ----------------------
by_key = defaultdict(list)
for r in rows:
    if not r["screen_flags"]:
        by_key[(r["channel"], r["tell_id"], r["game_id"])].append(r)
pos_pool = {ch: sorted(k for k in by_key if k[0] == ch) for ch in ("vote", "discussion")}
for ch in pos_pool:
    rng.shuffle(pos_pool[ch])
positives = []
while len(positives) < N_POS and any(pos_pool.values()):
    for ch in ("vote", "discussion"):
        if pos_pool[ch] and len(positives) < N_POS:
            key = pos_pool[ch].pop()
            positives.append(rng.choice(by_key[key]))

# ---- negatives: scanned cells with zero detections for a head tell ------------------------
detected_cells = {(r["game_id"], r["player"], r["channel"], r["tell_id"]) for r in rows}
neg_pool = []
for s in scanned:
    for t in checklist[s["channel"]][:HEAD_PER_CHANNEL]:
        cell = (s["game_id"], s["player"], s["channel"], t["tell_id"])
        if cell not in detected_cells:
            neg_pool.append(cell)
rng.shuffle(neg_pool)
# spread: at most 2 negatives per (game, tell)
negatives, used = [], defaultdict(int)
for cell in neg_pool:
    if used[(cell[0], cell[3])] < 2 and len(negatives) < N_NEG:
        used[(cell[0], cell[3])] += 1
        negatives.append(cell)

# ---- emit cases + role-blind transcripts ---------------------------------------------------
cases = []
for i, r in enumerate(positives):
    cases.append({"case_id": f"pos_{i}", "kind": "positive", "game_id": r["game_id"],
                  "player": r["player"], "channel": r["channel"], "tell_id": r["tell_id"],
                  "tell_text": tell_text[r["tell_id"]],
                  "detector_days": sorted({x["day"] for x in rows
                                           if (x["game_id"], x["player"], x["channel"], x["tell_id"]) ==
                                              (r["game_id"], r["player"], r["channel"], r["tell_id"])})})
for i, (gid, player, ch, tid) in enumerate(negatives):
    cases.append({"case_id": f"neg_{i}", "kind": "negative", "game_id": gid, "player": player,
                  "channel": ch, "tell_id": tid, "tell_text": tell_text[tid],
                  "detector_days": []})
(OUT / "adjudication_cases.json").write_text(json.dumps(cases, indent=1))

games = {g["game_id"]: g for g in load_games(DEFAULT_DUMPS, 5)}
tdir = OUT / "transcripts"
tdir.mkdir(exist_ok=True)
for gid in sorted({c["game_id"] for c in cases}):
    rec = games[gid]
    txt = "\n\n".join(_render_day(rec, d) for d in _game_days(rec))
    (tdir / f"{gid}.txt").write_text(txt)

from collections import Counter
print(f"{len(cases)} cases ({sum(1 for c in cases if c['kind']=='positive')} pos / "
      f"{sum(1 for c in cases if c['kind']=='negative')} neg) | "
      f"channels: {Counter(c['channel'] for c in cases)} | "
      f"distinct tells: {len({c['tell_id'] for c in cases})} | "
      f"games: {len({c['game_id'] for c in cases})}")
