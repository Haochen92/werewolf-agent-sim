"""Compounding loop — MEASUREMENT: per-generation de-luck decision quality (the slope proxy).

The loop "works" iff decision quality slopes UP across generations vs a flat memory-off baseline (plan
§4). This scores a generation's games by the SAME de-luck proxy the credit ledger uses (faction-relative
decision credit, outcome-independent) — overall + per-faction, so we can watch the deceiver cells (where
the synthesis fix concentrates) specifically.

Pure read over a batch jsonl's eval cases; no model, no spend.
"""

from __future__ import annotations

import glob
import json
import os
from collections import defaultdict

from evaluation.src.loop.credit_backfill import VERDICT_VALUE, _decision_credit, _majority_vote

TOWN = {"villager", "investigator", "healer", "vigilante"}


def generation_score(on_glob: str, off_glob: str | None = None, *,
                     skip_day1: bool = True, on_memory_active_only: bool = True) -> dict:
    """Mean de-luck decision value per faction for one generation, split by ARM. ON should slope up across
    generations; OFF is the flat baseline. Outcome-independent, pure read, no spend.

    Bucketing is by ARM (which dump the case came from), NOT by the per-decision `memory_enabled` flag. A
    flag-bucketed score mislabels a memoryless decision INSIDE an ON game — a day-1 retrieval skip, or a
    memory-disabled role under town_only — as 'off', polluting the OFF baseline with ON-arm games (and
    pulling those decisions OUT of the ON arm), so on/off end up on different decision mixes. Like-for-like
    by default: drop day-1 (memoryless in BOTH arms — pure noise for 'does memory help'), and count only
    memory-ACTIVE decisions in the ON arm, so on/<faction> reflects decisions that actually used memory and
    a faction with no memory this arm (e.g. wolf under town_only) is correctly EMPTY, not misleading."""
    sums: dict[str, float] = defaultdict(float)
    ns: dict[str, int] = defaultdict(int)

    def _score_arm(glob_pat: str | None, arm: str) -> None:
        if not glob_pat:
            return
        for dump in sorted(glob.glob(glob_pat)):
            for line in open(dump):
                if not line.strip():
                    continue
                g = json.loads(line)
                roles, path = g.get("roles"), g.get("eval_cases_path")
                if not roles or not path or not os.path.exists(path):
                    continue
                blend_by_day = {dr.get("day"): _majority_vote(dr) for dr in g.get("day_resolutions", [])}
                for cl in open(path):
                    if not cl.strip():
                        continue
                    env = json.loads(cl)
                    if env.get("kind") != "agent_action_eval":
                        continue
                    ec = (env.get("output") or {}).get("eval_case")
                    if not ec:
                        continue
                    if skip_day1 and ec.get("day") == 1:
                        continue                                  # day-1 is memoryless in BOTH arms
                    if arm == "on" and on_memory_active_only and not ec.get("memory_enabled"):
                        continue                                  # ON-arm decision that didn't use memory
                    verdict = _decision_credit(ec, roles, blend_by_day)
                    if verdict is None:
                        continue
                    val = VERDICT_VALUE[verdict]
                    role = ec.get("player_role", "?")
                    faction = "town" if role in TOWN else role
                    for key in (f"{arm}/overall", f"{arm}/{faction}"):
                        sums[key] += val
                        ns[key] += 1

    _score_arm(on_glob, "on")
    _score_arm(off_glob, "off")
    return {k: round(sums[k] / ns[k], 3) for k in ns} | {f"n_{k}": ns[k] for k in ns}


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--on", required=True, help="glob of the ON arm's batch record jsonl(s)")
    ap.add_argument("--off", default=None, help="glob of the OFF arm's batch record jsonl(s)")
    ap.add_argument("--include-day1", action="store_true", help="keep day-1 (memoryless) decisions")
    ap.add_argument("--on-all", action="store_true",
                    help="count ALL on-arm decisions, not only the memory-active ones")
    args = ap.parse_args()
    print(generation_score(args.on, args.off, skip_day1=not args.include_day1,
                           on_memory_active_only=not args.on_all))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
