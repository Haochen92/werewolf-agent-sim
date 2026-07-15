"""Read ledger — the Brier meter on agent READ skill (evidence/credit/report.md §5; design record §3
Layer 2). Measures the AGENT, never a memory item: how well each role's stated per-player reads match
revealed roles. It exists as its own ledger because mixing application quality into a fact's credit
makes the fact's score depend on who applied it — tells are credited by detector accuracy, agents are
measured here, and the two never touch. Its headline consumer is the free book-vs-no-book readout: a
tell book that works should move the memory-ON Brier below the memory-OFF Brier on the same cells.

Knowledge-masking: a read the role already KNOWS is not a read — a wolf's read on a packmate and an
investigator's read on a player it has already checked are excluded, so the ledger scores inference,
not private information. 'unclear' reads make no claim and are excluded from Brier (reported as
unclear_rate instead — a lazily-unchanged or evasive read list shows up there).

Empty on pre-2026-07-09 dumps (no reads field) by construction — the ledger reports n=0, never errors.

  poetry run python evaluation/src/loop/read_ledger.py --dumps "batch_results/<run>*.jsonl"
"""

from __future__ import annotations

import argparse
import json
import os
from collections import defaultdict

from evaluation.src.loop.credit_backfill import _expand_dumps
from evaluation.src.loop.decision_scoring import THREAT_ROLES

# Confidence -> claimed probability. Coarse on purpose: the read schema exposes two confidence levels,
# so the Brier is a two-point calibration check, not a full probability elicitation.
CONF_P = {"high": 0.85, "low": 0.65}


def _known_targets(ec: dict, roles: dict) -> set[str]:
    """Players whose role the actor already KNOWS at this decision (the knowledge mask): a wolf knows
    its packmates; the investigator knows everyone it has investigated (results ride private_context)."""
    known: set[str] = set()
    actor_role = ec.get("player_role")
    if actor_role == "wolf":
        known |= {p for p, r in roles.items() if r == "wolf"}
    if actor_role == "investigator":
        pc = ec.get("private_context") or {}
        known |= {r.get("player_investigated") for r in pc.get("investigator_results") or []}
        known.discard(None)
    return known


def compute_read_ledger(dumps_glob: str) -> dict:
    """Score every stated read in the window against revealed roles, knowledge-masked. Returns
    {"channels": {<role>/<phase>/<mem on|off>: {n, brier, role_acc, faction_acc, unclear_rate}},
     "rows": [...]} — rows carry enough to slice by day/arm offline; the mem split is the
    book-vs-no-book readout."""
    rows: list[dict] = []
    for dump in _expand_dumps(dumps_glob):
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
                ec = (json.loads(cl).get("output") or {}).get("eval_case") or {}
                reads = ec.get("reads") or []
                if not reads:
                    continue
                masked = _known_targets(ec, roles)
                for r in reads:
                    target = r.get("player")
                    true_role = roles.get(target)
                    if not target or true_role is None or target in masked:
                        continue
                    suspected, conf = r.get("suspected_role"), r.get("confidence")
                    row = {
                        "game_id": g.get("game_id"), "day": ec.get("day"),
                        "phase": ec.get("action_phase"), "actor": ec.get("player_id"),
                        "actor_role": ec.get("player_role"), "memory": bool(ec.get("memory_enabled")),
                        "target": target, "true_role": true_role,
                        "suspected": suspected, "confidence": conf,
                    }
                    if suspected == "unclear":
                        row["brier"] = None
                    else:
                        p = CONF_P.get(conf, 0.65)
                        row["brier"] = round((p - (1.0 if suspected == true_role else 0.0)) ** 2, 4)
                        row["role_correct"] = suspected == true_role
                        row["faction_correct"] = (suspected in THREAT_ROLES) == (true_role in THREAT_ROLES)
                    rows.append(row)

    channels: dict = defaultdict(lambda: {"n": 0, "n_claims": 0, "brier_sum": 0.0,
                                          "role_hits": 0, "faction_hits": 0, "unclear": 0})
    for row in rows:
        ch = channels[f"{row['actor_role']}/{row['phase']}/{'on' if row['memory'] else 'off'}"]
        ch["n"] += 1
        if row["brier"] is None:
            ch["unclear"] += 1
        else:
            ch["n_claims"] += 1
            ch["brier_sum"] += row["brier"]
            ch["role_hits"] += row["role_correct"]
            ch["faction_hits"] += row["faction_correct"]
    summary = {}
    for name, c in sorted(channels.items()):
        nc = c["n_claims"]
        summary[name] = {
            "n": c["n"], "n_claims": nc,
            "brier": round(c["brier_sum"] / nc, 4) if nc else None,
            "role_acc": round(c["role_hits"] / nc, 4) if nc else None,
            "faction_acc": round(c["faction_hits"] / nc, 4) if nc else None,
            "unclear_rate": round(c["unclear"] / c["n"], 4),
        }
    return {"channels": summary, "rows": rows}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dumps", required=True)
    ap.add_argument("--out", default=None, help="write the full ledger (rows included) to this path")
    args = ap.parse_args()
    ledger = compute_read_ledger(args.dumps)
    print(f"{len(ledger['rows'])} scored reads")
    for name, s in ledger["channels"].items():
        print(f"  {name:44s} n={s['n']:4d} brier={s['brier']} role_acc={s['role_acc']} "
              f"faction_acc={s['faction_acc']} unclear={s['unclear_rate']}")
    if args.out:
        with open(args.out, "w") as f:
            json.dump(ledger, f, indent=1)
        print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
