"""Held-out provisional lift table — PROBE SCAFFOLDING (experiment_log.md §14).

Consumes the held-out detector runs (outputs/heldout/*, k=2 union: full-view det_v1 +
split-view det_v2), joins exhibitor roles deterministically from the game records, and
computes per-tell lift over the cast prior with shrinkage.

PROVISIONAL by construction: the detector is temp-golden-grade (owner adjudication pending),
so every number here is direction+magnitude preview, not certified credit input. What IS
controlled here, unlike the 5-game preview: the games are HELD OUT (tells were mined from the
baseline arm only; these are the five memory arms), and denominators are complete (every
scanned player-slot counted).

Lift convention: exhibitor-grain. n = distinct (game, player) exhibitors; evil share =
exhibitors revealed as wolf/serial_killer over n; prior = 3/9 cast slots. Shrunk share pulls
toward the prior with K=5 pseudo-exhibitors (the credit design's small-evidence guard):
  shrunk_share = (evil + K*prior) / (n + K);  shrunk_lift = shrunk_share - prior

  PYTHONPATH=. poetry run python evidence/extraction/tell_extraction/heldout_lift.py
"""

from __future__ import annotations

import glob
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

PROBE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(PROBE_DIR.parents[2]))

from tell_mining_probe import load_games

EVIL = {"wolf", "werewolf", "serial_killer"}
PRIOR = 3 / 9
SHRINK_K = 5

# PAIRED-DESIGN NOTE: the five v6ab arms replay the SAME 12 boards (game_ids and role maps are
# identical across arms — verified), so a game is identified by (arm, game_id). Roles join
# correctly either way (pairing pins the cast); what must NOT collapse across arms is the
# union dedup key and the exhibitor key — the arms are different games behaviorally.
games: dict[tuple, dict] = {}
for cfg in ("skboth", "skobs", "sksp", "townobs", "townsp"):
    for g in load_games(f"batch_results/v6ab_{cfg}.jsonl", 12):
        games[(g["_source"], g["game_id"])] = g

rows, seen = [], set()
for p in sorted(glob.glob(str(PROBE_DIR / "outputs" / "heldout" / "*_v*.jsonl"))):
    for line in open(p):
        r = json.loads(line)
        key = (r["source"], r["game_id"], r["player"], r["channel"], r["tell_id"], r["day"])
        if key in seen or r.get("screen_flags"):
            continue
        seen.add(key)
        rows.append(r)

slots = Counter()
for g in games.values():
    for role in g["roles"].values():
        slots[role] += 1
n_games = len(games)
print(f"{len(rows)} unioned detections over {n_games} held-out games | role slots: {dict(slots)}")

cl = json.load(open(PROBE_DIR / "outputs" / "checklist_v0.json"))
text = {t["tell_id"]: t["text"] for ch in cl for t in cl[ch]}

agg: dict[str, set] = defaultdict(set)
for r in rows:
    role = games[(r["source"], r["game_id"])]["roles"].get(r["player"])
    if role:
        agg[r["tell_id"]].add((r["source"], r["game_id"], r["player"], role))

table = []
for tid, ex in agg.items():
    n = len(ex)
    evil = sum(1 for *_, role in ex if role in EVIL)
    shrunk = (evil + SHRINK_K * PRIOR) / (n + SHRINK_K)
    roles = Counter(role for *_, role in ex)
    table.append({
        "tell_id": tid, "channel": tid.split("_")[0], "text": text[tid],
        "n": n, "evil": evil, "raw_share": evil / n,
        "shrunk_share": shrunk, "shrunk_lift": shrunk - PRIOR,
        "roles": dict(roles),
        "role_rates": {role: roles.get(role, 0) / slots[role] for role in slots},
    })

out = PROBE_DIR / "outputs" / "heldout" / "provisional_lift_table.json"
out.write_text(json.dumps({
    "provenance": {"games": n_games, "arms": "v6ab memory arms: 12 PAIRED boards x 5 arms (same casts; arms are behaviorally distinct games but not fully independent samples)",
                   "detector": "det_v1 full-view UNION det_v2 split-view (temp-golden grade)",
                   "status": "PROVISIONAL — owner golden pending", "shrink_k": SHRINK_K,
                   "prior": PRIOR},
    "tells": sorted(table, key=lambda t: -abs(t["shrunk_lift"])),
}, indent=1))

print(f"\nwrote {out}\n")
for label, rows_ in (("EVIL-LEANING (shrunk lift, n>=8)",
                      sorted((t for t in table if t["n"] >= 8), key=lambda t: -t["shrunk_lift"])[:12]),
                     ("TOWN-LEANING (shrunk lift, n>=8)",
                      sorted((t for t in table if t["n"] >= 8), key=lambda t: t["shrunk_lift"])[:12])):
    print(f"== {label} ==")
    for t in rows_:
        print(f"  lift={t['shrunk_lift']:+.2f} raw={t['evil']:2d}/{t['n']:3d} [{t['channel']:4s}] {t['text'][:88]}")
    print()
