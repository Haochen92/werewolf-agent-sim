"""Ten-seat win check: which play-quality scores go with their side winning on the ten-seat game?

The nine-seat check (`evaluation/src/instrument_validation/proxies/proxy_win_monotonicity.py`, June
2026, and the July audit on 180 games) correlated each score with its own side's win. None of that
carries over to the ten-seat game, whose cast, roles and win conditions differ, so no score is named
in `VALIDATED_ON_TEN_SEAT_METRICS` (`Agents/compute_metrics.py`). This runner asks the same question
of the ten-seat games already on disk, with no model call:

1. Every game's metrics are recomputed from its record (`compute_game_metrics`), because a record
   written before the 2026-10-11 port stores the old nine-seat zeros.
2. Each score is correlated with its side's win three ways: over all games; within batch (each
   batch's own mean taken out of both the score and the win, so a batch that both played differently
   and won more cannot fake a link); and over the memory-off games alone (memory can raise a score
   and the win together).

Directions: a score the June check also tested carries June's expected direction; a score new to
the ten-seat game carries none, so its result is exploratory.

    poetry run python -m evaluation.experiments.ten_seat_win_check \
        --out evidence/evaluation/metrics/data/ten_seat_win_check/summary.json
"""
from __future__ import annotations

import argparse
import glob
import gzip
import json
import math
from dataclasses import dataclass, field
from pathlib import Path

from Agents.compute_metrics import compute_game_metrics
from Agents.schemas.game_events import DayChannel
from Agents.schemas.metrics import Metrics
from evaluation.src.core.stats import pearson, point_biserial

# Where the ten-seat games are, one entry per batch: (batch name, file glob, game model).
# Only games whose every night carries its full record are kept (`has_night_records`).
BATCHES: list[tuple[str, str, str]] = [
    ("ten_seat_pilot", "batch_results/ten_seat_pilot/**/*.jsonl", "gemini-3.5-flash-lite"),
    ("phase3_games", "evidence/gameplay/data/phase3_games/*.record.json", "gemini-3.5-flash-lite"),
    ("phase3_balance", "evidence/gameplay/data/phase3_balance/*.record.json", "gemini-3.5-flash-lite"),
    ("phase3_balance_2", "evidence/gameplay/data/phase3_balance_2/*.record.json", "gemini-3.5-flash-lite"),
    ("phase3_balance_3", "evidence/gameplay/data/phase3_balance_3/*.record.json", "gemini-3.5-flash-lite"),
    ("phase3_balance_4", "evidence/gameplay/data/phase3_balance_4/*.record.json", "gemini-3.5-flash-lite"),
    ("phase3_flash_games", "evidence/gameplay/data/phase3_flash_games/*.record.json", "gemini-3.5-flash"),
    ("phase3_luna_games", "evidence/gameplay/data/phase3_luna_games/*.record.json", "openai/gpt-6-luna"),
    ("v8_smoke", "batch_results/v8_smoke/**/*.jsonl", "gemini-3.5-flash-lite"),
    ("v8_seeding", "batch_results/v8_seed_[abcd]/games/*.jsonl", "recorded"),
    ("v8_demo", "batch_results/v8_demo/games_*.jsonl", "anthropic/claude-haiku-5-5"),
    ("v8_gate_haiku", "batch_results/v8_gate_haiku/games_*.jsonl", "anthropic/claude-haiku-5-5"),
    ("v8_luna_memory", "batch_results/v8_luna_memory/**/*.jsonl", "openai/gpt-6-luna"),
    ("cache_ab_2026_10_13", "batch_results/cache_ab_2026_10_13/**/*.jsonl", "openai/gpt-6-luna"),
    ("evil_cover_games", "evidence/gameplay/data/evil_cover_games/*/*.capture.json.gz", "anthropic/claude-haiku-5-5"),
    ("persona_voice_games", "evidence/gameplay/data/persona_voice_games/*.capture.json.gz", "anthropic/claude-haiku-5-5"),
    ("silence_calibration", "evidence/gameplay/data/silence_calibration/games/*.capture.json.gz", "anthropic/claude-haiku-5-5"),
]

TOWN = "town"
WOLVES = "wolves"
LONE_KILLER = "lone_killer"

