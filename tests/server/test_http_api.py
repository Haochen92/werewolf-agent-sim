"""The HTTP surface through a real TestClient: routing, validation, serialization, CORS.

API-layer tests in the dota2pred sense — the app is real (factory, lifespan, registry,
middleware), the game engine is not involved. Sessions are injected into
app.state.games pre-built (never started via POST /games, which would launch the real
graph); the runtime machine itself is pinned in test_server_runtime.py.
"""
from __future__ import annotations

from server.lobby import MAX_HUMAN_SEATS
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
    assert api_client.post("/games/nope/join", json={}).status_code == 404
    assert api_client.post("/games/nope/start").status_code == 404


def test_status_snapshot_of_a_fresh_session(api_client, quiet_session):
    session = quiet_session(FakeGraph([]))  # built, deliberately never started
    api_client.app.state.games[session.game_id] = session

    body = api_client.get(f"/games/{session.game_id}").json()
    assert body == {
        "game_id": session.game_id, "state": "running", "players": [], "max_seats": 0,
        "human_players": [], "pending_input": False, "pending_seats": [],
        "game_over": False, "last_seq": 0, "alive_role_counts": {}, "error": None,
    }


def test_turn_without_a_pending_request_is_409(api_client, quiet_session):
    session = quiet_session(FakeGraph([]))
    api_client.app.state.games[session.game_id] = session

    r = api_client.post(f"/games/{session.game_id}/turns", json={"message": "hi"})
    assert r.status_code == 409
    assert "no pending input_request" in r.json()["detail"]


# ---- the lobby: create -> join -> start (slice 2) ----------------------------------------

def _make_lobby(api_client, **extra):
    body = api_client.post("/games", json={"lobby": True, **extra}).json()
    return body["game_id"], body["host_key"]


def test_lobby_lifecycle_create_join_start(api_client, monkeypatch):
    """The happy path end to end, with the real GameSession swapped for one on a
    FakeGraph (starting the real graph would call an LLM)."""
    import server.app as app_mod
    from server import runtime as rt

    monkeypatch.setattr(rt, "seed_memory_from_config", lambda *a, **k: None)
    launched = []

    def fake_session(run, **kw):
        launched.append(run)
        return rt.GameSession(run, graph=FakeGraph([]), **kw)

    monkeypatch.setattr(app_mod, "GameSession", fake_session)

    game_id, host_key = _make_lobby(api_client)
    assert host_key  # the create response is the ONLY carrier of the host credential

    status = api_client.get(f"/games/{game_id}").json()
    assert (status["state"], status["players"]) == ("waiting", [])
    assert status["max_seats"] == MAX_HUMAN_SEATS  # the client's "room full" denominator

    r = api_client.post(f"/games/{game_id}/join", json={"name": "hao"})
    assert r.json() == {"position": 1}

    status = api_client.get(f"/games/{game_id}")
    assert status.json()["players"] == ["hao"]
    assert host_key not in status.text  # the host credential never leaves the create response

    # Only the host may start; the swap keeps the id; rooms deal random seats
    # (role choice is solo-only, on the instant-start path).
    assert api_client.post(f"/games/{game_id}/start?host_key=wrong").status_code == 403
    r = api_client.post(f"/games/{game_id}/start?host_key={host_key}")
    assert r.json()["game_id"] == game_id
    run = launched[0]
    assert (run.game_id, run.human_player, run.human_role) == (game_id, 1, None)
    assert run.memory_persistence.dump_enabled is False  # served games are never mined

    assert api_client.get(f"/games/{game_id}").json()["state"] == "running"
    # The room is gone: joining or re-starting a started game is a state conflict.
    assert api_client.post(f"/games/{game_id}/start?host_key={host_key}").status_code == 409
    assert api_client.post(f"/games/{game_id}/join", json={}).status_code == 409


def test_lobby_seat_cap(api_client):
    game_id, _ = _make_lobby(api_client)

    for i in range(MAX_HUMAN_SEATS):
        assert api_client.post(f"/games/{game_id}/join",
                               json={"name": f"p{i}"}).status_code == 200
    r = api_client.post(f"/games/{game_id}/join", json={"name": "late"})
    assert r.status_code == 409 and "seats are taken" in r.json()["detail"]


def test_lobby_blocks_turns_and_events_until_started(api_client):
    game_id, _ = _make_lobby(api_client)

    r = api_client.post(f"/games/{game_id}/turns", json={"message": "hi"})
    assert r.status_code == 409 and "not started" in r.json()["detail"]
    assert api_client.get(f"/games/{game_id}/events").status_code == 409


def test_lobby_rejects_instant_start_human_fields(api_client):
    r = api_client.post("/games", json={"lobby": True, "human": True})
    assert r.status_code == 422
    assert "via POST /join" in r.json()["detail"]


def test_start_without_joiners_runs_an_llm_only_game(api_client, monkeypatch):
    """An empty room may start: the host runs an all-LLM exhibition game to watch."""
    import server.app as app_mod
    from server import runtime as rt

    monkeypatch.setattr(rt, "seed_memory_from_config", lambda *a, **k: None)
    launched = []

    def fake_session(run, **kw):
        launched.append(run)
        return rt.GameSession(run, graph=FakeGraph([]), **kw)

    monkeypatch.setattr(app_mod, "GameSession", fake_session)

    game_id, host_key = _make_lobby(api_client)
    assert api_client.post(f"/games/{game_id}/start?host_key={host_key}").status_code == 200
    assert (launched[0].human_player, launched[0].human_role) == (0, None)


def test_lobby_carries_byok_to_the_session(api_client, monkeypatch):
    """The creator's key/model, given at create time, funds the started game."""
    import server.app as app_mod
    from server import runtime as rt

    monkeypatch.setattr(rt, "seed_memory_from_config", lambda *a, **k: None)
    seen = {}

    def fake_session(run, *, api_key="", model="", **kw):
        seen.update(api_key=api_key, model=model)
        return rt.GameSession(run, graph=FakeGraph([]), **kw)

    monkeypatch.setattr(app_mod, "GameSession", fake_session)

    game_id, host_key = _make_lobby(api_client, api_key="sk-room", model=GEMINI)
    api_client.post(f"/games/{game_id}/start?host_key={host_key}")
    assert seen == {"api_key": "sk-room", "model": GEMINI}
