"""The HTTP surface through a real TestClient: routing, validation, serialization, CORS.

API-layer tests in the dota2pred sense — the app is real (factory, lifespan, registry,
middleware), the game engine is not involved. Sessions are injected into
app.state.games pre-built (never started via POST /games, which would launch the real
graph); the runtime machine itself is pinned in test_server_runtime.py.
"""
from __future__ import annotations

import pytest

from server.lobby import MAX_HUMAN_SEATS
from server.runtime import SUPPORTED_GAME_MODELS
from tests.fixtures.server import FakeGraph

GEMINI = "gemini-3.1-flash-lite"


@pytest.fixture
def seated_session(api_client, quiet_session):
    """A running session with one proven human seat: token registered with the
    session, seats already dealt, and the cookie on the client — the state a real
    joiner is in mid-game. Returns (session, token)."""
    session = quiet_session(FakeGraph([]), seat_tokens=["tok-1"])
    session.human_players = ["player_3"]  # what INITIALIZE_GAME would set
    api_client.app.state.games[session.game_id] = session
    api_client.cookies.set(f"seat_{session.game_id}", "tok-1")
    return session, "tok-1"


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

def test_model_selection_without_a_key_is_rejected_at_both_doors(api_client):
    for door in ("/games", "/rooms"):
        r = api_client.post(door, json={"model": GEMINI})
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
    assert api_client.post("/games/nope/rejoin", json={"token": "t"}).status_code == 404
    assert api_client.post("/games/nope/start").status_code == 404


def test_status_snapshot_of_a_fresh_session(api_client, quiet_session):
    session = quiet_session(FakeGraph([]))  # built, deliberately never started
    api_client.app.state.games[session.game_id] = session

    body = api_client.get(f"/games/{session.game_id}").json()
    assert body == {
        "game_id": session.game_id, "state": "running", "players": [], "max_seats": 0,
        "human_players": [], "you": None, "pending_input": False, "pending_seats": [],
        "game_over": False, "last_seq": 0, "alive_role_counts": {}, "error": None,
    }


def test_turn_without_a_pending_request_is_409(api_client, seated_session):
    session, _ = seated_session

    r = api_client.post(f"/games/{session.game_id}/turns", json={"message": "hi"})
    assert r.status_code == 409
    assert "no pending input_request" in r.json()["detail"]


# ---- the lobby: create -> join -> start (slice 2) ----------------------------------------

def _make_room(api_client, **extra):
    body = api_client.post("/rooms", json=extra).json()
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

    game_id, host_key = _make_room(api_client)
    assert host_key  # the create response is the ONLY carrier of the host credential

    status = api_client.get(f"/games/{game_id}").json()
    assert (status["state"], status["players"]) == ("waiting", [])
    assert status["max_seats"] == MAX_HUMAN_SEATS  # the client's "room full" denominator

    r = api_client.post(f"/games/{game_id}/join", json={"name": "hao"})
    seat_token = r.json()["token"]
    assert r.json() == {"position": 1, "token": seat_token}

    status = api_client.get(f"/games/{game_id}")
    assert status.json()["players"] == ["hao"]
    assert host_key not in status.text  # the host credential never leaves the create response
    assert seat_token not in status.text  # seat secrets never ride the public snapshot

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
    game_id, _ = _make_room(api_client)

    for i in range(MAX_HUMAN_SEATS):
        assert api_client.post(f"/games/{game_id}/join",
                               json={"name": f"p{i}"}).status_code == 200
    r = api_client.post(f"/games/{game_id}/join", json={"name": "late"})
    assert r.status_code == 409 and "seats are taken" in r.json()["detail"]


def test_lobby_blocks_turns_and_events_until_started(api_client):
    game_id, _ = _make_room(api_client)

    r = api_client.post(f"/games/{game_id}/turns", json={"message": "hi"})
    assert r.status_code == 409 and "not started" in r.json()["detail"]
    assert api_client.get(f"/games/{game_id}/events").status_code == 409


def test_room_contract_has_no_human_fields(api_client):
    # Not a hand-written guard: NewRoom simply has no human/role fields and forbids
    # extras, so instant-start fields sent to /rooms fail schema validation.
    assert api_client.post("/rooms", json={"human": True}).status_code == 422
    assert api_client.post("/rooms", json={"human_role": "wolf"}).status_code == 422


