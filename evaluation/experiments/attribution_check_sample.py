"""Sample ten-seat "followed" reports for the attribution check (does the decision do what the lesson says?).

The July check read 15 nine-seat reports (13 matched; the one-sided 95% bound on the mismatch rate was about
36%). This draws a larger, stratified sample from the ten-seat demo games, the reports credit actually
counts: memory-on, the lesson mapped to a store key, and for discussion only spoken turns
(``credit._spoke``). Readers judge each case; the verdicts go beside the cases.

Run: poetry run python evaluation/experiments/attribution_check_sample.py
"""

from __future__ import annotations

import argparse
import ast
import glob
import json
import random
from pathlib import Path

PER_PHASE = {"day_discussion": 35, "day_vote": 30, "night_action": 35}
"""Votes are oversampled (135 of 1,154 reports) because the abstain cases are vote lessons."""


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--games", default="batch_results/v8_demo/games_*.jsonl")
    ap.add_argument("--out", type=Path, default=Path("evidence/credit/attribution_check_ten_seat"))
    ap.add_argument("--batches", type=int, default=5)
    ap.add_argument("--seed", type=int, default=20261028)
    args = ap.parse_args()

    pool = collect_follow_reports(args.games)
    rng = random.Random(args.seed)
    cases = []
    for phase, n in PER_PHASE.items():
        cases += rng.sample([c for c in pool if c["phase"] == phase], n)
    rng.shuffle(cases)
    for i, c in enumerate(cases):
        c["case_id"] = f"c{i:03d}"

    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "cases.json").write_text(json.dumps(cases, indent=1))
    size = -(-len(cases) // args.batches)
    for b in range(args.batches):
        (args.out / f"batch_{b}.json").write_text(json.dumps(cases[b * size:(b + 1) * size], indent=1))
    counts = {p: sum(c["phase"] == p for c in pool) for p in PER_PHASE}
    print(f"pool {len(pool)} {counts}; sampled {len(cases)} into {args.batches} batches at {args.out}")


def collect_follow_reports(games_glob: str) -> list[dict]:
    """Every credit-countable follow report in the games, one row per (decision, followed lesson).

    Args:
        games_glob: glob of batch-run game record files.

    Returns:
        Rows holding the lesson text, the player's stated reason and the decision taken.
    """
    rows = []
    for path in sorted(glob.glob(games_glob)):
        for line in open(path):
            game = json.loads(line)
            for ec in eval_cases(game["eval_cases_path"]):
                rows += follow_rows(game["game_id"], ec)
    return rows


def eval_cases(path: str):
    for line in open(path):
        env = json.loads(line)
        if env.get("kind") == "agent_action_eval":
            yield env["output"]["eval_case"]


def follow_rows(game_id: str, ec: dict) -> list[dict]:
    """The case's followed, store-keyed lessons; none for a memory-off turn or a passed speaking turn."""
    if not ec.get("memory_enabled"):
        return []
    phase = ec["action_phase"]
    message = (ec.get("agent_message") or {}).get("message") or ""
    if phase == "day_discussion" and not message.strip():
        return []
    index_to_key = ec.get("strategy_index_to_key") or {}
    lessons = {r["key"]: r for r in ec.get("retrieved_strategy_points") or []}
    rows = []
    for sv in ec.get("strategy_verdicts") or []:
        key = index_to_key.get(str(sv.get("strategy_index")))
        if sv.get("verdict") != "follow" or key not in lessons:
            continue
        rows.append({
            "game_id": game_id, "player": ec.get("player_id"), "role": ec.get("player_role"),
            "day": ec.get("day"), "phase": phase, "lesson_key": key,
            "lesson_situation": lesson_field(lessons[key].get("strategy_point"), "situation"),
            "lesson_action": lesson_field(lessons[key].get("strategy_point"), "action"),
            "matched_situation": lessons[key].get("matched_situation"),
            "stated_reason": sv.get("why"),
            "decision": decision_text(ec, phase, message),
            "recent_discussion": recent_discussion(ec),
        })
    return rows


def lesson_field(strategy_point, field: str) -> str:
    """One field of the stored lesson ("situation" = its when, "action" = its advice). The record
    stores the lesson as a dict's printed form. Not the case's ``matched_situation``: that is the live
    game's own situation the lookup searched with, which names this game's players."""
    if isinstance(strategy_point, str):
        try:
            strategy_point = ast.literal_eval(strategy_point)
        except (ValueError, SyntaxError):
            return strategy_point if field == "action" else ""
    return (strategy_point or {}).get(field, "")


def decision_text(ec: dict, phase: str, message: str) -> dict:
    if phase == "day_vote":
        return {"vote": (ec.get("agent_vote") or {}).get("votee")}
    if phase == "night_action":
        act = ec.get("agent_night_action") or {}
        return {k: act.get(k) for k in ("kind", "target", "role_named", "via")}
    return {"spoke": message}


def recent_discussion(ec: dict, last: int = 8) -> list[str]:
    """The last public lines the player saw, so a reader can tell what 'the accuser' or 'the claim' refers to."""
    lines = ec.get("visible_discussion") or []
    out = []
    for m in lines[-last:]:
        if isinstance(m, dict):
            out.append(f"{m.get('player')}: {m.get('message', '')}"[:400])
        else:
            out.append(str(m)[:400])
    return out


if __name__ == "__main__":
    main()
