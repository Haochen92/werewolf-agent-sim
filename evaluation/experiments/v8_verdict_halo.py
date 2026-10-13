"""Does the extraction judge's verdict follow the decision or the side's win? Before and after de-halo
(2026-10-13).

Record: evidence/memory_system/v8/decisions.md §13; the test the case study
evidence/case_studies/observation_extraction.md named. Each night or vote observation's `net_verdict`
(positive +1, negative −1, mixed or unclear 0; as extracted, and as the de-halo pass left it) is fitted
against the deterministic grade of that role's decisions in that game (grading.py, the mean over its
scopes) and whether its side won. An observation does not say which decision it describes, so the grade
is per role per game. No model calls.

  poetry run python evaluation/experiments/v8_verdict_halo.py
"""

from __future__ import annotations

import collections
import glob
import json
from pathlib import Path

import numpy as np

from Agents.memory.consolidation.credit_rules import (
    _iter_game_records,
    decision_credit,
    decision_scope,
    iter_eval_cases,
)
from Agents.memory.consolidation.grading import GameView, side

MAIN = Path(__file__).resolve().parents[2]
RECORDS = ["batch_results/v8_seed_*/games/*.jsonl", "batch_results/v8_gate_haiku/games_*.jsonl",
           "batch_results/v8_luna_memory/run2/game_*.jsonl"]
DEHALO = "batch_results/extraction_runs/*/dehalo.jsonl"
OUT = MAIN / "evidence/memory_system/v8/data/halo"
VALUE = {"positive": 1, "negative": -1, "mixed": 0, "unclear": 0}


def side_won(g: dict, role: str) -> bool:
    s, winner = side(role), g.get("winner")
    if s == "neutral":
        return str(g.get("neutral_result") or "").startswith("won")
    return winner == {"town": "villagers", "wolves": "wolves"}.get(s, role)


def role_grades(g: dict) -> dict[tuple, float]:
    """(role, phase) -> mean deterministic grade of its decisions, one per scope."""
    view, seen, acc = GameView(g), set(), collections.defaultdict(list)
    for ec in iter_eval_cases(g):
        v = decision_credit(ec, view)
        if v not in VALUE or decision_scope(ec) in seen:
            continue
        seen.add(decision_scope(ec))
        acc[(ec["player_role"], ec["action_phase"])].append(VALUE[v])
    return {k: float(np.mean(vs)) for k, vs in acc.items()}


def main() -> None:
    games = {g["game_id"]: g for pattern in RECORDS for g in _iter_game_records(str(MAIN / pattern))}
    grades = {gid: role_grades(g) for gid, g in games.items()}
    rows = []
    for path in glob.glob(str(MAIN / DEHALO)):
        for line in open(path):
            r = json.loads(line)
            g = games.get(r["game_id"])
            if g is None:
                continue
            for j in r["output"]["dehalo"]["judgments"]:
                grade = grades[r["game_id"]].get((j["perspective"], j["action_phase"]))
                if j["action_phase"] in ("night_action", "day_vote") and grade is not None:
                    rows.append({"game_id": r["game_id"], "role": j["perspective"], "phase": j["action_phase"],
                                 "grade": grade, "side_won": side_won(g, j["perspective"]),
                                 "original": j["original_verdict"], "revised": j["revised_verdict"]})
    X = np.c_[np.ones(len(rows)), [r["grade"] for r in rows], [r["side_won"] for r in rows]]
    summary = {"games": len({r["game_id"] for r in rows}), "observations": len(rows)}
    for name in ("original", "revised"):
        b, *_ = np.linalg.lstsq(X, [VALUE.get(r[name], 0) for r in rows], rcond=None)
        mix = {}
        for won in (True, False):
            c = collections.Counter(r[name] for r in rows if r["side_won"] == won)
            n = sum(c.values())
            mix["won" if won else "lost"] = {k: round(c[k] / n, 3) for k in VALUE} | {"n": n}
        summary[name] = {"intercept": round(b[0], 3), "grade": round(b[1], 3), "side_won": round(b[2], 3),
                         "mix": mix}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "rows.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