# ---- seat tokens: proof of ownership (slice 3) -------------------------------------------

def test_join_sets_an_httponly_seat_cookie_matching_the_body_token(api_client):
    game_id, _ = _make_room(api_client)

    r = api_client.post(f"/games/{game_id}/join", json={"name": "hao"})
    token = r.json()["token"]
    set_cookie = r.headers["set-cookie"]
    assert token and api_client.cookies.get(f"seat_{game_id}") == token
    assert "HttpOnly" in set_cookie          # out of page JavaScript's reach
    assert f"Path=/games/{game_id}" in set_cookie  # rides only this game's requests
    assert "SameSite=lax" in set_cookie


def test_turns_demand_a_proven_seat(api_client, seated_session):
    session, _ = seated_session
    url = f"/games/{session.game_id}/turns"

    api_client.cookies.clear()  # no cookie at all
    r = api_client.post(url, json={"message": "hi"})
    assert r.status_code == 403 and "seat cookie" in r.json()["detail"]

    api_client.cookies.set(f"seat_{session.game_id}", "forged")
    r = api_client.post(url, json={"message": "hi"})
    assert r.status_code == 403 and "unknown seat token" in r.json()["detail"]


def test_events_and_status_reject_a_forged_cookie(api_client, seated_session):
    session, _ = seated_session
    api_client.cookies.set(f"seat_{session.game_id}", "forged")

    assert api_client.get(f"/games/{session.game_id}/events").status_code == 403
    assert api_client.get(f"/games/{session.game_id}").status_code == 403


def test_status_resolves_you_from_the_cookie(api_client, seated_session):
    session, _ = seated_session
    assert api_client.get(f"/games/{session.game_id}").json()["you"] == "player_3"

    api_client.cookies.clear()  # spectators get the same snapshot, minus identity
    assert api_client.get(f"/games/{session.game_id}").json()["you"] is None


def test_rejoin_restores_a_lost_cookie_in_both_phases(api_client, seated_session):
    # Waiting room: the stashed body-copy token re-proves the seat.
    game_id, _ = _make_room(api_client)
    token = api_client.post(f"/games/{game_id}/join", json={"name": "hao"}).json()["token"]
    api_client.cookies.clear()  # the "new device" moment

    r = api_client.post(f"/games/{game_id}/rejoin", json={"token": token})
    assert r.json() == {"position": 1, "token": token}
    assert api_client.cookies.get(f"seat_{game_id}") == token

    assert api_client.post(f"/games/{game_id}/rejoin",
                           json={"token": "forged"}).status_code == 403

    # Running game: same door, served by GameSession.position_of.
    session, seat_token = seated_session
    api_client.cookies.clear()
    r = api_client.post(f"/games/{session.game_id}/rejoin", json={"token": seat_token})
    assert r.json() == {"position": 1, "token": seat_token}
    assert api_client.get(f"/games/{session.game_id}").json()["you"] == "player_3"


def test_solo_door_mints_the_same_seat_identity(api_client, monkeypatch):
    """POST /games {human} gets a token + cookie exactly like a room joiner (one
    identity mechanism at both doors); an LLM-only game mints nothing."""
    import server.app as app_mod
    from server import runtime as rt

    monkeypatch.setattr(rt, "seed_memory_from_config", lambda *a, **k: None)
    launched = []

    def fake_session(run, **kw):
        launched.append((run, kw))
        return rt.GameSession(run, graph=FakeGraph([]), **kw)

    monkeypatch.setattr(app_mod, "GameSession", fake_session)

    r = api_client.post("/games", json={"human": True})
    body = r.json()
    assert body["seat_token"]
    assert api_client.cookies.get(f"seat_{body['game_id']}") == body["seat_token"]
    assert launched[0][0].human_player == 1
    assert launched[0][1]["seat_tokens"] == [body["seat_token"]]

    api_client.cookies.clear()
    r = api_client.post("/games", json={})
    assert r.json()["seat_token"] is None
    assert "set-cookie" not in r.headers
    assert launched[1][0].human_player == 0


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

    game_id, host_key = _make_room(api_client)
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

    game_id, host_key = _make_room(api_client, api_key="sk-room", model=GEMINI)
    api_client.post(f"/games/{game_id}/start?host_key={host_key}")
    assert seen == {"api_key": "sk-room", "model": GEMINI}
