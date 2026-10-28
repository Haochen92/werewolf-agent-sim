"""Re-score the two abstain lessons against memory-off play on the same game day (no model calls).

Credit compared a lesson's followed decisions with memory-off decisions by the same role and phase, pooled
over every day. Both abstain lessons on the curating page fire early in the game, so this check asks how much
of each score came from comparing early-day decisions with an all-day average. It reads the nine-seat
records with the nine-seat grader (``credit_backfill``), under the grading as run then (abstention neutral)
and the corrected one (abstention on a day with no lynch graded bad).

Run: poetry run python evaluation/experiments/credit_day_matched_check.py
Output: evidence/credit/day_matched_baseline/results.json
"""

from __future__ import annotations

import json
import os
import statistics as st
from collections import defaultdict
from pathlib import Path

from evaluation.src.loop import credit_backfill as cb

OUT = Path("evidence/credit/day_matched_baseline/results.json")
SHRINK_K = 5
CASES = {
    "june_villager_abstain": {
        "key": "bc7b8a88-356e-4a89-a139-ec548f9bfe7a",
        "channel": "villager/day_vote",
        "on": cb.DEFAULT_DUMPS,
        "off": cb.DEFAULT_DUMPS,
    },
    "july_vigilante_abstain": {
        "key": "90324c3c-c8a6-4d00-a1c2-ee1312034c74",
        "channel": "vigilante/day_vote",
        "on": " ".join(f"batch_results/v7_compound_town5/gen{g}_on.jsonl" for g in (1, 2, 3, 4)),
        "off": " ".join(f"batch_results/v7_compound_town5/gen{g}_off.jsonl" for g in (1, 2, 3, 4)),
    },
}
RULES = {"as_run": "neutral", "corrected": "deadlock_negative"}


def main() -> None:
    results = {}
    for name, case in CASES.items():
        results[name] = {rule: score_case(case, abstain_rule) for rule, abstain_rule in RULES.items()}
        results[name]["memory_off_abstain_rate_by_day"] = abstain_rate_by_day(case)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(results, indent=1))
    for name, r in results.items():
        for rule in RULES:
            s = r[rule]
            print(f"{name:24s} {rule:9s} follows {s['follows']:3d} lesson {s['lesson_mean']:+.2f} | "
                  f"all days {s['base_all_days']:+.2f} -> {s['score_all_days']:+.2f} | "
                  f"same day {s['base_same_day']:+.2f} -> {s['score_same_day']:+.2f}")
    print(f"wrote {OUT}")


def score_case(case: dict, abstain_rule: str) -> dict:
    """The lesson's score against the pooled memory-off base and against the base of its own follow days.

    Args:
        case: the lesson key, its channel, and the memory-on and memory-off record globs.
        abstain_rule: the nine-seat grader's town-abstain rule.

    Returns:
        Follow count and days, the lesson's mean grade, both bases, both shrunk scores, and the
        memory-off base per day.
    """
    off_by_day = defaultdict(list)
    for ec, grade in graded_decisions(case["off"], abstain_rule):
        if not ec.get("memory_enabled") and channel(ec) == case["channel"]:
            off_by_day[ec.get("day")].append(grade)
    follows = []
    for ec, grade in graded_decisions(case["on"], abstain_rule):
        if ec.get("memory_enabled") and case["key"] in followed_keys(ec):
            follows.append((ec.get("day"), grade))

    n = len(follows)
    lesson_mean = st.mean(g for _, g in follows)
    base_all = st.mean(g for gs in off_by_day.values() for g in gs)
    base_same_day = st.mean(st.mean(off_by_day[day]) for day, _ in follows)
    shrink = n / (n + SHRINK_K)
    return {
        "follows": n,
        "follow_days": sorted(day for day, _ in follows),
        "lesson_mean": round(lesson_mean, 3),
        "base_all_days": round(base_all, 3),
        "score_all_days": round((lesson_mean - base_all) * shrink, 3),
        "base_same_day": round(base_same_day, 3),
        "score_same_day": round((lesson_mean - base_same_day) * shrink, 3),
        "memory_off_base_by_day": {d: [round(st.mean(gs), 3), len(gs)] for d, gs in sorted(off_by_day.items())},
    }


def abstain_rate_by_day(case: dict) -> dict:
    """How often memory-off players of the lesson's role abstained, by day: did the lesson change the move?"""
    role = case["channel"].split("/")[0]
    total, abstained = defaultdict(int), defaultdict(int)
    for ec in eval_cases(case["off"]):
        if ec.get("memory_enabled") or ec.get("player_role") != role or ec.get("action_phase") != "day_vote":
            continue
        votee = (ec.get("agent_vote") or {}).get("votee")
        total[ec.get("day")] += 1
        abstained[ec.get("day")] += not votee or votee == "abstain"
    return {d: [round(abstained[d] / total[d], 3), total[d]] for d in sorted(total)}


def graded_decisions(dumps: str, abstain_rule: str):
    """(eval case, grade value) for every graded decision in the records, nine-seat rules."""
    for game in games(dumps):
        roles = game["roles"]
        blend = {d.get("day"): cb._majority_vote(d) for d in game.get("day_resolutions", [])}
        nights = {n.get("day"): n for n in game.get("night_resolutions", [])}
        days = {d.get("day"): d for d in game.get("day_resolutions", [])}
        for ec in eval_cases_of(game):
            verdict = cb._decision_credit(ec, roles, blend, nights, abstain_rule=abstain_rule, day_res_by_day=days)
            if verdict in cb.VERDICT_VALUE:
                yield ec, cb.VERDICT_VALUE[verdict]


def eval_cases(dumps: str):
    for game in games(dumps):
        yield from eval_cases_of(game)


def games(dumps: str):
    for path in cb._expand_dumps(dumps):
        for line in open(path):
            if not line.strip():
                continue
            game = json.loads(line)
            if game.get("roles") and game.get("eval_cases_path") and os.path.exists(game["eval_cases_path"]):
                yield game


def eval_cases_of(game: dict):
    for line in open(game["eval_cases_path"]):
        if not line.strip():
            continue
        env = json.loads(line)
        if env.get("kind") == "agent_action_eval" and (env.get("output") or {}).get("eval_case"):
            yield env["output"]["eval_case"]


def channel(ec: dict) -> str:
    return f"{ec.get('player_role')}/{ec.get('action_phase')}"


def followed_keys(ec: dict) -> set[str]:
    index_to_key = ec.get("strategy_index_to_key") or {}
    return {index_to_key.get(str(sv.get("strategy_index"))) for sv in ec.get("strategy_verdicts") or []
            if sv.get("verdict") == "follow"}


if __name__ == "__main__":
    main()
