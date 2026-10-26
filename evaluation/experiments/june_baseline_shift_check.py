"""June baseline shift: did the town's win rate really change between the two no-memory baselines?

On 2026-06-11 a fresh no-memory baseline came back with the villagers winning far less often than
the original baseline of the same setup (nine-seat, identical prompts). The record read it two ways,
both as if every game were independent: 10 fresh games against the original 30 (Fisher p = 0.0028),
and the 30 games of the new period against the original 30. But 20 deals were played in both
baselines (the same game ids, so the same deal of roles), which makes those 20 games pairs.

This runner reads the pairs and tests them as pairs, with no model call:

1. The original winner of each of the 20 shared deals, from `seed_set.json` ("recovered").
2. The winner of the same deal re-run in the new period, from `batch_results/ab_baseline_recovered.jsonl`.
3. An exact McNemar test on the town's win: of the deals whose town result changed, did more change
   from a win to a loss than the other way?
4. For context, the 10 fresh deals' winners, from `batch_results/ab_baseline.jsonl`.

A difference here says the outcomes moved; it cannot say why (model drift, or chance at this size).

    poetry run python -m evaluation.experiments.june_baseline_shift_check
"""
from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from scipy.stats import binomtest

RECORD = Path("evidence/memory_system/effectiveness/paired_ab")
ORIGINAL_SEED_SET = RECORD / "seed_set.json"
FRESH_IDS = RECORD / "baseline_fresh_ids.json"
RERUN_GAMES = Path("batch_results/ab_baseline_recovered.jsonl")
FRESH_GAMES = Path("batch_results/ab_baseline.jsonl")

TOWN = "villagers"


@dataclass
class PairedTownResult:
    """The town's result on each shared deal, before and after."""

    pairs: int
    won_both: int
    won_original_only: int
    won_rerun_only: int
    won_neither: int
    exact_mcnemar_p: float


def read_winners(path: Path) -> dict[str, str]:
    """Map each game id in a batch file to the side that won it.

    Args:
        path: a batch JSONL file, one game record per line.

    Returns:
        game id -> winning side.
    """
    winners: dict[str, str] = {}
    with path.open() as handle:
        for line in handle:
            record = json.loads(line)
            winners[record["game_id"]] = record["winner"]
    return winners


def paired_town_result(original: dict[str, str], rerun: dict[str, str]) -> PairedTownResult:
    """Count how the town's result changed on the deals played twice, and test it.

    Args:
        original: game id -> winner in the original baseline.
        rerun: game id -> winner when the same deal was re-run.

    Returns:
        The four counts and the exact McNemar p-value (two-sided).
    """
    shared_ids = [game_id for game_id in original if game_id in rerun]
    won_both = won_original_only = won_rerun_only = won_neither = 0
    for game_id in shared_ids:
        town_won_before = original[game_id] == TOWN
        town_won_after = rerun[game_id] == TOWN
        if town_won_before and town_won_after:
            won_both += 1
        elif town_won_before:
            won_original_only += 1
        elif town_won_after:
            won_rerun_only += 1
        else:
            won_neither += 1

    changed = won_original_only + won_rerun_only
    p_value = binomtest(won_original_only, changed, 0.5).pvalue if changed else 1.0
    return PairedTownResult(len(shared_ids), won_both, won_original_only, won_rerun_only, won_neither, p_value)


def main() -> None:
    seed_set = json.loads(ORIGINAL_SEED_SET.read_text())
    original = {entry["game_id"]: entry["baseline_winner"] for entry in seed_set["recovered"]}
    rerun = read_winners(RERUN_GAMES)

    result = paired_town_result(original, rerun)
    shared_ids = [game_id for game_id in original if game_id in rerun]
    print(f"Shared deals: {result.pairs}")
    print(f"  original winners: {dict(Counter(original[g] for g in shared_ids))}")
    print(f"  re-run winners:   {dict(Counter(rerun[g] for g in shared_ids))}")
    print(f"  town won both {result.won_both}, original only {result.won_original_only}, "
          f"re-run only {result.won_rerun_only}, neither {result.won_neither}")
    print(f"  exact McNemar p = {result.exact_mcnemar_p:.3f}")

    fresh_ids = json.loads(FRESH_IDS.read_text())["game_ids"]
    fresh = read_winners(FRESH_GAMES)
    print(f"Fresh deals (10): {dict(Counter(fresh[g] for g in fresh_ids))}")


if __name__ == "__main__":
    main()
