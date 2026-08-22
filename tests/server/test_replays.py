"""Completed-game replay DTOs and the normalized read API.

Hermetic by construction: the autouse guard in tests/fixtures/server.py blanks
WW_POSTGRES_DSN, so nothing here can touch the live tick database. The hook tests
inject a small archive fake (the seam the session calls); the endpoint
tests run against the real router with the unconfigured-503 path, plus a recorded
fake for the storage calls. Real-Postgres coverage is one integration test gated on
WW_REPLAY_TEST_DSN — an explicitly separate opt-in var, never the live DSN.
"""
from __future__ import annotations

import os

import pytest
from sqlmodel import select

from server.database_models.game import COMPLETED, RUNNING, EventRow, GameRow
from server.db import Database
from server.game_repository import GameRepository
from server.replay_service import IncompleteReplay, ReplayNotFound, ReplayService
from server.schemas import events as ev
from server.schemas.replays import ReplayBase, ReplayGame

def _log(*, with_over=True):
    events: list[ev.DurableEvent] = [
        ev.GameStarted(seq=1, day=1, seats=["p1", "p2"],
                       cast_role_counts={"wolf": 1, "villager": 1}),
        ev.GmMessage(seq=2, day=2, channel_seq=0, text="dawn"),
    ]
    if with_over:
        events.append(ev.GameOver(seq=3, day=3, winner="wolves"))
    return events

# ---- the read API ---------------------------------------------------------------------------


def test_replays_answer_503_when_unconfigured(api_client):
    # Loud, not an empty-list lie (ruled): the autouse guard blanks the DSN.
    assert api_client.get("/replays").status_code == 503
    assert api_client.get("/replays/some-id").status_code == 503


def test_replay_router_translates_service_errors(api_client):
    """Application errors become HTTP responses only at the route boundary."""

    class MissingReplayService:
        async def get_replay(self, game_id: str):
            raise ReplayNotFound(game_id)

    api_client.app.state.resources.replays = MissingReplayService()
    response = api_client.get("/replays/missing")
    assert response.status_code == 404
    assert response.json()["detail"] == "unknown replay"

    class IncompleteReplayService:
        async def get_replay(self, game_id: str):
            raise IncompleteReplay(game_id)

    api_client.app.state.resources.replays = IncompleteReplayService()
    response = api_client.get("/replays/broken")
    assert response.status_code == 500
    assert response.json()["detail"] == "incomplete replay event log"


# ---- the wire model: typed events (ruled 2026-08-20, the frontend codegen contract) --------


def test_replay_game_parses_stored_dicts_into_typed_events():
    # EventRow keeps one payload dict; the wire model re-validates the collected
    # payloads through the discriminated union before they cross the API boundary.
    raw = [e.model_dump(mode="json") for e in _log()]
    game = ReplayGame(game_id="g", winner="wolves", days=3, n_events=3,
                      n_humans=0, cast_role_counts={"wolf": 1}, events=raw)
    assert isinstance(game.events[0], ev.GameStarted)
    assert isinstance(game.events[-1], ev.GameOver)

    with pytest.raises(Exception):  # unknown discriminator = drifted row, never served
        ReplayGame(game_id="g", winner="wolves", days=1, n_events=1,
                   n_humans=0, cast_role_counts={},
                           events=[{"type": "not_an_event", "seq": 1, "day": 1}])


def test_replay_dto_drops_private_game_row_fields():
    row = GameRow(
        game_id="g",
        status=COMPLETED,
        host_key="private-host-key",
        seats=[{"name": "hao", "token": "private-seat-token"}],
        winner="wolves",
        days=3,
        n_events=3,
        n_humans=1,
        cast_role_counts={"wolf": 1},
    )
    dto = ReplayBase.model_validate(row)
    assert dto.model_dump() == {
        "game_id": "g",
        "finished_at": None,
        "winner": "wolves",
        "days": 3,
        "n_events": 3,
        "n_humans": 1,
        "cast_role_counts": {"wolf": 1},
    }


def test_database_metadata_has_one_game_table_and_normalized_events():
    from sqlmodel import SQLModel

    assert set(SQLModel.metadata.tables) == {"games", "events"}
    assert "replays" not in SQLModel.metadata.tables
    event_fk = next(iter(SQLModel.metadata.tables["events"].foreign_keys))
    assert event_fk.target_fullname == "games.game_id"
    assert event_fk.ondelete == "CASCADE"


def test_event_union_reaches_openapi():
    # The whole point of the typed field: the frontend's TS event types are generated
    # from /openapi.json, so every union member must appear there as a oneOf ref.
    from typing import get_args

    from server.app import create_app

    items = (create_app().openapi()["components"]["schemas"]
             ["ReplayGame"]["properties"]["events"]["items"])
    n_members = len(get_args(get_args(ev.DurableGameEvent)[0]))
    assert len(items["oneOf"]) == n_members


# ---- optional integration (explicit opt-in var; NEVER the live DSN) -------------------------


@pytest.mark.skipif(not os.getenv("WW_REPLAY_TEST_DSN"),
                    reason="set WW_REPLAY_TEST_DSN to run the real-Postgres round-trip")
async def test_postgres_round_trip():
    from server.config import ServerSettings

    from sqlmodel import SQLModel

    settings = ServerSettings(WW_POSTGRES_DSN=os.environ["WW_REPLAY_TEST_DSN"])
    database = Database(settings.replay_database_url)
    await database.startup()
    repository = GameRepository(database)
    replay_service = ReplayService(database)
    assert database.engine is not None
    async with database.engine.begin() as conn:  # test-only; prod uses alembic
        await conn.run_sync(SQLModel.metadata.create_all)

    await repository.upsert_game("itest-game", status=RUNNING)
    await repository.record_events("itest-game", _log())
    await repository.complete_game("itest-game", _log(), n_humans=2)
    await repository.complete_game("itest-game", _log(), n_humans=2)  # idempotent

    summary = await replay_service.list_replays(limit=50, offset=0)
    game = await replay_service.get_replay("itest-game")
    assert any(item.game_id == "itest-game" for item in summary)
    assert game.winner == "wolves" and len(game.events) == 3

    async with database.session() as sess:
        row = await sess.get(GameRow, "itest-game")
        event_rows = (await sess.execute(
            select(EventRow).where(EventRow.game_id == "itest-game")
        )).scalars().all()
    assert row is not None and row.status == COMPLETED and row.winner == "wolves"
    assert len(event_rows) == 3
    await database.close()