# The record's `winner` for each side. The lone killer's win is named after its role.
WINNERS_OF_SIDE: dict[str, set[str]] = {
    TOWN: {"villagers"},
    WOLVES: {"wolves"},
    LONE_KILLER: {"serial_killer", "necromancer"},
}


@dataclass
class ScoreSpec:
    """One score to check: whose win it is read against, and June's expected direction if any."""

    name: str
    side: str
    june_direction: str | None
    """"+" or "-" when the June nine-seat check registered a direction for this score; None when the
    score is new to the ten-seat game (exploratory) or was descriptive in June."""


SCORES: list[ScoreSpec] = [
    # Town: votes and lynches
    ScoreSpec("correct_elimination_rate", TOWN, "+"),
    ScoreSpec("town_mislynch_rate", TOWN, "-"),
    ScoreSpec("mislynches", TOWN, "-"),
    ScoreSpec("town_vote_accuracy", TOWN, "+"),
    ScoreSpec("wolf_elimination_rate", TOWN, "+"),
    ScoreSpec("lone_killer_lynched", TOWN, "+"),
    ScoreSpec("power_roles_killed_by_evil", TOWN, "-"),
    ScoreSpec("town_accusation_precision", TOWN, "+"),
    # Town: night roles
    ScoreSpec("healer_town_save_rate", TOWN, "+"),
    ScoreSpec("healer_save_rate", TOWN, "+"),
    ScoreSpec("healer_friendly_fire_save_rate", TOWN, "-"),
    ScoreSpec("investigator_find_to_lynch_rate", TOWN, "+"),
    ScoreSpec("investigator_wolves_found", TOWN, "+"),
    ScoreSpec("investigator_find_next_round_convergence", TOWN, "+"),
    ScoreSpec("vigilante_correct_shot_rate", TOWN, "+"),
    ScoreSpec("vigilante_evil_shots", TOWN, "+"),
    ScoreSpec("vigilante_friendly_fire_shots", TOWN, "-"),
    ScoreSpec("sentinel_watches_naming_evil", TOWN, None),
    ScoreSpec("trailseer_follows_naming_evil", TOWN, None),
    ScoreSpec("sigilist_hits", TOWN, None),
    # Wolves (the Chanteuse and the Illusionist)
    ScoreSpec("wolf_unconditioned_blending_rate", WOLVES, "+"),
    ScoreSpec("wolf_blending_rate", WOLVES, "+"),
    ScoreSpec("wolf_power_kill_rate", WOLVES, "+"),
    ScoreSpec("chanteuse_blocks_real", WOLVES, None),
    ScoreSpec("chanteuse_blocks_critical", WOLVES, None),
    ScoreSpec("chanteuse_blocks_wasted", WOLVES, None),
    ScoreSpec("illusionist_conceals", WOLVES, None),
    ScoreSpec("illusionist_conceals_hid_record", WOLVES, None),
    # Lone killer (the serial killer or the necromancer)
    ScoreSpec("sk_kill_rate", LONE_KILLER, "+"),
    ScoreSpec("sk_power_roles_killed", LONE_KILLER, "+"),
    ScoreSpec("sk_unconditioned_blending_rate", LONE_KILLER, "+"),
    ScoreSpec("necromancer_nights_survived", LONE_KILLER, None),
]


@dataclass
class GameRecord:
    """One ten-seat game, ready to score."""

    game_id: str
    batch: str
    model: str
    memory_on: bool
    winner: str
    scores: dict[str, float] = field(default_factory=dict)
    """Every numeric metric of the game, recomputed from its record (None values left out)."""


@dataclass
class CheckResult:
    """One score's correlation with its side's win, three ways."""

    name: str
    side: str
    june_direction: str | None
    games: int
    side_wins: int
    pooled_r: float
    pooled_p: float
    within_batch_r: float
    within_batch_p: float
    memory_off_games: int
    memory_off_r: float
    memory_off_p: float


def read_game_dicts(path: str) -> list[dict]:
    """The game records in one file: a batch JSONL (one per line), a record JSON or a capture.

    Args:
        path: a `.jsonl`, `.record.json` or `.capture.json.gz` file.

    Returns:
        The game dicts in it. A capture's game is its ``final_state``.
    """
    if path.endswith(".jsonl"):
        game_dicts = []
        with open(path) as handle:
            for line in handle:
                line = line.strip()
                if line.startswith("{"):
                    game_dicts.append(json.loads(line))
        return game_dicts
    if path.endswith(".gz"):
        with gzip.open(path, "rt") as handle:
            capture = json.load(handle)
        return [capture["final_state"]]
    with open(path) as handle:
        return [json.load(handle)]


