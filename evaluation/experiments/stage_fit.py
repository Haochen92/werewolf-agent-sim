"""Stage fit: would the live stage have waited for the model? Read from served games' traces.

The server never waits for the stage: it runs ahead, and the browser plays each beat at its full hold
(a speech at 2.4 words a second for 5 to 15 s, a pass 4 s; `frontend/src/stage/beats/beatsFor.ts`). A
model call is fast enough when its event has arrived before the stage reaches it; otherwise the stage
stands with nothing to play. This runner measures that for served games, at no model cost:

1. Read each game's durable events (the server's Postgres, read-only) and its Langfuse trace.
2. Cut the events into beats with the stage's own cutter, as the seated human's live stage would
   (`frontend/scripts/beats-for-log.ts`).
3. Give every event the time it left the server. A seat's speech or pass is matched to its
   `day_channel_<seat>` span, a vote to `day_votes_<seat>`, a pack line to `wolf_channel_<seat>`, a night
   action to `<role>_target_<seat>` (only where the counts agree), a night result, lynch result and day
   summary to their own nodes. A round's lines and a day's votes leave together when the round or vote
   is collected. Every other event leaves with the one before it.
4. Find when the human acted: each action resumes the engine as a `LangGraph` run nested under another.
5. Play the beats: each starts at the later of the stage being free and its last needed event having
   arrived. Time the engine spent waiting for the human is not the model's, so it is taken out.

Two readings bound the answer: "restart", where the stage starts afresh at each human action (a solo
prompt waits for the stage, so the stage is at the prompt when the human acts), and "continuous", where
the simulated stage's own backlog is carried on (it ran behind the real one in some games, which hides
waits). Also reported: each model call's latency by graph node.

    poetry run python -m evaluation.experiments.stage_fit --since 2026-10-11 \
        --out frontend/docs/stage_fit/results.json

Raw events and traces are cached in `evaluation/eval_results/stage_fit/` (gitignored).
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path

from evaluation.src.core.settings import REPO_ROOT

CACHE_DIR = REPO_ROOT / "evaluation/eval_results/stage_fit"
FRONTEND = REPO_ROOT / "frontend"
OBSERVATION_FIELDS = ("id", "name", "type", "parentObservationId", "startTime", "endTime", "latency", "model")
SPAN_TYPES = ("GENERATION", "CHAIN", "SPAN")
WAIT_FLOOR_SECONDS = 0.5
"""A gap shorter than this is rounding between the trace's clock and the holds, not a wait."""

# Event kind -> (event types, span-name pattern capturing the seat). Matched per seat, in order.
SEAT_MAPPINGS = {
    "speech and passes": (("speech", "pass_marker"), r"day_channel_(player_\d+)"),
    "votes": (("vote_cast",), r"day_votes_(player_\d+)"),
    "pack lines": (("wolf_message",), r"wolf_channel_(player_\d+)"),
    "night actions": (("night_action",), r"[a-z_]+_target_(player_\d+)"),
}
# Event type -> the node that produces it, one span per event, matched in order.
PHASE_MAPPINGS = {
    "night_result": "NIGHT_RESOLUTION",
    "lynch_result": "DAY_RESOLUTION",
    "day_summary": "SUMMARIZE_DAY_DISCUSSION",
}
ROUND_END_TYPES = ("turn_started", "phase_change", "lynch_result", "round_opened", "vote_cast")
VOTE_BLOCK_TYPES = ("vote_cast", "lynch_result", "player_reads", "strategy_update")


@dataclass
class StageWait:
    """One stretch the stage stood with nothing to play."""

    beat: str
    """The beat it waited for, e.g. "day.pass"."""
    scene: str
    day: int
    seconds: float


@dataclass
class GameFit:
    """One game's stage fit."""

    game_id: str
    model: str
    human: str | None
    """The seated human, or None for an AI-only game."""
    beats: int
    stage_seconds: float
    """The beats' holds added up: how long the stage plays."""
    waits_restart_seconds: float
    waits_continuous_seconds: float
    waits: list[StageWait] = field(default_factory=list)
    """The restart reading's waits."""
    unmatched_counts: dict[str, int] = field(default_factory=dict)
    """Per mapping, the seats whose span and event counts differed (left unmatched for night actions)."""


