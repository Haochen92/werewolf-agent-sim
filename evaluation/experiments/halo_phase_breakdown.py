"""Outcome halo by phase: how often the extractor's verdict matches the rule-based grade, per phase and
side, before and after de-halo (2026-10-28).

Record: evidence/extraction/observation_quality/report.md §4. Reads the per-observation rows that
`evaluation/experiments/v8_verdict_halo.py --grain observation` wrote (one row per observation: its
phase, the rule-based grade of its decision, whether its side won, its verdict as extracted and after
de-halo). Counting only, no model calls.

  poetry run python evaluation/experiments/halo_phase_breakdown.py
"""

from __future__ import annotations

import json
from pathlib import Path

MAIN = Path(__file__).resolve().parents[2]
ROWS = MAIN / "evidence/memory_system/v8/data/halo/observation_rows.jsonl"

PHASES = [("day_discussion", "Discussion"), ("day_vote", "Vote"), ("night_action", "Night"),
          (None, "All phases")]
SIDES = [(False, "losing"), (True, "winning")]
GRADES = [(1, "Good moves"), (-1, "Bad moves")]
VERDICTS = ["positive", "negative"]


def main() -> None:
    """Print one markdown table: a row per phase and side; for good and for bad moves, the count and
    the share called positive and called negative, as "before de-halo → after"."""
    rows = load_rows(ROWS)
    header = ["Phase", "Side"]
    for _, grade_name in GRADES:
        header += [f"{grade_name} (n)"] + [f"called {v}" for v in VERDICTS]
    print("| " + " | ".join(header) + " |")
    print("|" + "---|" * len(header))
    for phase, phase_name in PHASES:
        for won, side_name in SIDES:
            line = [phase_name, side_name]
            for grade, _ in GRADES:
                cell = select(rows, phase=phase, side_won=won, grade=grade)
                line.append(str(len(cell)))
                for verdict in VERDICTS:
                    line.append(f"{share(cell, 'original', verdict)} → {share(cell, 'revised', verdict)}")
            print("| " + " | ".join(line) + " |")


def load_rows(path: Path) -> list[dict]:
    """Read the observation rows.

    Args:
        path: the JSONL file of observation rows.

    Returns:
        One dict per observation, with keys phase, grade (+1 good, -1 bad), side_won, original and
        revised (the verdict before and after de-halo).
    """
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def select(rows: list[dict], phase: str | None, side_won: bool, grade: int) -> list[dict]:
    """Keep the observations in one cell of the table.

    Args:
        rows: all observation rows.
        phase: the phase to keep, or None for every phase.
        side_won: True for the winning side, False for the losing side.
        grade: +1 for rule-graded good moves, -1 for bad ones.

    Returns:
        The matching rows.
    """
    return [r for r in rows
            if (phase is None or r["phase"] == phase) and r["side_won"] == side_won and r["grade"] == grade]


def share(rows: list[dict], field: str, verdict: str) -> str:
    """The percentage of rows whose verdict field equals the given verdict.

    Args:
        rows: the rows of one table cell.
        field: "original" (as extracted) or "revised" (after de-halo).
        verdict: the verdict word to count.

    Returns:
        A whole-number percentage such as "37%", or "n/a" when the cell is empty.
    """
    if not rows:
        return "n/a"
    hits = sum(1 for r in rows if r[field] == verdict)
    return f"{round(100 * hits / len(rows))}%"


if __name__ == "__main__":
    main()
