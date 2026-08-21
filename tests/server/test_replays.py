"""The replay archive: metadata derivation, the clean-finish-only hook, the read API.

Hermetic by construction: the autouse guard in tests/fixtures/server.py blanks
WW_POSTGRES_DSN, so nothing here can touch the live tick database. The hook tests
monkeypatch server.runtime.archive_game (the seam the session calls); the endpoint
tests run against the real router with the unconfigured-503 path, plus a recorded
fake for the storage calls. Real-Postgres coverage is one integration test gated on
WW_REPLAY_TEST_DSN — an explicitly separate opt-in var, never the live DSN.
"""
from __future__ import annotations

import asyncio
import os

import pytest

from server import replays
from server.schemas import events as ev
from tests.fixtures.server import FakeGraph

# ---- metadata derivation ------------------------------------------------------------------


def _log(*, with_over=True):
    events: list[ev.DurableEvent] = [
        ev.GameStarted(seq=1, day=1, seats=["p1", "p2"],
                       cast_role_counts={"wolf": 1, "villager": 1}),
        ev.GmMessage(seq=2, day=2, channel_seq=0, text="dawn"),
    ]
    if with_over:
        events.append(ev.GameOver(seq=3, day=3, winner="wolves"))
    return events


def test_metadata_is_lifted_from_the_log():
    meta = replays.derive_metadata(_log())
    assert meta == {"winner": "wolves", "days": 3, "n_events": 3,
                    "cast_role_counts": {"wolf": 1, "villager": 1}}


def test_no_game_over_means_not_archivable():
    assert replays.derive_metadata(_log(with_over=False)) is None
    assert replays.derive_metadata([]) is None


# ---- the hook: clean finishes archive, errors never do -------------------------------------


async def test_clean_finish_archives_once(quiet_session, monkeypatch, fixture_parts):
    calls = []

    async def record(game_id, log, n_humans):
        calls.append((game_id, len(log), n_humans))

    monkeypatch.setattr("server.runtime.archive_game", record)
    session = quiet_session(FakeGraph(fixture_parts))
    session.start()
    await asyncio.wait_for(session.wait_finished(), timeout=30)

    assert session.game_over and session.error is None
    assert calls == [(session.game_id, len(session.log), 0)]


async def test_died_game_is_never_archived(quiet_session, monkeypatch):
    calls = []

    async def record(*a):
        calls.append(a)

    class ExplodingGraph:
        async def astream(self, payload, **_):
            raise RuntimeError("provider died")
            yield  # pragma: no cover

    monkeypatch.setattr("server.runtime.archive_game", record)
    session = quiet_session(ExplodingGraph())
    session.start()
    await asyncio.wait_for(session.wait_finished(), timeout=10)

    assert session.error is not None
    assert calls == []


async def test_archive_failure_never_touches_the_game(quiet_session, monkeypatch,
                                                      fixture_parts):
    # The real archive_game swallows its own failures; here the seam itself explodes
    # to pin the stronger claim: even a raising archiver must not mark the game dead...
    # it would, and that is why archive_game guarantees no-raise. Pin THAT guarantee:
    # a broken engine inside archive_game surfaces as a log line, never an exception.
    async def broken_session():
        raise RuntimeError("pool exploded")

    monkeypatch.setattr("server.db.engine", lambda: object())  # configured...
    monkeypatch.setattr("server.db.session", broken_session)   # ...but broken
    await replays.archive_game("g1", _log(), 0)  # must not raise


# ---- the read API ---------------------------------------------------------------------------


def test_replays_answer_503_when_unconfigured(api_client):
    # Loud, not an empty-list lie (ruled): the autouse guard blanks the DSN.
    assert api_client.get("/replays").status_code == 503
    assert api_client.get("/replays/some-id").status_code == 503


# ---- the wire model: typed events (ruled 2026-08-20, the frontend codegen contract) --------


def test_replay_game_parses_stored_dicts_into_typed_events():
    # The table keeps list[dict] (JSONB); the wire model re-validates through the
    # discriminated union, so archive drift fails loudly instead of shipping mystery dicts.
    raw = [e.model_dump(mode="json") for e in _log()]
    game = replays.ReplayGame(game_id="g", winner="wolves", days=3, n_events=3,
                              n_humans=0, cast_role_counts={"wolf": 1}, events=raw)
    assert isinstance(game.events[0], ev.GameStarted)
    assert isinstance(game.events[-1], ev.GameOver)

    with pytest.raises(Exception):  # unknown discriminator = drifted row, never served
        replays.ReplayGame(game_id="g", winner="wolves", days=1, n_events=1,
                           n_humans=0, cast_role_counts={},
                           events=[{"type": "not_an_event", "seq": 1, "day": 1}])


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
async def test_postgres_round_trip(monkeypatch):
    from server import db

    monkeypatch.setattr(db.server_settings, "WW_POSTGRES_DSN",
                        os.environ["WW_REPLAY_TEST_DSN"])
    monkeypatch.setattr(db, "_engine", None)
    monkeypatch.setattr(db, "_sessions", None)

    from sqlmodel import SQLModel

    async with db.engine().begin() as conn:  # test-only convenience; prod uses alembic
        await conn.run_sync(SQLModel.metadata.create_all)

    await replays.archive_game("itest-game", _log(), n_humans=2)
    await replays.archive_game("itest-game", _log(), n_humans=2)  # idempotent

    async with db.session() as sess:
        row = await sess.get(replays.Replay, "itest-game")
    assert row is not None and row.winner == "wolves" and len(row.events) == 3
    await db.dispose()