def parse_time(text: str) -> float:
    """Return seconds since the epoch for a Langfuse or Postgres timestamp string."""
    return datetime.fromisoformat(text.replace("Z", "+00:00")).timestamp()


def seat_of(event: dict) -> str | None:
    """Return the seat an event is by: its speaker, voter, actor or pack member."""
    return event.get("player") or event.get("voter") or event.get("actor") or event.get("wolf")


# --- reading the games ---------------------------------------------------------------------------------


def served_games(since: str) -> list[dict]:
    """Return the completed served games created on or after a date, newest first.

    Args:
        since: an ISO date, e.g. "2026-10-11".

    Returns:
        One row per game: game id, model, human players and creation time.
    """
    import psycopg
    from dotenv import dotenv_values
    from psycopg.rows import dict_row

    dsn = dotenv_values(REPO_ROOT / ".env")["WW_POSTGRES_DSN"]
    with psycopg.connect(dsn, autocommit=True, row_factory=dict_row,
                         options="-c default_transaction_read_only=on") as connection:
        rows = connection.execute(
            "select game_id, model, human_players, created_at from games "
            "where created_at >= %s and status = 'completed' order by created_at desc", (since,)).fetchall()
    return rows


def fetch_game(game_id: str) -> dict:
    """Return a game's events and trace observations, from the cache or fetched and cached.

    Args:
        game_id: the served game's id (also its Langfuse session id).

    Returns:
        {"game": the games row as strings, "events": [...], "observations": [...]}.
    """
    cache_path = CACHE_DIR / f"game_{game_id[:8]}.json"
    if cache_path.exists():
        return json.loads(cache_path.read_text())

    import psycopg
    from dotenv import dotenv_values
    from psycopg.rows import dict_row

    from evaluation.src.data.sources.langfuse import _field, _require_langfuse_api, fetch_trace_ids_for_session_id

    dsn = dotenv_values(REPO_ROOT / ".env")["WW_POSTGRES_DSN"]
    with psycopg.connect(dsn, autocommit=True, row_factory=dict_row,
                         options="-c default_transaction_read_only=on") as connection:
        events = [row["payload"] for row in connection.execute(
            "select payload from events where game_id = %s order by seq", (game_id,)).fetchall()]
        game_row = connection.execute(
            "select game_id, model, human_players, created_at, finished_at from games where game_id = %s",
            (game_id,)).fetchone()

    api = _require_langfuse_api()
    observations = []
    for trace_id in fetch_trace_ids_for_session_id(game_id):
        for span_type in SPAN_TYPES:
            page = 1
            while True:
                listing = api.observations.get_many(trace_id=trace_id, type=span_type, page=page, limit=100)
                page_rows = _field(listing, "data", [])
                for observation in page_rows:
                    record = observation.dict()
                    row = {}
                    for name in OBSERVATION_FIELDS:
                        row[name] = record.get(name)
                    row["startTime"] = str(record.get("startTime"))
                    row["endTime"] = str(record.get("endTime"))
                    metadata = record.get("metadata") or {}
                    row["node"] = metadata.get("langgraph_node") if isinstance(metadata, dict) else None
                    observations.append(row)
                if len(page_rows) < 100:
                    break
                page += 1

    game = {"game": {key: str(value) for key, value in dict(game_row).items()}, "events": events,
            "observations": observations}
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(json.dumps(game))
    return game


def human_seat(game: dict) -> str | None:
    """Return the game's seated human, or None for an AI-only game."""
    seats = re.findall(r"player_\d+", game["game"].get("human_players") or "")
    return seats[0] if seats else None


