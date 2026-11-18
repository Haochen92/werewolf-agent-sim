"""BYOK pattern 2 (ephemeral pass-through): per-game (key, model) -> the game's `GameModels`.

The layers under test: a game's models object must keep the clients built on the player's key
to itself and apply the key ONLY to the selected model's provider family (an off-family call —
e.g. a Gemini extraction model during a DeepSeek game — must never receive the player's key);
the session must hand that object to the engine in the graph context; the rescue model must
derive from the registry, same credential as the primary; the object must refuse to be saved
or copied; and a dying game must never echo the key through the viewer-visible error field.
The endpoint-level registry gate (422s) is pinned over HTTP in test_http_api.py.
"""
from __future__ import annotations

import asyncio
import copy
import pickle

import pytest

from Agents.llm_factory import GameModels, chat
from server.game.model_catalog import game_model, menu_models

GEMINI = "gemini-3.1-flash-lite"
DEEPSEEK = "deepseek/deepseek-v4-pro"


# ---- the game's models: clients kept per game, key applied per provider family ------------

def test_each_game_builds_its_own_clients_on_its_own_key():
    # Arrange
    game_a = GameModels(api_key="byok-key-A", model=GEMINI)
    game_b = GameModels(api_key="byok-key-B", model=GEMINI)

    # Act: build the seat's client twice for game A, and once for a game with a different key
    client_a = game_a.seat()
    same_a = game_a.seat()
    client_b = game_b.seat()

    # Assert
    assert client_a is same_a  # memoized within a game
    assert client_b is not client_a  # same model and settings, different key -> different client
    assert client_a.google_api_key.get_secret_value() == "byok-key-A"
    assert client_b.google_api_key.get_secret_value() == "byok-key-B"


def test_a_players_key_is_cached_with_its_game_not_the_process():
    from Agents.llm_factory.chat import _MODEL_CACHE

    # Arrange
    game = GameModels(api_key="byok-key-C", model=GEMINI)

    # Act
    client = game.seat()

    # Assert
    assert client in game._clients.values()
    assert client not in _MODEL_CACHE.values()  # gone with the game, not kept until restart
    # Another game on the same key builds its own: nothing of one game's is handed to the next.
    again = GameModels(api_key="byok-key-C", model=GEMINI).seat()
    assert again is not client


def test_deepseek_selection_routes_the_key_to_deepseek():
    client = GameModels(api_key="ds-key-1", model=DEEPSEEK).seat()
    assert client.openai_api_key.get_secret_value() == "ds-key-1"
    assert "deepseek" in str(client.openai_api_base)


def test_openai_and_openrouter_selections_route_the_key_to_their_provider(monkeypatch):
    # Arrange
    # The server's own keys are set too: a player's game must never fall back to them.
    monkeypatch.setenv("OPENAI_API_KEY", "server-openai-key")
    monkeypatch.setenv("OPENROUTER_API_KEY", "server-openrouter-key")

    # Act and assert, once for each provider
    for model, base in (("openai/gpt-6-luna", "api.openai.com"),
                        ("openrouter/z-ai/glm-5.3-flash", "openrouter.ai")):
        client = GameModels(api_key="player-key", model=model).seat()
        assert client.openai_api_key.get_secret_value() == "player-key", model
        assert base in str(client.openai_api_base)


def test_off_family_models_never_receive_the_game_key(monkeypatch):
    # A DeepSeek game's key must not leak into a Gemini-family client (e.g. the pro
    # extraction models) — those fall back to server credentials.
    # Arrange
    monkeypatch.setenv("LLM_BACKEND", "google")  # the key-carrying build; Vertex carries no key
    monkeypatch.setenv("GOOGLE_API_KEY", "server-google-key")
    monkeypatch.setattr(chat, "_MODEL_CACHE", {})  # a client cached by an earlier test was built without a key
    game = GameModels(api_key="ds-key-2", model=DEEPSEEK)

    # Act: the client the game builds for a model of another company than its own
    client = game._client("gemini-2.5-pro", temperature=0.42)

    # Assert
    assert game._key_for("gemini-2.5-pro") == ""
    assert client.google_api_key.get_secret_value() == "server-google-key"
    assert client not in game._clients.values()  # built on the server's key, so not the game's to keep


