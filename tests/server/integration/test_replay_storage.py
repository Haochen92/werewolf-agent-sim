"""The replay archive's storage on a real Postgres database, in the test container.

The game repository writes a game's row, its events and its cast, completes it, and the replay
service reads it back; retries do not duplicate rows, and a game whose event log has a gap is
never served as a replay. The tables are made by the server's migrations (`server_tables_dsn`),
because the cast table's foreign key needs the puppet catalogue those migrations seed.

(Moved here on 2026-11-18 from tests/server/test_replays.py, where it was skipped unless
`WW_REPLAY_TEST_DSN` named a database.)
"""
from __future__ import annotations

from datetime import datetime, timezone

import pytest
from sqlmodel import select

from server.database_models.game import COMPLETED, DROPPED, RUNNING, EventRow, GameRow
from server.db import Database
from server.schemas import events as ev
from server.storage.game_repository import GameRepository
from server.storage.replay_service import IncompleteReplay, ReplayNotFound, ReplayService
from tests.factories.builders import short_event_log as _log
from tests.fixtures.database import sqlalchemy_url


async def test_postgres_round_trip(server_tables_dsn):
    # Arrange: a real Postgres database with the server's tables, made by its migrations
    database = Database(sqlalchemy_url(server_tables_dsn))
    await database.startup()
    repository = GameRepository(database)
    replay_service = ReplayService(database)
    assert database.engine is not None

    # Round 1: write and update a game row, and record its events twice
    assert await repository.create_game(
        "itest-game", status=RUNNING, model="test-model", seats=[{"token": "test-seat"}])
    # A partial write must update the existing row without needing its required status.
    assert await repository.update_game("itest-game", human_players=["player_3"])
    row = await repository.load_game("itest-game")
    assert row.status == RUNNING and row.human_players == ["player_3"]
    assert row.model == "test-model" and row.seats == [{"token": "test-seat"}]
    assert not await repository.update_game("missing-game", human_players=["player_3"])
    assert await repository.load_game("missing-game") is None
    assert await repository.record_events("itest-game", _log())
    assert await repository.record_events("itest-game", _log())  # retry cannot duplicate rows

    # Round 2: record the game's cast
    # The cast goes with the game: written once, listed in seat order, and the
    # constraints refuse a puppet standing twice or one the catalogue never issued.
    from sqlalchemy.exc import IntegrityError

    from server.game.cast import CastSeat

    cast = [CastSeat("player_2", "owl", False), CastSeat("player_1", "whale", True)]
    assert await repository.record_cast("itest-game", cast)
    assert await repository.record_cast("itest-game", cast)  # retry cannot duplicate rows
    assert await repository.load_cast("itest-game") == [cast[1], cast[0]]
    assert not await repository.record_cast(
        "itest-game", [CastSeat("player_3", "owl", False)])  # owl stands at player_2
    assert not await repository.record_cast(
        "itest-game", [CastSeat("player_3", "nobody", False)])  # not in the catalogue

    # Round 3: complete the game twice, then read it back as a replay
    await repository.complete_game("itest-game", _log(), n_humans=2)
    await repository.complete_game("itest-game", _log(), n_humans=2)  # idempotent

    summary = await replay_service.list_replays(limit=50, offset=0)
    game = await replay_service.get_replay("itest-game")
    assert game.cast == ["whale", "owl"]
    assert any(item.game_id == "itest-game" for item in summary)
    assert await replay_service.count_replays() >= 1
    assert game.winner == "wolves" and len(game.events) == 3

    async with database.session() as sess:
        row = await sess.get(GameRow, "itest-game")
        event_rows = (await sess.execute(
            select(EventRow).where(EventRow.game_id == "itest-game")
        )).scalars().all()
    assert row is not None and row.status == COMPLETED and row.winner == "wolves"
    assert len(event_rows) == 3

    # Round 4: a draw
    # A draw has no winner and is a replay all the same (2026-10-17, game f2e944a3).
    draw = [*_log(with_over=False), ev.GameOver(seq=3, day=3, winner=None)]
    await repository.create_game("itest-draw", status=RUNNING)
    await repository.record_events("itest-draw", draw)
    await repository.complete_game("itest-draw", draw, n_humans=1)
    assert (await replay_service.get_replay("itest-draw")).winner is None
    assert any(item.game_id == "itest-draw"
               for item in await replay_service.list_replays(limit=500, offset=0))

    # Round 5: a game that lost a batch of events
    # A batch was lost during play: completion marks the game dropped, not completed.
    await repository.create_game("itest-short", status=RUNNING)
    await repository.record_events("itest-short", _log()[:2])
    await repository.complete_game("itest-short", _log(), n_humans=0)
    async with database.session() as sess:
        short = await sess.get(GameRow, "itest-short")
    assert short is not None and short.status == DROPPED
    assert short.error == "event log incomplete: 2 of 3 events stored, last seq 2"
    with pytest.raises(ReplayNotFound):
        await replay_service.get_replay("itest-short")

    # Round 6: a completed row with a hole in its event log
    # A row completed before the write-side check, with a hole: the read side refuses.
    full = _log()
    await repository.create_game(
        "itest-holed", status=COMPLETED, finished_at=datetime.now(timezone.utc),
        winner="wolves", days=3, n_events=2, n_humans=0, cast_role_counts={"wolf": 1})
    await repository.record_events("itest-holed", [full[0], full[2]])
    with pytest.raises(IncompleteReplay):
        await replay_service.get_replay("itest-holed")
    await database.close()
