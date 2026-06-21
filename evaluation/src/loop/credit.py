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

import glob
import json
import os
from collections import defaultdict
from pathlib import Path

from evaluation.src.experiments.credit_backfill import (
    VERDICT_VALUE, SPCredit, _vote_credit, build_ledger, compute_base_rates,
)


def _discussion_ledger(dumps_glob: str) -> tuple[dict, dict]:
    """(d) free floor — credit day_discussion SPs by the DAY-VOTE ENDPOINT (the day's lynch outcome,
    faction-relative): discussion has no clean per-decision proxy, so it's scored by the vote it feeds.
    Returns ({sp_key: SPCredit}, {channel: (base_mean, n)}). Reproduced held-out at +0.51 (M1)."""
    base_sum, base_n = defaultdict(float), defaultdict(int)
    rows = []  # (channel, verdict_str, eval_case) for memory-ON discussion turns
    for dump in sorted(glob.glob(dumps_glob)):
        for line in open(dump):
            if not line.strip():
                continue
            g = json.loads(line)
            roles, path = g.get("roles"), g.get("eval_cases_path")
            if not roles or not path or not os.path.exists(path):
                continue
            lynch = {dr.get("day"): dr.get("voted_player") for dr in g.get("day_resolutions", [])}
            for cl in open(path):
                if not cl.strip():
                    continue
                ec = (json.loads(cl).get("output") or {}).get("eval_case") or {}
                if ec.get("action_phase") != "day_discussion":
                    continue
                v = _vote_credit(ec.get("player_role"), lynch.get(ec.get("day")), roles)
                ch = f"{ec.get('player_role')}/day_discussion"
                if not ec.get("memory_enabled"):
                    base_sum[ch] += VERDICT_VALUE[v]
                    base_n[ch] += 1
                elif ec.get("strategy_verdicts"):
                    rows.append((ch, v, ec))
    base = {ch: (base_sum[ch] / base_n[ch], base_n[ch]) for ch in base_n}
    ledger: dict = defaultdict(SPCredit)
    for ch, v, ec in rows:
        idx = ec.get("strategy_index_to_key") or {}
        for sv in ec["strategy_verdicts"]:
            if sv.get("verdict") == "follow":
                key = idx.get(str(sv.get("strategy_index")))
                if key:
                    ledger[key].add(v, ch, base.get(ch, (0.0, 0))[0])
    return dict(ledger), base


def _tagger_ledger(dumps_glob: str, tags_dir: str | None = None) -> tuple[dict, dict]:
    """(d) tier 2/3 — credit via the OMNISCIENT TAGGER (one pass/game): day_discussion SPs by the holistic
    verdict (framing/credibility/role-reveal weighed); night_action SPs by READ-QUALITY (de-lucks
    `_night_credit`'s outcome-luck). Returns (disc_ledger, night_ledger). PAID (flash-lite, env-pin model).
    Tagger verdicts are de-luck → base 0. tags_dir persists tags per game_id (no re-tagging across the
    rolling window each generation)."""
    from evaluation.src.loop.discussion_tagger import tag_game_cached  # lazy: pulls LLM deps only when used
    disc: dict = defaultdict(SPCredit)
    night: dict = defaultdict(SPCredit)
    for dump in sorted(glob.glob(dumps_glob)):
        for line in open(dump):
            if not line.strip():
                continue
            g = json.loads(line)
            roles, path = g.get("roles"), g.get("eval_cases_path")
            if not roles or not path or not os.path.exists(path):
                continue
            d_tags, n_tags = tag_game_cached(g, tags_dir)
            for cl in open(path):
                if not cl.strip():
                    continue
                ec = (json.loads(cl).get("output") or {}).get("eval_case") or {}
                phase = ec.get("action_phase")
                if not ec.get("memory_enabled") or not ec.get("strategy_verdicts"):
                    continue
                if phase == "day_discussion":
                    t, led = d_tags.get((ec.get("day"), ec.get("player_id"))), disc
                elif phase == "night_action":
                    t, led = n_tags.get((ec.get("day"), ec.get("player_id"))), night
                else:
                    continue
                if not t:
                    continue
                ch = f"{ec.get('player_role')}/{phase}"
                idx = ec.get("strategy_index_to_key") or {}
                for sv in ec["strategy_verdicts"]:
                    if sv.get("verdict") == "follow":
                        key = idx.get(str(sv.get("strategy_index")))
                        if key:
                            led[key].add(t["verdict"], ch, 0.0)  # tagger de-luck → base 0
    return dict(disc), dict(night)


def credit_apply(store_sp_path: str | Path, dumps_glob: str,
                 base_rates: dict | None = None, discussion: bool = True,
                 discussion_mode: str = "floor", tags_dir: str | None = None) -> dict:
    """Recompute the de-luck ledger over `dumps_glob` and SET positive/neutral/negative/follow counts on
    matching SPs in `store_sp_path` (strategy_points.json). Returns {credited, matched, total} stats.

    base_rates default = memory-off per-cell means computed from the same dumps (the de-luck baseline);
    pass a frozen set to reuse a calibration baseline across generations. `discussion` (d's free floor)
    additionally credits day_discussion SPs by the day-vote endpoint, so all 3 channels get a signal."""
    store_sp_path = Path(store_sp_path)
    base_rates = base_rates if base_rates is not None else compute_base_rates(dumps_glob)
    ledger, _ = build_ledger(dumps_glob, base_rates)
    if discussion:
        if discussion_mode == "tagger":        # (d) tier 2/3: omniscient LLM tagger (paid)
            disc_ledger, night_ledger = _tagger_ledger(dumps_glob, tags_dir)
            # night_ledger OVERRIDES the deterministic _night_credit (de-luck read-quality > outcome-luck);
            # disc_ledger ADDS day_discussion (disjoint keys). Tagger verdicts de-luck → base 0.
            ledger = {**ledger, **night_ledger, **disc_ledger}
        else:                                   # (d) tier 1: day-vote endpoint free floor
            disc_ledger, disc_base = _discussion_ledger(dumps_glob)
            ledger = {**ledger, **disc_ledger}  # disjoint keys (vote/night vs day_discussion SPs)
            base_rates = {**base_rates, **disc_base}

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
