"""Compounding loop — (a) CREDIT-APPLY: write realized de-luck credit into a store's strategy points.

Between generations the loop credits the SPs an agent FOLLOWED by the de-luck outcome of the decisions
they drove (reusing credit_backfill's faction-relative de-luck scoring), and writes the
positive/neutral/negative tallies onto the StoredStrategyPoint counts — the signal (b) consolidation
weights by. Adoption already writes follow/override live; this fills the outcome half that was only ever
backfilled offline.

ROLLING WINDOW = the dumps glob: pass only the recent W generations' batch records and the counts are
RECOMPUTED (set, not accumulated) over that window each tick, so stale credit ages out — the
non-stationarity guard, for free.
"""

from __future__ import annotations

import json
from pathlib import Path

from evaluation.src.experiments.credit_backfill import build_ledger, compute_base_rates


def credit_apply(store_sp_path: str | Path, dumps_glob: str,
                 base_rates: dict | None = None) -> dict:
    """Recompute the de-luck ledger over `dumps_glob` and SET positive/neutral/negative/follow counts on
    matching SPs in `store_sp_path` (strategy_points.json). Returns {credited, matched, total} stats.

    base_rates default = memory-off per-cell means computed from the same dumps (the de-luck baseline);
    pass a frozen set to reuse a calibration baseline across generations."""
    store_sp_path = Path(store_sp_path)
    base_rates = base_rates if base_rates is not None else compute_base_rates(dumps_glob)
    ledger, _ = build_ledger(dumps_glob, base_rates)

    store = json.loads(store_sp_path.read_text())
    matched = credited = total = 0
    for recs in store.get("namespaces", {}).values():
        for r in recs:
            total += 1
            c = ledger.get(r["key"])
            if c is None:
                continue
            matched += 1
            v = r["value"]
            v["positive_count"] = c.positive
            v["neutral_count"] = c.neutral
            v["negative_count"] = c.negative
            v["follow_count"] = c.follow
            credited += 1
    store_sp_path.write_text(json.dumps(store, indent=2))
    # persist the per-cell de-luck baseline next to the store: consolidation needs it to compute LIFT
    # (raw pos/neg counts carry the halo — e.g. SK non-abstain is ~always "positive"; lift = utility −
    # baseline is the real de-luck signal). base_rates: channel "role/phase" -> (mean, n).
    (store_sp_path.parent / "base_rates.json").write_text(
        json.dumps({k: list(v) for k, v in base_rates.items()}, indent=2))
    return {"total_sps": total, "credited": credited, "ledger_keys": len(ledger), "matched": matched}


def sp_lift(value: dict, base_mean: float = 0.0) -> float | None:
    """De-luck shrunk-lift for a stored SP from its counts + the per-cell baseline. None if no follows.

    utility = (positive − negative)/follow; lift = utility − base_mean; shrunk = lift·follow/(follow+5).
    The baseline strip is what separates the SK −0.30 blend loser (raw utility +0.39) from a real winner.
    Caller supplies base_mean = base_rates["role/phase"][0] for this SP's namespace."""
    follow = value.get("follow_count", 0)
    if not follow:
        return None
    util = (value.get("positive_count", 0) - value.get("negative_count", 0)) / follow
    lift = util - base_mean
    return lift * follow / (follow + 5)


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--store-sp", required=True, help="strategy_points.json to credit (in place)")
    ap.add_argument("--dumps", required=True, help="glob of this window's batch records (eval-case-bearing)")
    args = ap.parse_args()
    print(credit_apply(args.store_sp, args.dumps))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
