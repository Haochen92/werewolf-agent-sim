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

from evaluation.src.experiments.credit_backfill import VERDICT_VALUE, _decision_credit

TOWN = {"villager", "investigator", "healer", "vigilante"}


def generation_score(batch_glob: str) -> dict:
    """Mean de-luck decision value over ALL of a generation's decisions, split memory ON vs OFF and by
    faction. ON should slope up across generations; OFF is the flat baseline. Outcome-independent."""
    sums: dict[str, float] = defaultdict(float)
    ns: dict[str, int] = defaultdict(int)
    for dump in sorted(glob.glob(batch_glob)):
        for line in open(dump):
            if not line.strip():
                continue
            g = json.loads(line)
            roles, path = g.get("roles"), g.get("eval_cases_path")
            if not roles or not path or not os.path.exists(path):
                continue
            for cl in open(path):
                if not cl.strip():
                    continue
                env = json.loads(cl)
                if env.get("kind") != "agent_action_eval":
                    continue
                ec = (env.get("output") or {}).get("eval_case")
                if not ec:
                    continue
                verdict = _decision_credit(ec, roles)
                if verdict is None:
                    continue
                val = VERDICT_VALUE[verdict]
                arm = "on" if ec.get("memory_enabled") else "off"
                role = ec.get("player_role", "?")
                faction = "town" if role in TOWN else role
                for key in (f"{arm}/overall", f"{arm}/{faction}"):
                    sums[key] += val
                    ns[key] += 1
    return {k: round(sums[k] / ns[k], 3) for k in ns} | {f"n_{k}": ns[k] for k in ns}


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--batch", required=True, help="glob of a generation's batch record jsonl(s)")
    args = ap.parse_args()
    print(generation_score(args.batch))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
