"""How complete and how fast the deduction engine's candidate-role solver is, on random legal games.

Record: evidence/reasoning_failures/report.md (§3, §5) and the output folder
evidence/reasoning_failures/data/solver_census/. No model call.

The solver (Agents/deduction/candidates/solver.py) is sound by construction and propagates without
search, so it may in principle keep a role a full search would rule out. This measures how often
that happens: for every point a seat reasons from in `--games` random games (the generator and the
brute-force oracle the tests use, tests/factories/), the public's view and every living seat's view
are solved, and each player's remaining roles are compared with the roles some deal the oracle allows
gives them. A role the solver keeps and no allowed deal gives is a miss. The oracle builds its own
conditions from what the view knows, so a fact neither encodes is invisible here: zero misses means
no gap against the oracle, not completeness. Conditional runs (a claim added as a premise) are not
covered.

Timings are wall-clock on the machine that ran it, for scale only: every seat's candidates (its
constraints built from its view, then solved), and whole turns (both blocks, every level) on
acceptance case 2's frozen vote turn.

  poetry run python evaluation/experiments/deduction_solver_census.py --games 150
"""

from __future__ import annotations

import argparse
import json
import platform
import random
import statistics
import time
from pathlib import Path

OUT = Path("evidence/reasoning_failures/data/solver_census")
SEED = 20261018
AC2_ID = "9b827b695a61ece9"


def _ms(start: float) -> float:
    return (time.perf_counter() - start) * 1000


def completeness(games: int, seed: int) -> tuple[dict, list[float]]:
    """Misses against the oracle over every view, and the timings of each seat's candidates."""
    from Agents.deduction import seat_view_from_payload
    from Agents.deduction.candidates import public_candidates, seat_candidates
    from tests.engine.deduction.test_candidates import _continuing_snapshots
    from tests.factories.role_assignments import oracle_of

    counts = {"public_views": 0, "seat_views": 0, "views_with_a_miss": 0, "roles_missed": 0, "unsolved_views": 0}
    examples, timings = [], []
    for game, snapshot in _continuing_snapshots(random.Random(seed), games):
        views = [(None, None)] + [(player, seat_view_from_payload(game.payload_of(player, snapshot)))
                                  for player in snapshot.living]
        for player, view in views:
            start = time.perf_counter()
            candidates = public_candidates(snapshot) if view is None else seat_candidates(view)
            if view is not None:
                timings.append(_ms(start))
            counts["public_views" if view is None else "seat_views"] += 1
            if candidates is None:
                counts["unsolved_views"] += 1
                continue
            support, _ = oracle_of(snapshot, view).support()
            missed = {p: sorted(set(candidates.roles[p]) - support[p]) for p in support
                      if set(candidates.roles[p]) - support[p]}
            if missed:
                counts["views_with_a_miss"] += 1
                counts["roles_missed"] += sum(len(roles) for roles in missed.values())
                if len(examples) < 5:
                    examples.append({"seat": player, "missed": missed})
    return {**counts, "examples": examples}, timings


def whole_turns(repeats: int) -> list[float]:
    """Both blocks of AC2's frozen vote turn, built `repeats` times."""
    from Agents.deduction import deduction_blocks, fold_own_lines, own_result_lines, seat_view_from_payload
    from tests.engine.deduction.test_render import _frozen

    payload = _frozen(AC2_ID)
    view = seat_view_from_payload(payload)
    lines = fold_own_lines(view.night_records, own_result_lines(view))
    timings = []
    for _ in range(repeats):
        start = time.perf_counter()
        deduction_blocks(view, lines, payload["day_channel"], payload["current_day"], vote=True)
        timings.append(_ms(start))
    return timings


def _summary(timings: list[float]) -> dict:
    ordered = sorted(timings)
    return {"n": len(ordered), "median_ms": round(statistics.median(ordered), 3),
            "p99_ms": round(ordered[int(len(ordered) * 0.99)], 3), "max_ms": round(ordered[-1], 3)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--games", type=int, default=150)
    parser.add_argument("--seed", type=int, default=SEED)
    args = parser.parse_args()

    from Agents.run_fingerprint import git_revision

    misses, seat_solves = completeness(args.games, args.seed)
    summary = {"pointer": {"code": "evaluation/experiments/deduction_solver_census.py", **git_revision()},
               "games": args.games, "seed": args.seed, "completeness": misses,
               "timing": {"machine": f"{platform.machine()}, {platform.processor() or platform.system()}",
                          "seat_candidates": _summary(seat_solves), "ac2_whole_turn": _summary(whole_turns(30))}}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "census.json").write_text(json.dumps(summary, indent=1) + "\n")
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