# ---- rescue: derived from the registry, same credential ----------------------------------

def test_rescue_follows_the_registry_row():
    # Round 1: the rescue model of a Gemini game
    gemini_rescue = GameModels(
        api_key="k", model=GEMINI, rescue_model=game_model(GEMINI).rescue_model).seat_rescue()
    assert gemini_rescue is not None
    assert gemini_rescue.model == game_model(GEMINI).rescue_model
    assert gemini_rescue.google_api_key.get_secret_value() == "k"  # same credential

    # Round 2: the rescue model of a DeepSeek game
    deepseek_rescue = GameModels(
        api_key="k", model=DEEPSEEK, rescue_model=game_model(DEEPSEEK).rescue_model).seat_rescue()
    # The two DeepSeek models share one key, so each rescues the other on that same key.
    assert deepseek_rescue is not None
    # The factory strips the "deepseek/" backend prefix before it reaches the client.
    assert "deepseek/" + deepseek_rescue.model_name == game_model(DEEPSEEK).rescue_model
    assert deepseek_rescue.openai_api_key.get_secret_value() == "k"


# ---- session: the game's models reach the engine in the graph context ---------------------

class _ContextRecordingGraph:
    """Records the models in the context the session drives the graph with."""

    def __init__(self):
        self.seen: GameModels | None = None

    async def astream(self, payload, *, config, context, stream_mode, subgraphs, version):
        self.seen = context["models"]
        return
        yield  # makes this an async generator


async def test_the_session_drives_the_graph_with_its_own_models_carrying_the_players_model_and_key(
        quiet_session):
    # Arrange
    graph = _ContextRecordingGraph()
    session = quiet_session(graph, api_key="sk-player-123", model=DEEPSEEK)
    sessions_models = session._models

    # Act: run the session to its end
    session.start()
    await asyncio.wait_for(session.wait_finished(), timeout=10)

    # Assert
    assert graph.seen is sessions_models  # the engine got the session's object, not a copy
    assert (graph.seen.model, graph.seen.rescue_model) == (DEEPSEEK, game_model(DEEPSEEK).rescue_model)
    assert graph.seen._key_for(DEEPSEEK) == "sk-player-123"
    assert graph.seen._backup_key == ""


async def test_bare_key_runs_the_default_registry_model(quiet_session):
    # Arrange: a key with no model chosen
    graph = _ContextRecordingGraph()
    session = quiet_session(graph, api_key="sk-player-123")

    # Act: run the session to its end
    session.start()
    await asyncio.wait_for(session.wait_finished(), timeout=10)

    # Assert
    assert graph.seen.model == menu_models()[0].model
    assert graph.seen.rescue_model == game_model(graph.seen.model).rescue_model


async def test_house_model_selection_uses_server_credentials(quiet_session):
    # Arrange: a model chosen with no key, so the house pays
    graph = _ContextRecordingGraph()
    model = "gemini-3.6-flash"
    session = quiet_session(graph, model=model)

    # Act: run the session to its end
    session.start()
    await asyncio.wait_for(session.wait_finished(), timeout=10)

    # Assert
    assert (graph.seen.model, graph.seen.rescue_model) == (model, game_model(model).rescue_model)
    assert (graph.seen._api_key, graph.seen._backup_key) == ("", "")
    assert graph.seen._key_for(model) == ""  # no player's key: the client is built on the server's


# ---- failure: surfaced, but redacted ------------------------------------------------------

class _KeyRejectedGraph:
    async def astream(self, payload, *, config, context, stream_mode, subgraphs, version):
        raise ValueError("401: API key not valid: sk-player-123")
        yield


async def test_dead_game_error_never_echoes_the_key(quiet_session):
    # Arrange: a graph that fails with an error that contains the player's key
    session = quiet_session(_KeyRejectedGraph(), api_key="sk-player-123")

    # Act: run the session until it dies
    session.start()
    await asyncio.wait_for(session.wait_finished(), timeout=10)

    # Assert
    assert session.error is not None  # surfaced: the player restarts with a valid key
    assert "sk-player-123" not in session.error
    assert "***" in session.error


