# ── FROZEN RECORD (stamped 2026-07-05) ──────────────────────────
# Dated evidence artifact, NOT maintained code. It answered its question once
# (verdict: ../README.md); it is kept runnable-as-of last touch (1835863) but is
# not import-safe against future refactors. Standing apparatus lives in
# evaluation/src/instrument_validation/.
# ────────────────────────────────────────────────────────────────────────────
"""v7 (c) — two FREE extraction-shape screens (zero spend) over the RAW (no-dedup) v6_1 store.

The store is the per-cell re-extraction output BEFORE dedup, so every observation still carries its
source game_id + (role, phase) namespace — i.e. the raw shape of what the extractor emitted per game.

SCREEN 1 — QUOTA-BINDING. The prompt asks for "6-12 observations" per cell with a soft "may yield
fewer" hedge. If the per-(game,cell) count is pinned near the cap regardless of game, the floor is
binding and padding pressure is real; if it varies naturally, the hedge already works.

SCREEN 2 — REDUNDANCY (padding SIGNATURE). Within each (game, cell) the prompt says "never pad with
near-restatements". Measure intra-group mean pairwise lexical similarity (token Jaccard over
situation+approach+outcome — free, no model) and ask: do bigger cells carry MORE near-restatement?
A positive count->similarity slope = the floor is being filled with restatements = padding.

NEITHER screen touches CONFABULATION (the lesson being causally wrong) — that is not cleanly
free-screenable; it needs the re-extraction screen or downstream credit. Stated, not hidden.

  poetry run python evidence/v7_final/extraction_screens/extraction_quota_screen.py
"""

import json
from collections import defaultdict
from itertools import combinations

STORE = "memory_stores/v6_1/observations.json"
CAP = 12  # prompt's stated upper bound ("6-12 observations")


def _text(val: dict) -> str:
    parts = [str(val.get(f, "")) for f in ("situation", "approach", "outcome", "immediate_response")]
    return " ".join(p for p in parts if p)


def _tokens(s: str) -> set:
    return {w for w in "".join(c.lower() if c.isalnum() else " " for c in s).split() if len(w) > 2}


def _jaccard(a: set, b: set) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


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
    store = json.load(open(STORE))
    ns = store["namespaces"]

    # group obs by (cell, game_id)
    groups = defaultdict(list)  # (cell, game_id) -> [value, ...]
    total_obs = 0
    games = set()
    for cell, records in ns.items():
        role_phase = "/".join(cell.split("/")[1:])  # drop leading "observations"
        for rec in records:
            v = rec["value"]
            gid = v.get("game_id", "?")
            groups[(role_phase, gid)].append(v)
            total_obs += 1
            games.add(gid)

    counts = [len(g) for g in groups.values()]
    n_groups = len(counts)
    print(f"RAW store: {total_obs} obs across {len(games)} games, {len(ns)} cells, "
          f"{n_groups} (game,cell) groups\n")

    # ---- SCREEN 1: quota-binding ----
    print("=== SCREEN 1 — QUOTA-BINDING (obs per game-cell; prompt says 6-12) ===")
    hist = defaultdict(int)
    for c in counts:
        hist[c] += 1
    mean = sum(counts) / n_groups
    at_cap = sum(1 for c in counts if c >= CAP)
    over_cap = sum(1 for c in counts if c > CAP)
    below_floor = sum(1 for c in counts if c < 6)
    print(f"  mean={mean:.2f}  min={min(counts)}  max={max(counts)}  "
          f"median={sorted(counts)[n_groups//2]}")
    print(f"  at/over cap (>={CAP}): {at_cap}/{n_groups} ({at_cap/n_groups:.0%})   "
          f"OVER cap (>{CAP}): {over_cap}   below floor (<6): {below_floor} "
          f"({below_floor/n_groups:.0%})")
    print("  histogram (count: #groups):")
    for c in sorted(hist):
        bar = "#" * min(hist[c], 60)
        print(f"    {c:>3}: {hist[c]:>4} {bar}")
    pin = at_cap / n_groups
    print(f"  -> {'PINNED at cap = floor BINDING (padding pressure real)' if pin > 0.4 else 'count VARIES = hedge largely works; floor not the main disease'} "
          f"(pin={pin:.0%})\n")

    # ---- SCREEN 2: redundancy vs group size ----
    print("=== SCREEN 2 — REDUNDANCY (intra-group mean pairwise Jaccard) vs group size ===")
    sizes, sims = [], []
    high_sim_pairs = 0
    total_pairs = 0
    for (cell, gid), vals in groups.items():
        if len(vals) < 2:
            continue
        toks = [_tokens(_text(v)) for v in vals]
        pairs = list(combinations(range(len(vals)), 2))
        ms = [_jaccard(toks[i], toks[j]) for i, j in pairs]
        sizes.append(len(vals))
        sims.append(sum(ms) / len(ms))
        high_sim_pairs += sum(1 for s in ms if s > 0.5)
        total_pairs += len(ms)
    r = _pearson(sizes, sims)
    print(f"  groups with >=2 obs: {len(sims)}   mean intra-group similarity: {sum(sims)/len(sims):.3f}")
    print(f"  high-similarity pairs (Jaccard>0.5 = near-restatement): "
          f"{high_sim_pairs}/{total_pairs} ({high_sim_pairs/max(total_pairs,1):.1%})")
    print(f"  Pearson(group_size, mean_similarity) = {r:+.2f}")
    print(f"  -> {'bigger cells ARE more redundant = padding signature' if r > 0.15 else 'no size->redundancy slope = extra obs are DISTINCT, not restatements'}")

    # similarity binned by size, to see the shape
    by_size = defaultdict(list)
    for s, sim in zip(sizes, sims):
        by_size[s].append(sim)
    print("  mean similarity by group size:")
    for s in sorted(by_size):
        print(f"    size {s:>2}: sim {sum(by_size[s])/len(by_size[s]):.3f}  (n={len(by_size[s])})")

    print("\n[neither screen addresses CONFABULATION — lesson causally wrong — that needs re-extraction "
          "or downstream credit, not a free read]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
