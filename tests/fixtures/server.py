"""Server-layer fixtures, by test level (the dota2pred hierarchy, scaled to one domain):

1. RUNTIME TESTS (the session machine): use `quiet_session` — a factory for a real
   GameSession over an injected fake graph (zero LLM), memory seeding silenced.
   Example: session = quiet_session(FakeGraph(parts))
2. API-LAYER TESTS (routing, validation, serialization): use `api_client` — a
   TestClient over the real create_app() (real lifespan, real registry). Inject
   prepared sessions via `api_client.app.state.games[id] = session`; never POST
   /games for a success path here — that would launch the real graph.
"""

from __future__ import annotations

import pytest
from starlette.testclient import TestClient

from Agents.config import RunConfig
from server import runtime as rt
from server.app import create_app
from server.runtime import GameSession


class FakeGraph:
    """Yields scripted phases: phase 1, then (after each resume) the next phase."""

    def __init__(self, *phases):
        self.phases = list(phases)
        self.calls = []

    async def astream(self, payload, *, config, context, stream_mode, subgraphs, version):
        assert version == "v2" and subgraphs and stream_mode == ["updates", "custom"]
        self.calls.append(payload)
        for part in self.phases[len(self.calls) - 1]:
            yield part


class HangingGraph:
    """Parks forever without yielding — a stalled provider, for cancellation tests."""

    async def astream(self, payload, **_):
        import asyncio

        await asyncio.Event().wait()
        yield


@pytest.fixture(autouse=True)
def _no_real_replay_db():
    """Hermetic guard: the dev .env carries the LIVE WW_POSTGRES_DSN (the memory
    tick's database), and any test that finishes a game cleanly triggers the archive
    hook — without this, tests would write real rows. Force the archive layer
    unconfigured everywhere; a test that wants a database opts in explicitly.

    Deliberately NOT via the monkeypatch fixture: an autouse dependency on it changes
    fixture teardown order so the api_client lifespan would exit while a test's own
    GameSession patch is still applied (isinstance TypeError at shutdown)."""
    from server import db

    old = db.server_settings.WW_POSTGRES_DSN
    db.server_settings.WW_POSTGRES_DSN = ""
    db._engine = None
    db._sessions = None
    yield
    db.server_settings.WW_POSTGRES_DSN = old
    db._engine = None
    db._sessions = None


@pytest.fixture
def quiet_session(monkeypatch):
    """GameSession factory with the memory-seeding side effect silenced."""
    monkeypatch.setattr(rt, "seed_memory_from_config", lambda *a, **k: None)

    def make(graph, api_key: str = "", model: str = "", **kw) -> GameSession:
        return GameSession(RunConfig(memory_persistence={"dump_enabled": False}),
                           api_key=api_key, model=model, graph=graph, **kw)

    return make


@pytest.fixture
def api_client():
    """TestClient over the real app factory; `with` runs the lifespan (registry +
    shutdown cancellation), so injected sessions are cleaned up like real ones."""
    with TestClient(create_app()) as client:
        yield client