def memory_was_on(game: dict) -> bool:
    """Whether any role played with memory. Records with no memory config played without it.

    Args:
        game: one game record.

    Returns:
        True when the record's ``memory_config`` turns memory on for at least one role.
    """
    memory_config = game.get("memory_config")
    if not isinstance(memory_config, dict):
        return False
    return any(bool(enabled) for enabled in memory_config.values())


def score_game(game: dict) -> dict[str, float] | None:
    """Recompute a game's metrics from its record.

    Args:
        game: one ten-seat game record with roles, winner, day and night resolutions.

    Returns:
        The numeric metrics (None values left out), or None when a night lacks its full record.
    """
    metrics = Metrics(
        day_resolutions=game.get("day_resolutions") or [],
        night_resolutions=game.get("night_resolutions") or [],
    )
    if not metrics.night_resolutions or not all(night.outcome for night in metrics.night_resolutions):
        return None
    result = dict(game)
    # Server records carry no survivor lists; they feed only the exit-method labels, not a score here.
    result.setdefault("surviving_wolves", [])
    result.setdefault("surviving_villagers", [])
    # The accusation counts read the day's messages as models, as the live game holds them.
    messages = []
    for message in game.get("day_channel") or []:
        messages.append(DayChannel.model_validate(message))
    result["day_channel"] = messages
    computed = compute_game_metrics(result, metrics).model_dump()
    numeric_scores = {}
    for name, value in computed.items():
        if isinstance(value, bool):
            numeric_scores[name] = float(value)
        elif isinstance(value, (int, float)):
            numeric_scores[name] = float(value)
    return numeric_scores


def load_games() -> list[GameRecord]:
    """Every ten-seat game with full night records, scored, one per game id.

    Returns:
        The games, in batch order.
    """
    games: list[GameRecord] = []
    seen_ids: set[str] = set()
    for batch_name, pattern, model in BATCHES:
        for path in sorted(glob.glob(pattern, recursive=True)):
            if "eval_cases" in path:
                continue
            for game in read_game_dicts(path):
                if not isinstance(game.get("roles"), dict) or "wolf" in game["roles"].values():
                    continue
                game_id = game.get("game_id") or path
                if game_id in seen_ids:
                    continue
                scores = score_game(game)
                if scores is None:
                    continue
                seen_ids.add(game_id)
                game_model = model
                if model == "recorded":
                    game_model = (game.get("runtime_fingerprint") or {}).get("game_model") or "unknown"
                games.append(GameRecord(
                    game_id=game_id,
                    batch=batch_name,
                    model=game_model,
                    memory_on=memory_was_on(game),
                    winner=str(game.get("winner")),
                    scores=scores,
                ))
    return games


def side_won(game: GameRecord, side: str) -> int:
    """1 when the game's winner is the given side, else 0."""
    return int(game.winner in WINNERS_OF_SIDE[side])


def within_batch_correlation(games: list[GameRecord], score: str, side: str) -> tuple[float, float]:
    """Correlate score and win after taking each batch's own mean out of both.

    Args:
        games: the games where the score is defined.
        score: the metric name.
        side: whose win to read it against.

    Returns:
        (r, p) over the batch-centred values; batches with one game add nothing and are dropped.
    """
    games_by_batch: dict[str, list[GameRecord]] = {}
    for game in games:
        games_by_batch.setdefault(game.batch, []).append(game)
    centred_scores: list[float] = []
    centred_wins: list[float] = []
    for batch_games in games_by_batch.values():
        if len(batch_games) < 2:
            continue
        batch_score_mean = sum(game.scores[score] for game in batch_games) / len(batch_games)
        batch_win_mean = sum(side_won(game, side) for game in batch_games) / len(batch_games)
        for game in batch_games:
            centred_scores.append(game.scores[score] - batch_score_mean)
            centred_wins.append(side_won(game, side) - batch_win_mean)
    return pearson(centred_wins, centred_scores)