def stage_beats(game: dict, human: str | None) -> list[dict]:
    """Return the beats the human's live stage would play, cut by the frontend's own code.

    Args:
        game: the fetched game.
        human: the seated human, or None.

    Returns:
        One dict per beat: id, scene, day, seq, end, holdMs, subject, liveOnly.
    """
    game_path = CACHE_DIR / f"events_{game['game']['game_id'][:8]}.json"
    beats_path = CACHE_DIR / f"beats_{game['game']['game_id'][:8]}.json"
    game_path.write_text(json.dumps({"events": game["events"]}))
    subprocess.run([str(FRONTEND / "node_modules/.bin/vite-node"), "--config", "vitest.config.ts",
                    "scripts/beats-for-log.ts", "--", str(game_path), str(beats_path), human or ""],
                   cwd=FRONTEND, check=True, capture_output=True)
    return json.loads(beats_path.read_text())


# --- when each event left the server -------------------------------------------------------------------


def span_ends_by_seat(observations: list[dict], name_pattern: str) -> dict[str, list[float]]:
    """Return, per seat, the end times of the spans whose name matches a pattern, in time order.

    Args:
        observations: the trace's observations.
        name_pattern: a regex with one group capturing the seat, e.g. r"day_votes_(player_\\d+)".

    Returns:
        {"player_4": [end time, ...], ...}.
    """
    ends: dict[str, list[float]] = defaultdict(list)
    for observation in observations:
        match = re.fullmatch(name_pattern, observation["name"] or "")
        if match and observation["endTime"] not in ("None", None):
            ends[match.group(1)].append(parse_time(observation["endTime"]))
    for seat in ends:
        ends[seat].sort()
    return ends


def node_span_ends(observations: list[dict], node_name: str) -> list[float]:
    """Return the end times of a graph node's own spans, in time order."""
    ends = []
    for observation in observations:
        if observation["name"] == node_name and observation["type"] == "CHAIN":
            ends.append(parse_time(observation["endTime"]))
    return sorted(ends)


def emit_times(game: dict, human: str | None) -> tuple[list[float], dict[str, int]]:
    """Return when each event left the server, in log order, and the seats left unmatched per mapping.

    Args:
        game: the fetched game.
        human: the seated human, whose events have no model spans.

    Returns:
        (times, unmatched): one time per event; per mapping, how many seats had differing counts.
    """
    events = game["events"]
    observations = game["observations"]
    time_by_seq: dict[int, float] = {}
    unmatched: dict[str, int] = {}

    for label, (event_types, name_pattern) in SEAT_MAPPINGS.items():
        ends = span_ends_by_seat(observations, name_pattern)
        events_by_seat: dict[str, list[dict]] = defaultdict(list)
        for event in events:
            seat = seat_of(event)
            if event["type"] in event_types and seat and seat != human:
                events_by_seat[seat].append(event)
        unmatched[label] = 0
        for seat, seat_events in events_by_seat.items():
            seat_ends = ends.get(seat, [])
            if len(seat_ends) != len(seat_events):
                unmatched[label] += 1
                if label == "night actions":
                    continue  # a carrier's kill and its skill can shift the order; pairing would misplace times
            for event, end in zip(seat_events, seat_ends):
                time_by_seq[event["seq"]] = end

    for event_type, node_name in PHASE_MAPPINGS.items():
        ends = node_span_ends(observations, node_name)
        phase_events = [event for event in events if event["type"] == event_type]
        for event, end in zip(phase_events, ends):
            time_by_seq[event["seq"]] = end

    # A round's lines and a day's votes go out together, when the collect step ends.
    round_ends = node_span_ends(observations, "COLLECT_ROUND")
    vote_ends = node_span_ends(observations, "COLLECT_VOTES")
    rounds_seen = 0
    votes_seen = 0
    index = 0
    while index < len(events):
        event = events[index]
        if event["type"] == "round_opened" and rounds_seen < len(round_ends):
            collect_end = round_ends[rounds_seen]
            rounds_seen += 1
            index += 1
            while index < len(events) and events[index]["type"] not in ROUND_END_TYPES:
                seq = events[index]["seq"]
                time_by_seq[seq] = max(time_by_seq.get(seq, 0.0), collect_end)
                index += 1
            continue
        if event["type"] == "vote_cast" and votes_seen < len(vote_ends):
            collect_end = vote_ends[votes_seen]
            votes_seen += 1
            while index < len(events) and events[index]["type"] in VOTE_BLOCK_TYPES:
                seq = events[index]["seq"]
                time_by_seq[seq] = max(time_by_seq.get(seq, 0.0), collect_end)
                index += 1
                if events[index - 1]["type"] == "lynch_result":
                    break
            continue
        index += 1

    times = []
    latest = parse_time(game["game"]["created_at"])
    for event in events:
        own_time = time_by_seq.get(event["seq"])
        if own_time is not None and own_time > latest:
            latest = own_time
        times.append(latest)  # events leave in seq order, so a time never goes backwards
    return times, unmatched


