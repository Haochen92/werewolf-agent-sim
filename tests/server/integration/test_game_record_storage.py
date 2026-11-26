"""A served game's record of how it was run, on a real Postgres database, in the test container.

The unit tests (tests/server/test_game_record.py) show what a game hands to the repository. These
show it stored on the real tables: each run of a game's task is appended to the game's row, the
record of rescued and defaulted turns reads back as saved, and every event row carries the time
it was written.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlmodel import select

from server.database_models.game import RUNNING, EventRow
from server.db import Database
from server.storage.game_repository import GameRepository
from tests.factories.builders import short_event_log
from tests.fixtures.database import sqlalchemy_url


async def test_a_games_runs_outcomes_and_event_times_are_stored(server_tables_dsn):
    # Arrange
    database = Database(sqlalchemy_url(server_tables_dsn))
    await database.startup()
    try:
        repository = GameRepository(database)
        assert await repository.create_game("itest-game", status=RUNNING, model="test-model",
                                            seats=[])
        assert (await repository.load_game("itest-game")).runs is None  # nothing ran yet

        # Round 1: two runs of the task, as for a game resumed by a new process on a new build
        first = {"trace_id": "trace-1", "started_at": "2026-11-20T01:00:00+00:00",
                 "recovered": False, "fingerprint": {"git_commit": "aaaa", "game_model": "m"}}
        second = {"trace_id": "trace-2", "started_at": "2026-11-20T02:00:00+00:00",
                  "recovered": True, "fingerprint": {"git_commit": "bbbb", "game_model": "m"}}
        assert await repository.record_run("itest-game", first)
        assert await repository.record_run("itest-game", second)
        # Appended in the database, oldest first: the second process never read the first's entry.
        assert (await repository.load_game("itest-game")).runs == [first, second]

        # Round 2: the record of rescued and defaulted turns
        outcomes = {"counts": {"rescue": 2, "failed_pass": 0, "random_default": 1,
                               "no_action_default": 0},
                    "turns": [{"player": "player_5", "day": 1, "turn": "day_votes",
                               "path": "random_default"}],
                    "cached_steps": 3}
        assert await repository.update_game("itest-game", turn_outcomes=outcomes)
        assert (await repository.load_game("itest-game")).turn_outcomes == outcomes

        # Round 3: each event row carries the time it was written
        before = datetime.now(timezone.utc) - timedelta(minutes=1)
        assert await repository.record_events("itest-game", short_event_log())
        async with database.session() as session:
            saved_at = (await session.execute(
                select(EventRow.saved_at).where(EventRow.game_id == "itest-game"))).scalars().all()
        assert len(saved_at) == len(short_event_log())
        assert all(at is not None and at >= before for at in saved_at)
    finally:
        await database.close()