def check_score(games: list[GameRecord], spec: ScoreSpec) -> CheckResult:
    """One score's correlation with its side's win: pooled, within batch, memory-off only.

    Args:
        games: every scored game.
        spec: the score and its side.

    Returns:
        The three correlations, with the game counts behind them.
    """
    scored_games = []
    for game in games:
        if spec.name in game.scores:
            scored_games.append(game)
    wins = []
    values = []
    for game in scored_games:
        wins.append(side_won(game, spec.side))
        values.append(game.scores[spec.name])
    pooled_r, pooled_p = point_biserial(wins, values)
    within_r, within_p = within_batch_correlation(scored_games, spec.name, spec.side)

    off_wins = []
    off_values = []
    for game in scored_games:
        if not game.memory_on:
            off_wins.append(side_won(game, spec.side))
            off_values.append(game.scores[spec.name])
    off_r, off_p = point_biserial(off_wins, off_values)

    return CheckResult(
        name=spec.name,
        side=spec.side,
        june_direction=spec.june_direction,
        games=len(scored_games),
        side_wins=sum(wins),
        pooled_r=pooled_r,
        pooled_p=pooled_p,
        within_batch_r=within_r,
        within_batch_p=within_p,
        memory_off_games=len(off_wins),
        memory_off_r=off_r,
        memory_off_p=off_p,
    )


def correlation_range(r: float, games: int) -> tuple[float, float]:
    """The 95% range of a correlation (Fisher's z), to show what a small sample cannot rule out.

    Args:
        r: the measured correlation.
        games: how many games it rests on.

    Returns:
        (low, high); (nan, nan) when r is not computable or there are fewer than four games.
    """
    if r is None or math.isnan(r) or games < 4 or abs(r) >= 1:
        return (float("nan"), float("nan"))
    z = math.atanh(r)
    half_width = 1.96 / math.sqrt(games - 3)
    return (math.tanh(z - half_width), math.tanh(z + half_width))


def rounded(value: float) -> float | None:
    """A correlation or p-value to three places; None when it could not be computed."""
    if value is None or math.isnan(value):
        return None
    return round(value, 3)


def format_cell(r: float, p: float) -> str:
    """'+0.62 (p<0.001)' for the printed table; '—' when not computable."""
    if r is None or math.isnan(r):
        return "—"
    if p < 0.001:
        p_text = "p<0.001"
    else:
        p_text = f"p={p:.3f}"
    return f"{r:+.2f} ({p_text})"


def main() -> None:
    """Run the check, print a markdown table, and write the summary JSON."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", required=True, help="where to write summary.json")
    args = parser.parse_args()

    games = load_games()
    batch_counts: dict[str, dict] = {}
    for game in games:
        entry = batch_counts.setdefault(game.batch, {"games": 0, "model": game.model, "memory_on": 0, "winners": {}})
        entry["games"] += 1
        entry["memory_on"] += int(game.memory_on)
        entry["winners"][game.winner] = entry["winners"].get(game.winner, 0) + 1

    results = []
    for spec in SCORES:
        results.append(check_score(games, spec))

    print(f"{len(games)} ten-seat games; memory off in {sum(not game.memory_on for game in games)}")
    print("| Score | Side | June | Games (side wins) | All games | Within batch | Memory off (games) |")
    print("|---|---|---|---|---|---|---|")
    for result in results:
        print(
            f"| `{result.name}` | {result.side} | {result.june_direction or 'new'} | "
            f"{result.games} ({result.side_wins}) | {format_cell(result.pooled_r, result.pooled_p)} | "
            f"{format_cell(result.within_batch_r, result.within_batch_p)} | "
            f"{format_cell(result.memory_off_r, result.memory_off_p)} ({result.memory_off_games}) |"
        )

    result_rows = []
    for result in results:
        range_low, range_high = correlation_range(result.pooled_r, result.games)
        result_rows.append({
            "score": result.name,
            "side": result.side,
            "june_direction": result.june_direction,
            "games": result.games,
            "side_wins": result.side_wins,
            "pooled_r": rounded(result.pooled_r),
            "pooled_p": rounded(result.pooled_p),
            "pooled_range_95": [rounded(range_low), rounded(range_high)],
            "within_batch_r": rounded(result.within_batch_r),
            "within_batch_p": rounded(result.within_batch_p),
            "memory_off_games": result.memory_off_games,
            "memory_off_r": rounded(result.memory_off_r),
            "memory_off_p": rounded(result.memory_off_p),
        })
    summary = {"games": len(games), "batches": batch_counts, "scores": result_rows}
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(summary, indent=2) + "\n")
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
