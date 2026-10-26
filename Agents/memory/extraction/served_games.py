"""Served games for the offline extraction job: which to take, their inputs, and the write-back.

The owner runs extraction by hand, offline, in batches (v8 decisions §11, §16). A served game saves its
extraction input when it completes (``games.extraction_input``); this module reads the games a run
selects, and writes what the run extracted back: the ``game_lessons`` row (migration 0015), which the
replay shows and the learning tick folds, and ``games.lessons_extracted_at``. Which games a run takes is
a setting chosen per run, not a rule: memory on or off, with or without a human seat, finished after a
time, named games, or a random sample of them. Games with a human seat may teach the store (§16).
"""

from __future__ import annotations

import os
import random
from dataclasses import dataclass, field
from datetime import datetime, timezone
from logging import getLogger
from types import SimpleNamespace

logger = getLogger(__name__)

_TEN_SEATS = ("jsonb_array_length(coalesce((select payload->'lineup' from events e "
              "where e.game_id = games.game_id and e.seq = 1), '[]')) = 10")


@dataclass
class ServedSelection:
    """Which completed ten-seat served games an extraction run takes."""

    memory: bool | None = True
    """Memory on (True), off (False) or either (None)."""
    humans: bool | None = None
    """Only games with a human seat (True), only AI-only games (False) or either (None)."""
    since: str | None = None
    """Only games finished after this ISO time."""
    games: list[str] = field(default_factory=list)
    """Only games whose id starts with one of these."""
    sample: int | None = None
    """Take this many of the matching games at random (``seed``), instead of all of them."""
    seed: int = 0
    redo: bool = False
    """Also take games already extracted (a game already folded into the store is never rewritten)."""


def select_served_games(selection: ServedSelection, dsn: str | None = None) -> list[tuple[dict, object]]:
    """The selected games' extraction inputs, oldest first.

    Args:
        selection: which games to take.
        dsn: the database; ``WW_POSTGRES_DSN`` by default.

    Returns:
        (metadata, ExtractionCase) per game, the same shape ``offline.load_inputs`` returns for files.
        A game whose input was not saved (it finished before inputs were) is rebuilt from its event log,
        which lacks the pack's vote lines (``offline.input_from_event_log``).
    """
    import psycopg
    from psycopg.rows import dict_row

    from Agents.memory.extraction.offline import input_from_event_log
    from Agents.schemas.evaluation import ExtractionCase

    query = ("select game_id, memory, n_humans, human_players, extraction_input from games "
             f"where status = 'completed' and {_TEN_SEATS}")
    params: list = []
    if selection.memory is not None:
        query += " and memory = %s"
        params.append(selection.memory)
    if selection.humans is True:
        query += " and n_humans > 0"
    elif selection.humans is False:
        query += " and n_humans = 0"
    if selection.since:
        query += " and finished_at > %s"
        params.append(selection.since)
    if selection.games:
        query += " and (" + " or ".join("game_id like %s" for _ in selection.games) + ")"
        params += [f"{prefix}%" for prefix in selection.games]
    if not selection.redo:
        query += " and lessons_extracted_at is null"
    query += " order by finished_at"

    with psycopg.connect(dsn or os.environ["WW_POSTGRES_DSN"], autocommit=True, row_factory=dict_row,
                         options="-c default_transaction_read_only=on") as conn:
        rows = conn.execute(query, params).fetchall()
        if selection.sample is not None and selection.sample < len(rows):
            chosen = set(random.Random(selection.seed).sample(range(len(rows)), selection.sample))
            rows = [row for i, row in enumerate(rows) if i in chosen]

        selected = []
        for row in rows:
            human_players = list(row["human_players"] or [])
            if row["extraction_input"]:
                case = ExtractionCase.model_validate(row["extraction_input"])
                case = case.model_copy(update={"observations": [], "strategy_points": []})
                input_source = "saved"
            else:
                events = [r["payload"] for r in conn.execute(
                    "select payload from events where game_id = %s order by seq", (row["game_id"],)).fetchall()]
                case = input_from_event_log(row["game_id"], events, human_players)
                input_source = "event_log"
            metadata = {"source": "server", "input": input_source, "memory": row["memory"],
                        "n_humans": row["n_humans"], "human_players": human_players}
            selected.append((metadata, case))
    return selected


def write_back(run_name: str, filled_cases: list, dehalo: dict[str, dict], dsn: str | None = None) -> dict:
    """Write each extracted game's lessons into ``game_lessons`` and mark the game extracted.

    Args:
        run_name: the extraction run's name.
        filled_cases: the games' ExtractionCases with their observations filled in (verdicts as de-halo
            left them).
        dehalo: the de-halo record by game id (missing when the pass was skipped or failed).
        dsn: the database; ``WW_POSTGRES_DSN`` by default.

    Returns:
        {"written": n, "skipped_folded": [game ids]}: a game whose earlier lessons the learning tick has
        already folded into the store keeps them, since folding the new ones too would count the game
        twice.
    """
    import psycopg
    from psycopg.types.json import Jsonb

    from Agents.memory.extraction.offline import memory_extracted_payload
    from Agents.schemas.memory import cell_observation_schema_for

    written, skipped = 0, []
    with psycopg.connect(dsn or os.environ["WW_POSTGRES_DSN"]) as conn:
        for case in filled_cases:
            folded = conn.execute("select folded_in_gen from game_lessons where game_id = %s",
                                  (case.game_id,)).fetchone()
            if folded and folded[0] is not None:
                skipped.append(case.game_id)
                continue
            days = conn.execute("select days from games where game_id = %s", (case.game_id,)).fetchone()
            observations = [cell_observation_schema_for(o["perspective"], o["action_phase"]).model_validate(o)
                            for o in case.observations]
            replay = memory_extracted_payload(SimpleNamespace(observations=observations, strategy_points=[]),
                                              day=(days[0] if days and days[0] is not None else 0))
            with conn.transaction():
                conn.execute(
                    "insert into game_lessons (game_id, run_name, extraction_case, dehalo, replay, model_used) "
                    "values (%s, %s, %s, %s, %s, %s) on conflict (game_id) do update set "
                    "run_name = excluded.run_name, extraction_case = excluded.extraction_case, "
                    "dehalo = excluded.dehalo, replay = excluded.replay, model_used = excluded.model_used, "
                    "extracted_at = now()",
                    (case.game_id, run_name, Jsonb(case.model_dump(mode="json")),
                     Jsonb(dehalo[case.game_id]) if case.game_id in dehalo else None,
                     Jsonb(replay), case.model_used or ""))
                conn.execute("update games set lessons_extracted_at = %s where game_id = %s",
                             (datetime.now(timezone.utc), case.game_id))
            written += 1
    if skipped:
        logger.warning("%d games already folded into the store kept their lessons: %s", len(skipped),
                       ", ".join(g[:8] for g in skipped))
    return {"written": written, "skipped_folded": skipped}
