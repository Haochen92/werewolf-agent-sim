"""v7 endpoint, board by board: rebuild the paired result from the per-game records.

The July 2026 v7 test played 30 boards twice, once with the loop's final memory and once without.
The record reports the main result board by board (the town's decision score 0.147 lower with
memory, lower on 19 of 30 boards, p about 0.06), but the committed `endpoint_result.json` holds
only the pooled per-decision scores, and no record names the test behind the p-value. This runner
recomputes the per-board scores from the per-game records, with no model call:

1. Each game's town decisions are scored with `evaluation.src.loop.measure.game_score`, the
   pre-registered scorer. Its defaults are the July grading (a town abstain stays neutral; the
   later abstain fix is opt-in), so the scores are the ones the July run produced.
2. As a check, the games' decisions are pooled and compared with the committed
   `endpoint_result.json` (town 0.039 with memory over 458 decisions, 0.247 without over 438).
3. The boards are paired by game id, and the gap (with memory minus without) is tested three
   ways: a paired t-test, the Wilcoxon signed-rank test and a sign test.

The per-game records are git-ignored (`batch_results/v7_endpoint_ab/`); the output is committed
beside the run's other files.

    poetry run python -m evaluation.experiments.v7_endpoint_paired \
        --out evidence/memory_system/v7/execution_plan/data/v7_endpoint_ab/paired_boards.json
"""
from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path

from scipy import stats

from evaluation.src.core.stats import wilcoxon_paired
from evaluation.src.loop.measure import game_score

RUN_DIR = Path("batch_results/v7_endpoint_ab")
FACTION = "town"


@dataclass
class BoardScore:
    """One board's town score in each arm (mean decision value, and the decisions behind it)."""

    game_id: str
    with_memory: float
    with_memory_decisions: int
    without_memory: float
    without_memory_decisions: int

    @property
    def gap(self) -> float:
        return self.with_memory - self.without_memory


@dataclass
class PooledCheck:
    """The games' decisions pooled per arm, to compare with the committed `endpoint_result.json`."""

    with_memory: float
    with_memory_decisions: int
    without_memory: float
    without_memory_decisions: int
    matches_committed: bool


def load_games(path: Path) -> dict[str, dict]:
    """Read one arm's game records, keyed by game id.

    Args:
        path: a jsonl file with one whole-game record per line.

    Returns:
        game id -> record.
    """
    games: dict[str, dict] = {}
    for line in path.read_text().splitlines():
        if line.strip():
            record = json.loads(line)
            games[record["game_id"]] = record
    return games


def town_sum_and_count(record: dict, arm: str) -> tuple[float, int]:
    """Score one game's town decisions with the pre-registered scorer.

    Args:
        record: a whole-game record.
        arm: "on" (count only decisions that used memory) or "off".

    Returns:
        (sum of decision values, number of decisions) for the town.
    """
    sums, counts = game_score(record, arm)
    return sums.get(FACTION, 0.0), counts.get(FACTION, 0)


def score_boards(on_games: dict[str, dict], off_games: dict[str, dict]) -> tuple[list[BoardScore], PooledCheck]:
    """Score every board in both arms, and pool the decisions for the check.

    Args:
        on_games: game id -> record, with memory.
        off_games: game id -> record, without memory.

    Returns:
        the per-board scores (boards with no town decision in either arm are left out) and the pooled check.
    """
    committed = json.loads((RUN_DIR / "endpoint_result.json").read_text())["score"]
    boards: list[BoardScore] = []
    on_total, on_n, off_total, off_n = 0.0, 0, 0.0, 0
    for game_id in sorted(on_games, key=lambda gid: int(gid.rsplit("_g", 1)[1])):
        on_sum, on_count = town_sum_and_count(on_games[game_id], "on")
        off_sum, off_count = town_sum_and_count(off_games[game_id], "off")
        on_total, on_n = on_total + on_sum, on_n + on_count
        off_total, off_n = off_total + off_sum, off_n + off_count
        if on_count == 0 or off_count == 0:
            continue
        boards.append(BoardScore(game_id, on_sum / on_count, on_count, off_sum / off_count, off_count))
    pooled_on = round(on_total / on_n, 3)
    pooled_off = round(off_total / off_n, 3)
    matches = (pooled_on == committed["on/town"] and on_n == committed["n_on/town"]
               and pooled_off == committed["off/town"] and off_n == committed["n_off/town"])
    return boards, PooledCheck(pooled_on, on_n, pooled_off, off_n, matches)


def paired_tests(boards: list[BoardScore]) -> dict:
    """Test the per-board gap three ways.

    Args:
        boards: the per-board scores.

    Returns:
        the mean gap, the board counts by direction, and each test's p-value (two-sided).
    """
    with_memory = [board.with_memory for board in boards]
    without_memory = [board.without_memory for board in boards]
    gaps = [board.gap for board in boards]
    worse = sum(1 for gap in gaps if gap < 0)
    better = sum(1 for gap in gaps if gap > 0)
    _, wilcoxon_p = wilcoxon_paired(without_memory, with_memory)
    return {
        "boards": len(boards),
        "mean_gap": round(sum(gaps) / len(gaps), 3),
        "boards_worse_with_memory": worse,
        "boards_better_with_memory": better,
        "boards_tied": len(gaps) - worse - better,
        "p_paired_t": round(float(stats.ttest_rel(with_memory, without_memory).pvalue), 3),
        "p_wilcoxon": round(float(wilcoxon_p), 3),
        "p_sign_test": round(float(stats.binomtest(worse, worse + better).pvalue), 3),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Rebuild the v7 endpoint's paired result.")
    parser.add_argument("--out", type=Path, required=True, help="where to write the JSON summary")
    args = parser.parse_args()

    on_games = load_games(RUN_DIR / "endpoint_on.jsonl")
    off_games = load_games(RUN_DIR / "endpoint_off.jsonl")
    boards, pooled = score_boards(on_games, off_games)
    summary = {
        "pooled_check": asdict(pooled),
        "paired": paired_tests(boards),
        "per_board": [asdict(board) | {"gap": round(board.gap, 3)} for board in boards],
    }
    args.out.write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps({"pooled_check": summary["pooled_check"], "paired": summary["paired"]}, indent=2))


if __name__ == "__main__":
    main()