def resume_times(observations: list[dict]) -> list[float]:
    """Return when the engine resumed after the human acted.

    A resume is a `LangGraph` run nested directly under another `LangGraph` run. The game's first run
    hangs off the root span and a subgraph's run off a phase node, so neither counts. Runs within a
    second of each other are one resume.

    Args:
        observations: the trace's observations.

    Returns:
        The resume times, in order.
    """
    name_by_id = {}
    for observation in observations:
        name_by_id[observation["id"]] = observation["name"]
    starts = []
    for observation in observations:
        if observation["name"] == "LangGraph" and name_by_id.get(observation["parentObservationId"]) == "LangGraph":
            starts.append(parse_time(observation["startTime"]))
    starts.sort()
    resumes = []
    for start in starts:
        if not resumes or start - resumes[-1] > 1.0:
            resumes.append(start)
    return resumes


def human_blocked(events: list[dict], times: list[float], resumes: list[float],
                  human: str | None) -> list[tuple[float, float]]:
    """Return the stretches the engine waited for the human: each prompt until the next resume."""
    blocked = []
    for index, event in enumerate(events):
        if event["type"] == "input_request" and event.get("player") == human:
            asked_at = times[index]
            later = [resume for resume in resumes if resume > asked_at]
            if later:
                blocked.append((asked_at, later[0]))
    return blocked


def seconds_inside(start: float, end: float, stretches: list[tuple[float, float]]) -> float:
    """Return how many seconds of [start, end] fall inside the stretches."""
    total = 0.0
    for low, high in stretches:
        total += max(0.0, min(end, high) - max(start, low))
    return total


# --- playing the stage ---------------------------------------------------------------------------------


def play_stage(beats: list[dict], times: list[float], resumes: list[float],
               blocked: list[tuple[float, float]], restart_at_human: bool) -> tuple[list[StageWait], float]:
    """Play the beats against the event times and return the waits and the stage's playing time.

    Args:
        beats: the stage's beats, in order.
        times: when each event left the server.
        resumes: when the human acted.
        blocked: the stretches the engine waited for the human (not counted as waits).
        restart_at_human: at each human action, start the stage afresh from the action, or carry the
            simulated backlog on.

    Returns:
        (waits, stage_seconds).
    """
    stage_free = times[0]
    waits = []
    stage_seconds = 0.0
    for beat in beats:
        ready = times[beat["end"] - 1]
        start = max(stage_free, ready)
        wait = ready - stage_free
        if wait > 0:
            wait -= seconds_inside(stage_free, ready, blocked)
        if wait > WAIT_FLOOR_SECONDS:
            waits.append(StageWait(beat=beat["id"], scene=beat["scene"], day=beat["day"], seconds=round(wait, 1)))
        if beat["holdMs"] > 0:
            stage_free = start + beat["holdMs"] / 1000
            stage_seconds += beat["holdMs"] / 1000
            continue
        if not beat["liveOnly"]:
            break  # the epilogue: the game is over
        later = [resume for resume in resumes if resume > ready]
        if not later:
            break
        if restart_at_human:
            stage_free = later[0]
        else:
            stage_free = max(start, later[0])
    return waits, stage_seconds


def game_fit(game: dict) -> GameFit:
    """Return one game's stage fit, both readings."""
    human = human_seat(game)
    beats = stage_beats(game, human)
    times, unmatched = emit_times(game, human)
    resumes = resume_times(game["observations"])
    blocked = human_blocked(game["events"], times, resumes, human)
    restart_waits, stage_seconds = play_stage(beats, times, resumes, blocked, restart_at_human=True)
    continuous_waits, _ = play_stage(beats, times, resumes, blocked, restart_at_human=False)
    return GameFit(
        game_id=game["game"]["game_id"],
        model=game["game"]["model"],
        human=human,
        beats=len(beats),
        stage_seconds=round(stage_seconds),
        waits_restart_seconds=round(sum(wait.seconds for wait in restart_waits), 1),
        waits_continuous_seconds=round(sum(wait.seconds for wait in continuous_waits), 1),
        waits=restart_waits,
        unmatched_counts=unmatched,
    )


