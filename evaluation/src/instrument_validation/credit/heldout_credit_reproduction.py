"""v7 b1 validation — held-out reproduction of the credit signal (zero spend, deterministic).

The circular-check guard: flagging losers on ALL games then deleting them is circular (you removed the
notes your own metric disliked, measured on the same data). This splits the v6ab games into two halves
by game_id, computes per-SP lift on EACH half independently, and asks the non-circular question: does a
note flagged a loser on half A stay negative on held-out half B? Plus the Pearson correlation of
lift_A vs lift_B. Positive / losers-stay-negative => the credit signal is real and stable => pruning is
justified. Flat => the threshold catches noise => back off before deleting anything.

Per the frozen-calibration design, the memory-off BASELINE is computed on the FULL data (a stable
reference); only the memory-on FOLLOWS are split A/B. Reuses the scoring from credit_backfill.

  poetry run python -m evaluation.src.instrument_validation.credit.heldout_credit_reproduction
"""

import glob
import json
import os
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from evaluation.src.loop.credit_backfill import (  # noqa: E402
    SPCredit, _decision_credit, compute_base_rates,
)

DUMPS = "batch_results/*v6ab*.jsonl"
F = 3          # min follows in EACH half to be comparable
TAU = -0.15    # the b1 drop threshold under test
N_FULL = 8     # the b1 follow floor (full-data); reported for context


def _iter_cases_with_game():
    for dump in sorted(glob.glob(DUMPS)):
        for line in open(dump):
            if not line.strip():
                continue
            g = json.loads(line)
            roles, path, gid = g.get("roles"), g.get("eval_cases_path"), str(g.get("game_id"))
            if not roles or not path or not os.path.exists(path):
                continue
            for cl in open(path):
                if not cl.strip():
                    continue
                env = json.loads(cl)
                if env.get("kind") != "agent_action_eval":
                    continue
                ec = (env.get("output") or {}).get("eval_case")
                if ec and ec.get("memory_enabled") and ec.get("strategy_verdicts"):
                    yield gid, roles, ec


def _half(gid: str) -> int:
    return sum(ord(c) for c in gid) % 2  # deterministic, content-based split


def _build_split(base_rates) -> tuple[dict, dict]:
    led = {0: defaultdict(SPCredit), 1: defaultdict(SPCredit)}
    for gid, roles, ec in _iter_cases_with_game():
        verdict = _decision_credit(ec, roles)
        if verdict is None:
            continue
        channel = f"{ec['player_role']}/{ec['action_phase']}"
        base = base_rates.get(channel, (0.0, 0))[0]
        idx = ec.get("strategy_index_to_key") or {}
        for sv in ec["strategy_verdicts"]:
            if sv.get("verdict") != "follow":
                continue
            key = idx.get(str(sv.get("strategy_index")))
            if key:
                led[_half(gid)][key].add(verdict, channel, base)
    return led[0], led[1]


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
    base = compute_base_rates(DUMPS)
    A, B = _build_split(base)
    both = [(k, A[k], B[k]) for k in set(A) & set(B) if A[k].follow >= F and B[k].follow >= F]
    print(f"split by game_id; full-data baseline. SPs with >={F} follows in BOTH halves: {len(both)}")
    if len(both) < 3:
        print("  too few doubly-mature SPs to test (expected — splitting halves the already-thin "
              "follows). Report as underpowered.")
        return 0

    la = [a.lift for _, a, _ in both]
    lb = [b.lift for _, _, b in both]
    r = _pearson(la, lb)
    print(f"\n=== STABILITY === Pearson(lift_A, lift_B) = {r:+.2f}  (n={len(both)})")
    print("    >0 => credit signal reproduces across independent game sets (real); ~0 => noise")

    # base rate of negativity on B (chance level a 'loser' is negative on held-out)
    negB = sum(1 for _, _, b in both if b.lift < 0)
    print(f"\n=== REPRODUCTION === baseline P(lift_B < 0) over all comparable SPs: "
          f"{negB}/{len(both)} = {negB/len(both):.0%}")
    losersA = [(k, a, b) for k, a, b in both if a.lift < TAU]
    if losersA:
        repro = sum(1 for _, _, b in losersA if b.lift < 0)
        print(f"    A-flagged losers (lift_A < {TAU}): {len(losersA)}; "
              f"still negative on held-out B: {repro}/{len(losersA)} = {repro/len(losersA):.0%}")
        print(f"    {'lift_A':>7} {'lift_B':>7} {'fA':>3} {'fB':>3}")
        for k, a, b in sorted(losersA, key=lambda t: t[1].lift):
            flag = "" if b.lift < 0 else "  <-- flipped positive on B"
            print(f"    {a.lift:+7.2f} {b.lift:+7.2f} {a.follow:3d} {b.follow:3d}{flag}")
    else:
        print(f"    no SP crosses lift_A < {TAU} with >={F} follows in both halves (loser tail thins "
              "under the split) — lower TAU/F or read the correlation instead.")

    print(f"\n(context: full-data b1 default is N>={N_FULL}, tau<={TAU})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
