"""Granularity screen — PROBE SCAFFOLDING (owner question 2026-07-13: at what granularity are
two tells "really different"?).

Operational answer, no semantics: two same-channel tells are THE SAME iff they fire on the
same instances at the same lift; they are DISTINCT iff their instance sets or lifts diverge.
(The owner's g1 adjudication instantiated both: vote_221/51/673 co-fire at ~0 lift -> one
behavior; the verbally-similar silence family splits +0.02 / +0.20 / +0.38 -> genuinely
three.) The screen turns the fold's merge step from a judgment call into ratification:

  MERGE proposal:  co-exhibitor Jaccard >= J_MERGE  and  |shrunk_lift gap| < LIFT_GAP
  HIERARCHY flag:  high containment (one tell's instances mostly inside another's) but the
                   lift gap is real -> parent/child granularity, keep both, note the link

Instance grain = (arm, game, player, day) within channel, from the held-out k=2 union
(complete denominators). Support floor keeps noise pairs out.

  PYTHONPATH=. poetry run python evidence/extraction/tell_extraction/granularity_screen.py
"""

from __future__ import annotations

import glob
import json
from collections import defaultdict
from pathlib import Path

PROBE_DIR = Path(__file__).resolve().parent.parent
OUT = PROBE_DIR / "outputs"
N_FLOOR = 10       # min instances per tell to be screened
J_MERGE = 0.5      # co-exhibitor Jaccard above which tells look like one behavior
J_CONTAIN = 0.7    # containment (|A&B|/min) above which one tell nests in another
LIFT_GAP = 0.05    # shrunk-lift gap below which discrimination is indistinguishable

lift = {r["tell_id"]: r["shrunk_lift"]
        for r in json.load(open(OUT / "heldout" / "provisional_lift_table.json"))["tells"]}
text = {t["tell_id"]: t["text"]
        for ch, ts in json.load(open(OUT / "checklist_v0.json")).items() for t in ts}

inst: dict[str, set] = defaultdict(set)
chan: dict[str, str] = {}
for fp in glob.glob(str(OUT / "heldout" / "*_v*.jsonl")):
    arm = Path(fp).name.split("_")[0]
    for line in open(fp):
        r = json.loads(line)
        inst[r["tell_id"]].add((arm, r["game_id"], r["player"], r["day"]))
        chan[r["tell_id"]] = r["channel"]

tells = sorted(t for t, s in inst.items() if len(s) >= N_FLOOR and t in lift)
merges, hierarchy = [], []
for i, a in enumerate(tells):
    for b in tells[i + 1:]:
        if chan[a] != chan[b]:
            continue
        ov = len(inst[a] & inst[b])
        if not ov:
            continue
        jac = ov / len(inst[a] | inst[b])
        contain = ov / min(len(inst[a]), len(inst[b]))
        gap = abs(lift[a] - lift[b])
        row = {"a": a, "b": b, "n_a": len(inst[a]), "n_b": len(inst[b]),
               "jaccard": round(jac, 2), "containment": round(contain, 2),
               "lift_a": round(lift[a], 3), "lift_b": round(lift[b], 3),
               "lift_gap": round(gap, 3)}
        if jac >= J_MERGE and gap < LIFT_GAP:
            merges.append(row)
        elif contain >= J_CONTAIN and gap >= LIFT_GAP:
            hierarchy.append(row)

out = {"params": {"n_floor": N_FLOOR, "j_merge": J_MERGE, "j_contain": J_CONTAIN,
                  "lift_gap": LIFT_GAP, "grain": "(arm, game, player, day) within channel",
                  "source": "held-out k=2 union (PROVISIONAL detector grade)"},
       "merge_proposals": sorted(merges, key=lambda r: -r["jaccard"]),
       "hierarchy_flags": sorted(hierarchy, key=lambda r: -r["containment"])}
(OUT / "granularity_screen.json").write_text(json.dumps(out, indent=1))

print(f"screened {len(tells)} tells (n>={N_FLOOR})")
print(f"\nMERGE proposals (same instances, same lift): {len(merges)}")
for r in out["merge_proposals"]:
    print(f"  {r['a']} + {r['b']}  J={r['jaccard']} lifts {r['lift_a']:+}/{r['lift_b']:+}")
    print(f"      a: {text.get(r['a'], '?')[:90]}")
    print(f"      b: {text.get(r['b'], '?')[:90]}")
print(f"\nHIERARCHY flags (nested instances, REAL lift gap — keep split): {len(hierarchy)}")
for r in out["hierarchy_flags"]:
    print(f"  {r['a']} ({r['lift_a']:+}, n={r['n_a']}) ⊃⊂ {r['b']} ({r['lift_b']:+}, n={r['n_b']})"
          f"  contain={r['containment']}")