def percentile(values: list[float], fraction: float) -> float:
    """Return a percentile by linear interpolation, e.g. fraction 0.95."""
    ordered = sorted(values)
    position = (len(ordered) - 1) * fraction
    low = int(position)
    high = min(low + 1, len(ordered) - 1)
    return round(ordered[low] + (ordered[high] - ordered[low]) * (position - low), 1)


def latency_by_node(games: list[dict]) -> dict[str, dict]:
    """Return each model call's latency by model and graph node: calls, median, p90, p95 and max."""
    seconds: dict[str, list[float]] = defaultdict(list)
    for game in games:
        for observation in game["observations"]:
            if observation["type"] == "GENERATION" and observation.get("latency") is not None:
                key = f"{game['game']['model']} | {observation.get('node') or '?'}"
                seconds[key].append(observation["latency"])
    table = {}
    for key in sorted(seconds):
        values = seconds[key]
        table[key] = {"calls": len(values), "p50": percentile(values, 0.5), "p90": percentile(values, 0.9),
                      "p95": percentile(values, 0.95), "max": round(max(values), 1)}
    return table


def main() -> None:
    """Fetch the served games, measure the stage fit of each, and write the results JSON."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--since", default="2026-10-11", help="served games created on or after this date")
    parser.add_argument("--exclude", nargs="*", default=[], help="game id prefixes to leave out")
    parser.add_argument("--out", required=True, help="where to write results.json")
    args = parser.parse_args()

    games = []
    for row in served_games(args.since):
        if any(row["game_id"].startswith(prefix) for prefix in args.exclude):
            continue
        games.append(fetch_game(row["game_id"]))

    fits = []
    for game in games:
        fit = game_fit(game)
        fits.append(fit)
        print(f"{fit.game_id[:8]} {fit.model:28s} {'human' if fit.human else 'ai-only':7s} "
              f"stage {fit.stage_seconds:5.0f} s  waits {fit.waits_continuous_seconds:6.1f}-{fit.waits_restart_seconds:6.1f} s")

    pooled: dict[str, dict] = defaultdict(lambda: {"games": 0, "stage_seconds": 0.0, "waits_continuous": 0.0,
                                                   "waits_restart": 0.0})
    waits_by_beat: dict[str, dict] = defaultdict(lambda: {"waits": 0, "seconds": 0.0, "max": 0.0})
    for fit in fits:
        if fit.human is None:
            continue  # an AI-only game's stage only falls further behind; it never waits
        row = pooled[fit.model]
        row["games"] += 1
        row["stage_seconds"] += fit.stage_seconds
        row["waits_continuous"] += fit.waits_continuous_seconds
        row["waits_restart"] += fit.waits_restart_seconds
        for wait in fit.waits:
            beat_row = waits_by_beat[f"{fit.model} | {wait.beat}"]
            beat_row["waits"] += 1
            beat_row["seconds"] = round(beat_row["seconds"] + wait.seconds, 1)
            beat_row["max"] = max(beat_row["max"], wait.seconds)
    for row in pooled.values():
        row["share_continuous"] = round(row["waits_continuous"] / row["stage_seconds"], 3)
        row["share_restart"] = round(row["waits_restart"] / row["stage_seconds"], 3)

    results = {"since": args.since, "excluded": args.exclude, "pooled_human_games": dict(pooled),
               "waits_by_beat": dict(waits_by_beat), "latency_by_node": latency_by_node(games),
               "games": [asdict(fit) for fit in fits]}
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=1) + "\n")
    for model, row in pooled.items():
        print(f"{model}: {row['games']} games, waits {100 * row['share_continuous']:.1f}-"
              f"{100 * row['share_restart']:.1f}% of stage time")
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
