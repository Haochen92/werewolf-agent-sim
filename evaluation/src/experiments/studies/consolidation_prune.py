"""v7 b1 — apply the deterministic credit pre-prune to a COPY of the store (never canonical).

Reads the credit ledger (a's output), drops strategy points with `follow >= N AND shrunk_lift < tau`
(clear, well-evidenced losers), on a COPY of the store. Canonical v6_1 is never mutated and the live
pointer is never flipped — adoption is a separate, gated step. Guard-asserted: never drops a positive-lift
or thin-evidence SP. The `indexed_cache.pkl` (embedding vectors, SHA-keyed to the JSON) is removed in the
copy since the JSON changed — it rebuilds on next seed (observations.json is untouched, SP-only prune).

  dry run:  poetry run python evaluation/src/experiments/studies/consolidation_prune.py
  apply:    poetry run python evaluation/src/experiments/studies/consolidation_prune.py --apply
"""

import argparse
import json
import shutil
import sys
from pathlib import Path

DEFAULT_LEDGER = "evidence/v7_final/credit_backfill_ledger.json"
DEFAULT_SRC = "memory_stores/v6_1"
DEFAULT_DST = "memory_stores/v6_1_b1pruned"


def _sp_record_map(store_dir: Path) -> dict[str, dict]:
    """key -> SP record (for action-text readout)."""
    ns = json.load(open(store_dir / "strategy_points.json"))["namespaces"]
    return {it["key"]: it["value"] for items in ns.values() for it in items}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--ledger", default=DEFAULT_LEDGER)
    ap.add_argument("--src", default=DEFAULT_SRC)
    ap.add_argument("--dst", default=DEFAULT_DST)
    ap.add_argument("--N", type=int, default=8, help="follow floor (evidence gate)")
    ap.add_argument("--tau", type=float, default=-0.15, help="drop if shrunk_lift < tau")
    ap.add_argument("--apply", action="store_true", help="write the pruned copy (else dry run)")
    args = ap.parse_args()
    src = Path(args.src)

    ledger = json.load(open(args.ledger))
    drop = {k: v for k, v in ledger.items() if v["follow"] >= args.N and v["shrunk_lift"] < args.tau}

    # ---- GUARD ASSERTS (safety: never kill a winner or a thin-evidence note) ----
    assert all(v["shrunk_lift"] < args.tau for v in drop.values()), "a drop is above tau"
    assert all(v["follow"] >= args.N for v in drop.values()), "a drop is below the follow floor"
    assert not any(v["shrunk_lift"] >= 0 for v in drop.values()), "would drop a non-negative-lift SP!"
    max_lift = max(v["shrunk_lift"] for v in ledger.values())
    assert max_lift > args.tau, "sanity: best SP must be far above the cut"

    records = _sp_record_map(src)
    assert all(k in records for k in drop), "a ledger drop-key is missing from the store!"

    # ---- prune (on an in-memory copy of the JSON) ----
    sp = json.load(open(src / "strategy_points.json"))
    ns = sp["namespaces"]
    before = sum(len(items) for items in ns.values())
    for nsk in ns:
        ns[nsk] = [it for it in ns[nsk] if it["key"] not in drop]
    after = sum(len(items) for items in ns.values())
    prevented = sum(v["follow"] for v in drop.values())

    print(f"=== b1 PRUNE (N>={args.N}, shrunk_lift<{args.tau}) ===")
    print(f"drop set: {len(drop)} SPs | store {before} -> {after} ({(before-after)/before:.1%} removed) "
          f"| follows prevented: {prevented}")
    print(f"winner-safety: best shrunk_lift in ledger = {max_lift:+.2f} (untouched)\n")
    print("dropped (clear, well-evidenced losers):")
    for k, v in sorted(drop.items(), key=lambda kv: kv[1]["shrunk_lift"]):
        act = (records[k].get("action", "") or "")[:64]
        print(f"  lift{v['shrunk_lift']:+.2f} raw{v['utility']:+.2f} n={v['follow']:3d}  {act}")

    assert before - after == len(drop), "pruned count != drop count"

    if args.apply:
        dst = Path(args.dst)
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(src, dst)
        json.dump(sp, open(dst / "strategy_points.json", "w"), indent=2)
        cache = dst / "indexed_cache.pkl"
        if cache.exists():
            cache.unlink()  # SHA-stale after the JSON edit; rebuilds on next seed
        print(f"\nWROTE pruned copy -> {dst}")
        print(f"  canonical {src} UNTOUCHED; live pointer NOT flipped (adoption is a separate gated step)")
        print("  indexed_cache.pkl removed (rebuilds on seed); observations.json unchanged (SP-only prune)")
    else:
        print("\nDRY RUN — re-run with --apply to write the pruned copy.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
