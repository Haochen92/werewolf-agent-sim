"""Override validity on the ten-seat game: does an agent's "override" verdict pick out the bad lessons?

The June check (`evaluation/src/instrument_validation/credit/g3a_verdict_validity.py`, nine-seat) asked
whether lessons could be decayed on the agent's own verdict. It failed because agents almost never
overrode (town day votes: 3 overrides against 334 follows). This runner asks the same two questions of
ten-seat games, with the live credit rules (`Agents/memory/consolidation/credit_rules.py`):

1. How often do agents follow, override, or mark a lesson not relevant, on turns shown lessons?
2. Do decisions where the agent overrode a lesson turn out better than decisions where it followed one?
   Each decision (one player, day, phase and night scope) is graded once: +1 good, 0 neutral, -1 bad.

No model call. First run: the 20 Claude Haiku 5.5 memory-on demo games of 2026-10-14
(`batch_results/v8_demo/`, gitignored). Record: `evidence/evaluation/loop/report.md` (credit validators).

    poetry run python -m evaluation.experiments.v8_override_validity \
        --games "batch_results/v8_demo/games_*.jsonl" \
        --out evidence/memory_system/v8/data/override_validity/summary.json
"""
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path

from Agents.memory.consolidation.credit_rules import (
    _iter_game_records,
    decision_channel,
    decision_credit,
    decision_scope,
    iter_eval_cases,
)
from Agents.memory.consolidation.grading import GameView

GRADE_VALUE = {"positive": 1, "neutral": 0, "negative": -1}


@dataclass
class GroupGrades:
    """The grades of the decisions in one group (for example, "follow only" decisions of one channel)."""

    values: list[int] = field(default_factory=list)

    @property
    def mean(self) -> float | None:
        if not self.values:
            return None
        return sum(self.values) / len(self.values)


def lesson_verdicts_shown(eval_case: dict) -> list[str]:
    """The agent's verdict words on the lessons this turn was actually shown.

    Args:
        eval_case: one agent-action eval case, with ``strategy_index_to_key`` (the lessons shown,
            keyed by their 1-based position) and ``strategy_verdicts`` (the agent's verdict per position).

    Returns:
        The verdict words ("follow", "override", "not_relevant") for shown lessons only; an empty list
        when the turn was shown no lessons. Verdicts on positions that were not shown are dropped: on
        2026-10-14 Haiku copied the example's "follow" onto turns shown nothing.
    """
    shown_positions = set()
    for position in eval_case.get("strategy_index_to_key") or {}:
        shown_positions.add(str(position))
    verdict_words = []
    for verdict in eval_case.get("strategy_verdicts") or []:
        if str(verdict.get("strategy_index")) in shown_positions:
            verdict_words.append(verdict["verdict"])
    return verdict_words


def decision_group(verdict_words: list[str]) -> str | None:
    """The group a decision falls in by its verdicts.

    Args:
        verdict_words: the verdicts on the lessons the turn was shown.

    Returns:
        "follow_only", "override_only" or "mixed"; None when the agent neither followed nor overrode any
        lesson (all marked not relevant), so the decision says nothing about overriding.
    """
    followed = "follow" in verdict_words
    overrode = "override" in verdict_words
    if followed and overrode:
        return "mixed"
    if followed:
        return "follow_only"
    if overrode:
        return "override_only"
    return None


def run(games_glob: str) -> dict:
    """Count the verdicts and compare the grades of override and follow decisions.

    Args:
        games_glob: a glob of batch-run game files whose eval cases hold memory-on decisions,
            e.g. "batch_results/v8_demo/games_*.jsonl".

    Returns:
        A summary dict: verdict counts per phase, the mean grade per group, the per-channel comparison,
        the within-channel gap (override minus follow, weighted by the smaller group's size), and the
        count of decisions the rules do not grade, per phase.
    """
    verdict_counts_by_phase: dict[str, Counter] = defaultdict(Counter)
    grades_by_group: dict[str, GroupGrades] = defaultdict(GroupGrades)
    grades_by_channel: dict[str, dict[str, GroupGrades]] = defaultdict(lambda: defaultdict(GroupGrades))
    ungraded_by_phase: Counter = Counter()
    game_count = 0

    for game_record in _iter_game_records(games_glob):
        game_count += 1
        game_view = GameView(game_record)
        graded_scopes = set()
        for eval_case in iter_eval_cases(game_record):
            if not eval_case.get("memory_enabled"):
                continue
            verdict_words = lesson_verdicts_shown(eval_case)
            phase = eval_case.get("action_phase")
            verdict_counts_by_phase[phase].update(verdict_words)

            group = decision_group(verdict_words)
            scope = decision_scope(eval_case)
            if group is None or scope in graded_scopes:
                continue
            grade = decision_credit(eval_case, game_view)
            if grade not in GRADE_VALUE:
                ungraded_by_phase[phase] += 1
                continue
            graded_scopes.add(scope)
            grades_by_group[group].values.append(GRADE_VALUE[grade])
            grades_by_channel[decision_channel(eval_case)][group].values.append(GRADE_VALUE[grade])

    channel_rows = []
    weighted_gap_sum = 0.0
    weight_sum = 0
    for channel in sorted(grades_by_channel):
        follow_grades = grades_by_channel[channel]["follow_only"]
        override_grades = grades_by_channel[channel]["override_only"]
        if not follow_grades.values or not override_grades.values:
            continue
        gap = override_grades.mean - follow_grades.mean
        weight = min(len(follow_grades.values), len(override_grades.values))
        weighted_gap_sum += gap * weight
        weight_sum += weight
        channel_rows.append({
            "channel": channel,
            "follow_only_n": len(follow_grades.values),
            "follow_only_mean": round(follow_grades.mean, 3),
            "override_only_n": len(override_grades.values),
            "override_only_mean": round(override_grades.mean, 3),
        })

    group_rows = {}
    for group_name, group_grades in sorted(grades_by_group.items()):
        group_rows[group_name] = {"n": len(group_grades.values), "mean": round(group_grades.mean, 3)}

    verdict_rows = {}
    for phase, counts in sorted(verdict_counts_by_phase.items()):
        verdict_rows[phase] = dict(counts)

    within_channel_gap = round(weighted_gap_sum / weight_sum, 3) if weight_sum else None
    return {
        "games_glob": games_glob,
        "games": game_count,
        "verdict_counts_by_phase": verdict_rows,
        "grade_by_group": group_rows,
        "channels": channel_rows,
        "within_channel_gap_override_minus_follow": within_channel_gap,
        "within_channel_weight": weight_sum,
        "ungraded_decisions_by_phase": dict(ungraded_by_phase),
    }


def main() -> None:
    """Run the check and write the summary JSON."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--games", required=True, help="glob of batch-run game files")
    parser.add_argument("--out", required=True, help="where to write summary.json")
    args = parser.parse_args()

    summary = run(args.games)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary["grade_by_group"], indent=2))
    print("within-channel gap (override - follow):", summary["within_channel_gap_override_minus_follow"])
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