# ---- backup key: a second company's key runs the rescue (2026-10-21) ------------------------

HAIKU = "anthropic/claude-haiku-5-5"


def test_the_backup_key_goes_to_the_rescues_company_only(monkeypatch):
    # Arrange: a DeepSeek game whose rescue belongs to another company, with a backup key for it
    monkeypatch.setenv("OPENAI_API_KEY", "server-openai-key")
    game = GameModels(api_key="ds-key-3", model=DEEPSEEK, rescue_model=HAIKU,
                      backup_key="sk-ant-backup")

    # Act: build the main client, the rescue client, and a client for a third company
    main = game.seat()
    rescue = game.seat_rescue()
    other = game._client("openai/gpt-6-luna", temperature=1.0)

    # Assert
    assert main.openai_api_key.get_secret_value() == "ds-key-3"
    assert rescue.anthropic_api_key.get_secret_value() == "sk-ant-backup"
    assert rescue in game._clients.values()  # kept with the game, like the key's own clients
    assert other.openai_api_key.get_secret_value() == "server-openai-key"  # a third company
    assert "sk-ant-backup" not in repr(game)


def test_neither_key_shows_in_the_printed_form_of_a_games_models():
    # Arrange
    game = GameModels(api_key="sk-main-key", model=DEEPSEEK, rescue_model=HAIKU,
                      backup_key="sk-ant-backup")

    # Act and assert, for each way of printing the object
    for shown in (repr(game), str(game), f"{game}"):
        assert "sk-main-key" not in shown
        assert "sk-ant-backup" not in shown
    assert DEEPSEEK in repr(game)  # the model is still shown, which is what a log line needs


@pytest.mark.parametrize("save_or_copy", [pickle.dumps, copy.deepcopy, copy.copy],
                         ids=["pickle", "deep copy", "copy"])
def test_a_games_models_refuse_to_be_saved_or_copied_and_the_refusal_shows_no_key(save_or_copy):
    """The object rides in the graph context beside state that is checkpointed. If a later change
    put it where a checkpoint or a copy reaches, the player's key would be written out with it."""
    # Arrange: a game holding both keys, with a client already built on the player's key
    game = GameModels(api_key="sk-main-key", model=DEEPSEEK, rescue_model=HAIKU,
                      backup_key="sk-ant-backup")
    game.seat()

    # Act
    with pytest.raises(TypeError, match="never saved or copied") as raised:
        save_or_copy(game)

    # Assert
    assert "sk-main-key" not in str(raised.value) and "sk-ant-backup" not in str(raised.value)
    assert "sk-main-key" not in repr(game) and "sk-ant-backup" not in repr(game)


async def test_session_runs_its_rescue_on_the_backup(quiet_session):
    # Arrange
    graph = _ContextRecordingGraph()
    session = quiet_session(graph, api_key="sk-player-123", model=DEEPSEEK,
                            backup_model=HAIKU, backup_key="sk-ant-backup")

    # Act: run the session to its end
    session.start()
    await asyncio.wait_for(session.wait_finished(), timeout=10)

    # Assert
    assert (graph.seen.rescue_model, graph.seen._backup_key) == (HAIKU, "sk-ant-backup")
    assert graph.seen._key_for(HAIKU) == "sk-ant-backup"
    # the game is over: both keys are let go with it, here and in the context the engine reads
    assert session._secrets == () and session._models._backup_key == ""
    assert session._context["models"] is session._models


class _BackupKeyRejectedGraph:
    async def astream(self, payload, *, config, context, stream_mode, subgraphs, version):
        raise ValueError("401: invalid x-api-key: sk-ant-backup")
        yield


async def test_dead_game_error_never_echoes_the_backup_key(quiet_session):
    # Arrange: a graph that fails with an error that contains the backup key
    session = quiet_session(_BackupKeyRejectedGraph(), api_key="sk-player-123", model=DEEPSEEK,
                            backup_model=HAIKU, backup_key="sk-ant-backup")

    # Act: run the session until it dies
    session.start()
    await asyncio.wait_for(session.wait_finished(), timeout=10)

    # Assert
    assert "sk-ant-backup" not in session.error and "***" in session.error
