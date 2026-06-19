"""v7 (b/loop) — does cluster-SYNTHESIS (the loop's 'regeneration' step) concentrate SP QUALITY,
or is it quality-blind? Zero spend.

Setup we already have (no games re-run):
  - credit_backfill_ledger.json : per-game (v6_1) SP key -> lift/shrunk_lift/follow  (the credited layer)
  - memory_stores/v6_1            : per-game SPs (key -> action text, cell)            (what was followed)
  - memory_stores/v6_1_sp_cluster : the cluster_synth SPs (the regeneration OUTPUT, never played)

Synthesis clusters by SITUATION and DROPS net_verdict on purpose (cell.py) -> it is outcome-blind by
construction. PREDICTION: it carries forward winners and losers at the SAME rate -> the wash survives
regeneration -> the loop's improvement must come from the CREDIT-PRUNE (b), not from synthesis.

TEST: for each CREDITED per-game SP, is its directive 'carried forward' (a near lexical match exists in
the synth store, same cell)? Compare the lift distribution of CARRIED vs DROPPED. Quality-aware synthesis
=> carried SPs have higher lift than dropped. Quality-blind => equal.

  poetry run python evidence/v7_final/sp_synthesis_quality_check.py
"""

import json
from collections import defaultdict

LEDGER = "evidence/v7_final/credit_backfill_ledger.json"
PERGAME = "memory_stores/v6_1/strategy_points.json"
SYNTH = "memory_stores/v6_1_sp_cluster/strategy_points.json"
MIN_FOLLOW = 5          # only SPs with enough follows for a meaningful lift
CARRY_THRESH = 0.30     # token-Jaccard >= this in the same cell = "same directive carried forward"


def _tokens(s: str) -> set:
    return {w for w in "".join(c.lower() if c.isalnum() else " " for c in s).split() if len(w) > 2}


def _jaccard(a: set, b: set) -> float:
    return len(a & b) / len(a | b) if (a and b) else 0.0


def _load_cells(path: str) -> dict:
    """cell -> list of (key, action_text)."""
    sp = json.load(open(path))
    out = defaultdict(list)
    for cell, recs in sp["namespaces"].items():
        rp = "/".join(cell.split("/")[1:])
        for r in recs:
            out[rp].append((r["key"], r["value"].get("action", "")))
    return out


def main() -> int:
    ledger = json.load(open(LEDGER))
    pergame = _load_cells(PERGAME)         # cell -> [(key, action)]
    synth = _load_cells(SYNTH)
    synth_tok = {cell: [(_tokens(a), a) for _, a in lst] for cell, lst in synth.items()}

    # key -> (cell, action) for per-game SPs
    key_meta = {}
    for cell, lst in pergame.items():
        for k, a in lst:
            key_meta[k] = (cell, a)

    print(f"ledger: {len(ledger)} credited per-game SPs | synth store: "
          f"{sum(len(v) for v in synth.values())} SPs across {len(synth)} cells\n")

    rows = []  # (lift, follow, carried, best_sim)
    for k, c in ledger.items():
        if c["follow"] < MIN_FOLLOW or k not in key_meta:
            continue
        cell, action = key_meta[k]
        at = _tokens(action)
        cands = synth_tok.get(cell, [])
        best = max((_jaccard(at, st) for st, _ in cands), default=0.0)
        rows.append((c["shrunk_lift"], c["follow"], best >= CARRY_THRESH, best))

    n = len(rows)
    carried = [r for r in rows if r[2]]
    dropped = [r for r in rows if not r[2]]

    def grp(label, rs):
        if not rs:
            print(f"  {label:9} n=0")
            return
        lifts = [r[0] for r in rs]
        pos = sum(1 for x in lifts if x > 0.1)
        neg = sum(1 for x in lifts if x < -0.1)
        print(f"  {label:9} n={len(rs):3}  mean_lift={sum(lifts)/len(rs):+.3f}  "
              f"helpers(>+.1)={pos:2}  hurters(<-.1)={neg:2}  mean_sim={sum(r[3] for r in rs)/len(rs):.2f}")

    print(f"=== CARRIED-FORWARD vs DROPPED (credited SPs, follow>={MIN_FOLLOW}, n={n}, "
          f"carry@Jaccard>={CARRY_THRESH}) ===")
    grp("ALL", rows)
    grp("CARRIED", carried)
    grp("DROPPED", dropped)
    if len(carried) < 8:
        print(f"\n  ** UNDERPOWERED: only {len(carried)} lexical carry-matches (mean_sim {sum(r[3] for r in rows)/n:.2f}). "
              "Synthesis PARAPHRASES directives, so token-overlap cannot trace carry-forward. "
              "A clean empirical answer needs embeddings (small spend) or games on the synth store. "
              "The structural answer (below) does NOT need this test. **")
    elif carried and dropped:
        dlift = sum(r[0] for r in carried)/len(carried) - sum(r[0] for r in dropped)/len(dropped)
        print(f"\n  carried-minus-dropped mean lift = {dlift:+.3f}")
        print(f"  -> {'QUALITY-AWARE: synthesis keeps better SPs' if dlift > 0.1 else 'QUALITY-BLIND: wash survives regeneration; only the CREDIT-PRUNE (b) can fix it'}")

    # synth-side mirror: each synth SP inherits the lift of its nearest credited per-game SP
    print("\n=== SYNTH-SIDE: inherited lift of nearest credited per-game SP (does the regen store inherit the wash?) ===")
    key_by_cell = defaultdict(list)
    for k, c in ledger.items():
        if k in key_meta and c["follow"] >= MIN_FOLLOW:
            cell, action = key_meta[k]
            key_by_cell[cell].append((_tokens(action), c["shrunk_lift"]))
    inh = []
    for cell, lst in synth.items():
        for _, a in lst:
            at = _tokens(a)
            cands = key_by_cell.get(cell, [])
            best = max(cands, key=lambda t: _jaccard(at, t[0]), default=None)
            if best and _jaccard(at, best[0]) >= CARRY_THRESH:
                inh.append(best[1])
    if inh:
        pos = sum(1 for x in inh if x > 0.1)
        neg = sum(1 for x in inh if x < -0.1)
        print(f"  synth SPs matched to a credited SP: {len(inh)}  mean inherited lift={sum(inh)/len(inh):+.3f}  "
              f"helpers={pos}  hurters={neg}")
        print("  (helpers ~ hurters => the regenerated store inherits the same wash)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
