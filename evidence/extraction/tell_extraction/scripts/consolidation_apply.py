"""Batch-consolidation apply + fresh-rate replay — PROBE SCAFFOLDING (experiment_log.md §3.9).

Consumes the Claude-side cluster verdicts (consolidation_clusters_{vote,discussion}.json),
applies drop-or-keep union (earliest tid survives as canonical; no rewording), and
re-derives the fresh-tell-per-game curve under the consolidated equivalence — with NO
API calls: tids encode global creation order and the sim metrics record fresh-per-game,
so each tell's creation game is exactly reconstructible; a cluster was "fresh at game g"
iff its EARLIEST member was created at g.

Support caveat: the store snapshot holds support counts, not instance lists, so a merged
cluster's support is the SUM of member supports — an upper bound (a (game, exhibitor)
pair that hit two fragments would be double-counted).

  PYTHONPATH=. poetry run python evidence/extraction/tell_extraction/consolidation_apply.py
"""

from __future__ import annotations

import json
from pathlib import Path

PROBE_DIR = Path(__file__).resolve().parent.parent
OUT = PROBE_DIR / "outputs"

snap = {t["tid"]: t for t in json.load(open(OUT / "ledger_sim_store.json"))}
metrics = [json.loads(l) for l in open(OUT / "ledger_sim_metrics.jsonl")]

# creation game per tell: tid integer = global creation index; fresh counts partition it
creation_game = {}
k = 0
for g, m in enumerate(metrics, start=1):
    for _ in range(m["fresh"]):
        creation_game[k] = g
        k += 1
assert k == len(snap)
idx = lambda tid: int(tid.split("_")[1])

# Fable verification overrides (experiment_log.md §3.9): tids excised from their cluster.
# vote_506: the exhibitor is not the one under attack — they voted a third party's accuser,
# so the retaliation cluster's trigger (self accused) doesn't hold.
EXCISED = {"vote_506"}

# ---- load + validate clusters ------------------------------------------------------------
clusters, borderline = [], []
for ch in ("vote", "discussion"):
    data = json.load(open(OUT / f"consolidation_clusters_{ch}.json"))
    seen = set()
    for c in data["clusters"]:
        tids = [t for t in c["tids"] if t not in EXCISED]
        if len(tids) < 2:
            continue
        for t in tids:
            assert t in snap, f"unknown tid {t}"
            assert snap[t]["channel"] == ch, f"cross-channel tid {t} in {ch}"
            assert t not in seen, f"tid {t} in two clusters"
            seen.add(t)
        clusters.append({**c, "tids": tids, "channel": ch})
    borderline.extend({**b, "channel": ch} for b in data.get("borderline", []))

# ---- drop-or-keep union ------------------------------------------------------------------
root = {}          # tid -> surviving canonical tid (earliest-created member)
for c in clusters:
    survivor = min(c["tids"], key=idx)
    for t in c["tids"]:
        root[t] = survivor
canon = lambda tid: root.get(tid, tid)

merged_away = sum(len(c["tids"]) - 1 for c in clusters)
consolidated = {}
for tid, t in snap.items():
    r = canon(tid)
    e = consolidated.setdefault(r, {"tid": r, "channel": t["channel"], "canonical": snap[r]["canonical"],
                                    "support": 0, "members": [], "statuses": set()})
    e["support"] += t["support"]           # upper bound (see module docstring)
    e["members"].append(tid)
    e["statuses"].add(t["status"])

print(f"clusters: {len(clusters)} | tells absorbed: {merged_away} | "
      f"store: {len(snap)} -> {len(consolidated)} canonicals | borderline pairs: {len(borderline)}")

# ---- consolidated fresh-rate curve -------------------------------------------------------
raw_fresh = [m["fresh"] for m in metrics]
cons_fresh = [0] * len(metrics)
for e in consolidated.values():
    g = min(creation_game[idx(t)] for t in e["members"])
    cons_fresh[g - 1] += 1
print("\n game | raw fresh | consolidated fresh")
for g in range(len(metrics)):
    print(f"  {g+1:3d} | {raw_fresh[g]:9d} | {cons_fresh[g]:9d}")
for name, s in (("raw", raw_fresh), ("consolidated", cons_fresh)):
    last10 = s[-10:]
    print(f"{name}: last-10 mean {sum(last10)/10:.1f} | games 11-20 mean {sum(s[10:20])/10:.1f} "
          f"| games 1-10 mean {sum(s[:10])/10:.1f}")

# ---- head after consolidation ------------------------------------------------------------
head = sorted(consolidated.values(), key=lambda e: -e["support"])[:15]
print("\ntop 15 consolidated (support = SUM of member supports, upper bound):")
for e in head:
    print(f"  n={e['support']:3d} x{len(e['members']):2d} [{e['channel']:4s}] {e['canonical'][:110]}")

snapshot = [{**e, "statuses": sorted(e["statuses"])} for e in consolidated.values()]
(OUT / "consolidated_store.json").write_text(json.dumps(snapshot, indent=1))
print(f"\nwrote {OUT / 'consolidated_store.json'}")
