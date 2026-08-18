"""The HTTP surface through a real TestClient: routing, validation, serialization, CORS.

API-layer tests in the dota2pred sense — the app is real (factory, lifespan, registry,
middleware), the game engine is not involved. Sessions are injected into
app.state.games pre-built (never started via POST /games, which would launch the real
graph); the runtime machine itself is pinned in test_server_runtime.py.
"""
from __future__ import annotations

from server.runtime import SUPPORTED_GAME_MODELS
from tests.fixtures.server import FakeGraph

GEMINI = "gemini-3.1-flash-lite"


# ---- wiring: factory, lifespan registry, CORS -------------------------------------------

def test_health_and_lifespan_registry(api_client):
    assert api_client.get("/health").json() == {"status": "healthy"}
    assert api_client.app.state.games == {}  # the lifespan created the registry


def test_cors_allows_the_configured_frontend_origin(api_client):
    from server.config import server_settings

    origin = server_settings.cors_allowed_origins[0]
    r = api_client.get("/health", headers={"Origin": origin})
    assert r.headers["access-control-allow-origin"] == origin

    r = api_client.get("/health", headers={"Origin": "http://evil.example"})
    assert "access-control-allow-origin" not in r.headers


def test_models_menu_serves_the_registry(api_client):
    menu = api_client.get("/models").json()
    assert [m["model"] for m in menu["models"]] == list(SUPPORTED_GAME_MODELS)
    assert menu["models"][0]["rescue_model"]  # the default row carries its rescue


# ---- POST /games: the registry gate (BYOK v1.5) -----------------------------------------

def test_model_selection_without_a_key_is_rejected(api_client):
    r = api_client.post("/games", json={"model": GEMINI})
    assert r.status_code == 422
    assert "requires api_key" in r.json()["detail"]


def test_untested_models_are_rejected(api_client):
    r = api_client.post("/games", json={"api_key": "k", "model": "gpt-5"})
    assert r.status_code == 422
    assert "unsupported model" in r.json()["detail"]


# ---- per-game routes over an injected session -------------------------------------------

def test_unknown_game_is_404_everywhere(api_client):
    assert api_client.get("/games/nope").status_code == 404
    assert api_client.post("/games/nope/turns", json={}).status_code == 404


def test_status_snapshot_of_a_fresh_session(api_client, quiet_session):
    session = quiet_session(FakeGraph([]))  # built, deliberately never started
    api_client.app.state.games[session.game_id] = session

    body = api_client.get(f"/games/{session.game_id}").json()
    assert body == {
        "game_id": session.game_id, "human_player": "", "pending_input": False,
        "game_over": False, "last_seq": 0, "alive_role_counts": {}, "error": None,
    }


def test_turn_without_a_pending_request_is_409(api_client, quiet_session):
    session = quiet_session(FakeGraph([]))
    api_client.app.state.games[session.game_id] = session

    r = api_client.post(f"/games/{session.game_id}/turns", json={"message": "hi"})
    assert r.status_code == 409
    assert "no pending input_request" in r.json()["detail"]
