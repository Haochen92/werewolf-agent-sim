"""v7 (d) — the FREE deterministic discussion-credit slice (zero spend).

Credits day_discussion SPs on the only cleanly per-SP-computable deterministic signal: ADVOCACY
CORRECTNESS (the offense axis). An accusation (addressed_targets stance=accusation) is scored
faction-relative on the accused target's true role — reusing credit_backfill._vote_credit (an
accusation = a vote-in-words). Transmission credit is BLOCKED (needs the role_claims persist); heat
credit is per-day/tautological (the LLM tagger's job) — both out of this slice.

Reports: (1) COVERAGE — what fraction of followed discussion SP-instances are on accusatory turns
(the ceiling for this free signal); (2) does the credit SEPARATE; (3) HELD-OUT reproduction (split
games, corr lift_A vs lift_B) = is it signal or noise. Tells us how much of d is achievable with no LLM.

  poetry run python evidence/v7_final/discussion_credit_deterministic.py
"""

import glob
import json
import os
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from evaluation.src.loop.credit_backfill import VERDICT_VALUE, _vote_credit  # noqa: E402

DUMPS = "batch_results/*v6ab*.jsonl"
SHRINK_K = 5


def _turn_advocacy_value(ec: dict, roles: dict) -> float | None:
    """Mean faction-relative value over this turn's accusations, or None if no accusation."""
    msg = ec.get("agent_message") or {}
    accusations = [t for t in (msg.get("addressed_targets") or []) if t.get("stance") == "accusation"]
    if not accusations:
        return None
    vals = []
    for a in accusations:
        tgt = a.get("target")
        if tgt and tgt in roles:
            vals.append(VERDICT_VALUE[_vote_credit(ec["player_role"], tgt, roles)])
    return sum(vals) / len(vals) if vals else None


def _iter_discussion(dumps_glob: str):
    for dump in sorted(glob.glob(dumps_glob)):
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
                if ec and ec.get("action_phase") == "day_discussion":
                    yield str(g.get("game_id")), roles, ec


def _half(gid: str) -> int:
    return sum(ord(c) for c in gid) % 2


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
    # baseline: memory-OFF mean advocacy value per (role) cell
    base_sum, base_n = defaultdict(float), defaultdict(int)
    # coverage counters
    cov = {"followed_sp_instances": 0, "accusatory": 0, "turns": 0, "acc_turns": 0}
    for gid, roles, ec in _iter_discussion(DUMPS):
        v = _turn_advocacy_value(ec, roles)
        if not ec.get("memory_enabled"):
            if v is not None:
                base_sum[ec["player_role"]] += v
                base_n[ec["player_role"]] += 1
            continue
        cov["turns"] += 1
        n_fol = sum(1 for sv in (ec.get("strategy_verdicts") or []) if sv.get("verdict") == "follow")
        cov["followed_sp_instances"] += n_fol
        if v is not None:
            cov["acc_turns"] += 1
            cov["accusatory"] += n_fol
    base = {r: base_sum[r] / base_n[r] for r in base_n}

    # per-SP credit, split by game half for held-out reproduction
    led = {0: defaultdict(lambda: [0, 0.0]), 1: defaultdict(lambda: [0, 0.0])}  # key -> [follow, bsum]
    for gid, roles, ec in _iter_discussion(DUMPS):
        if not (ec.get("memory_enabled") and ec.get("strategy_verdicts")):
            continue
        v = _turn_advocacy_value(ec, roles)
        if v is None:
            continue
        b = base.get(ec["player_role"], 0.0)
        h, idx = _half(gid), ec.get("strategy_index_to_key") or {}
        for sv in ec["strategy_verdicts"]:
            if sv.get("verdict") != "follow":
                continue
            key = idx.get(str(sv.get("strategy_index")))
            if key:
                led[h][key][0] += 1
                led[h][key][1] += v - b

    print("=== COVERAGE (the ceiling of the free advocacy signal) ===")
    print(f"  memory-on discussion turns: {cov['turns']} | accusatory: {cov['acc_turns']} "
          f"({cov['acc_turns']/max(cov['turns'],1):.0%})")
    print(f"  followed discussion SP-instances: {cov['followed_sp_instances']} | on accusatory turns: "
          f"{cov['accusatory']} ({cov['accusatory']/max(cov['followed_sp_instances'],1):.0%}) "
          "<- the rest (defense/neutral) are NOT creditable by this free slice")

    # combined ledger for the separation read
    comb = defaultdict(lambda: [0, 0.0])
    for h in (0, 1):
        for k, (f, s) in led[h].items():
            comb[k][0] += f
            comb[k][1] += s
    def shrunk(f, s):
        return (s / f) * f / (f + SHRINK_K) if f else 0.0
    deep = [(k, f, s) for k, (f, s) in comb.items() if f >= 3]
    lifts = [shrunk(f, s) for _, f, s in deep]
    pos = sum(1 for x in lifts if x > 0.1)
    neg = sum(1 for x in lifts if x < -0.1)
    print(f"\n=== SEPARATION (discussion SPs with >=3 advocacy-follows, n={len(deep)}) ===")
    print(f"  shrunk-lift split:  >+0.1: {pos}   [-0.1,+0.1]: {len(deep)-pos-neg}   <-0.1: {neg}")

    # held-out reproduction
    both = [(k, led[0][k], led[1][k]) for k in set(led[0]) & set(led[1])
            if led[0][k][0] >= 3 and led[1][k][0] >= 3]
    print(f"\n=== HELD-OUT REPRODUCTION (>=3 follows in BOTH halves, n={len(both)}) ===")
    if len(both) >= 3:
        la = [shrunk(a[0], a[1]) for _, a, _ in both]
        lb = [shrunk(b[0], b[1]) for _, _, b in both]
        print(f"  Pearson(lift_A, lift_B) = {_pearson(la, lb):+.2f}  (>0 => signal reproduces)")
    else:
        print("  too few doubly-mature discussion SPs (advocacy on accusatory turns is sparse) "
              "-> underpowered; the free signal is thin.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
