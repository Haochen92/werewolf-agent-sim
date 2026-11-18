"""BYOK pattern 2 (ephemeral pass-through): per-game (key, model) -> ContextVar -> factory.

The layers under test: the factory must key its client cache on the game key and apply it
ONLY to the selected model's provider family (an off-family call — e.g. a Gemini extraction
model during a DeepSeek game — must never receive the player's key); the session must set
the selection inside its own task (LangGraph's context copies deliver it to worker threads
without touching any node code); the rescue model must derive from the registry, same
credential as the primary; and a dying game must never echo the key through the
viewer-visible error field. The endpoint-level registry gate (422s) is pinned over HTTP
in test_http_api.py.
"""
from __future__ import annotations

import asyncio

from Agents.llm_factory import GAME_LLM, GameLLM, chat, get_llm_game_fallback
from Agents.llm_factory.chat import create_chat_model
from server.game.model_catalog import game_model, menu_models

GEMINI = "gemini-3.1-flash-lite"
DEEPSEEK = "deepseek/deepseek-v4-pro"


def _with_override(override: GameLLM, fn):
    token = GAME_LLM.set(override)
    try:
        return fn()
    finally:
        GAME_LLM.reset(token)


# ---- factory: cache keyed per game key, key applied per provider family ------------------

def test_factory_builds_isolated_clients_per_game_key():
    # Arrange
    game_a = GameLLM(api_key="byok-key-A", model=GEMINI)

    # Act: build a client twice for game A, and once for a game with a different key
    client_a = _with_override(game_a, lambda: create_chat_model(GEMINI, temperature=0.42))
    same_a = _with_override(game_a, lambda: create_chat_model(GEMINI, temperature=0.42))
    client_b = _with_override(
        GameLLM(api_key="byok-key-B", model=GEMINI),
        lambda: create_chat_model(GEMINI, temperature=0.42))

    # Assert
    assert client_a is same_a  # memoized within a game
    assert client_b is not client_a  # same args, different key -> different client
    assert client_a.google_api_key.get_secret_value() == "byok-key-A"
    assert client_b.google_api_key.get_secret_value() == "byok-key-B"


def test_a_players_key_is_cached_with_its_game_not_the_process():
    from Agents.llm_factory.chat import _MODEL_CACHE

    # Arrange
    game = GameLLM(api_key="byok-key-C", model=GEMINI)

    # Act
    client = _with_override(game, lambda: create_chat_model(GEMINI, temperature=0.43))

    # Assert
    assert client in game.clients.values()
    assert client not in _MODEL_CACHE.values()  # gone with the game, not kept until restart
    # Another game on the same key builds its own: nothing of one game's is handed to the next.
    again = _with_override(GameLLM(api_key="byok-key-C", model=GEMINI),
                           lambda: create_chat_model(GEMINI, temperature=0.43))
    assert again is not client


def test_deepseek_selection_routes_the_key_to_deepseek():
    client = _with_override(
        GameLLM(api_key="ds-key-1", model=DEEPSEEK),
        lambda: create_chat_model(DEEPSEEK, temperature=0.42))
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
        client = _with_override(GameLLM(api_key="player-key", model=model),
                                lambda: create_chat_model(model, temperature=0.42))
        assert client.openai_api_key.get_secret_value() == "player-key", model
        assert base in str(client.openai_api_base)


def test_off_family_models_never_receive_the_game_key(monkeypatch):
    # A DeepSeek game's key must not leak into a Gemini-family client (e.g. the pro
    # extraction models) — those fall back to server credentials.
    # Arrange
    monkeypatch.setenv("LLM_BACKEND", "google")  # the key-carrying build; Vertex carries no key
    monkeypatch.setenv("GOOGLE_API_KEY", "server-google-key")
    monkeypatch.setattr(chat, "_MODEL_CACHE", {})  # a client cached by an earlier test was built without a key
    game = GameLLM(api_key="ds-key-2", model=DEEPSEEK)

    # Act
    client = _with_override(game, lambda: create_chat_model("gemini-2.5-pro", temperature=0.42))

    # Assert
    assert client.google_api_key.get_secret_value() == "server-google-key"


# ---- rescue: derived from the registry, same credential ----------------------------------

def test_rescue_follows_the_registry_row():
    # Round 1: the rescue model of a Gemini game
    gemini_rescue = _with_override(
        GameLLM(api_key="k", model=GEMINI,
                rescue_model=game_model(GEMINI).rescue_model),
        get_llm_game_fallback)
    assert gemini_rescue is not None
    assert gemini_rescue.model == game_model(GEMINI).rescue_model
    assert gemini_rescue.google_api_key.get_secret_value() == "k"  # same credential

    # Round 2: the rescue model of a DeepSeek game
    deepseek_rescue = _with_override(
        GameLLM(api_key="k", model=DEEPSEEK,
                rescue_model=game_model(DEEPSEEK).rescue_model),
        get_llm_game_fallback)
    # The two DeepSeek models share one key, so each rescues the other on that same key.
    assert deepseek_rescue is not None
    # The factory strips the "deepseek/" backend prefix before it reaches the client.
    assert "deepseek/" + deepseek_rescue.model_name == game_model(DEEPSEEK).rescue_model
    assert deepseek_rescue.openai_api_key.get_secret_value() == "k"


# ---- session: the selection is set task-locally, invisible outside -----------------------

class _SelectionEchoGraph:
    """Records what GAME_LLM looks like from inside the game task."""

    def __init__(self):
        self.seen: GameLLM | None = None

    async def astream(self, payload, *, config, context, stream_mode, subgraphs, version):
        self.seen = GAME_LLM.get()
        return
        yield  # makes this an async generator


async def test_session_sets_the_selection_inside_its_own_task_only(quiet_session):
    # Arrange
    graph = _SelectionEchoGraph()
    session = quiet_session(graph, api_key="sk-player-123", model=DEEPSEEK)

    # Act: run the session to its end
    session.start()
    await asyncio.wait_for(session.wait_finished(), timeout=10)

    # Assert
    assert graph.seen == GameLLM(api_key="sk-player-123", model=DEEPSEEK,
                                 rescue_model=game_model(DEEPSEEK).rescue_model)
    assert GAME_LLM.get() == GameLLM()  # task-local: the caller's context is untouched


async def test_bare_key_runs_the_default_registry_model(quiet_session):
    # Arrange: a key with no model chosen
    graph = _SelectionEchoGraph()
    session = quiet_session(graph, api_key="sk-player-123")

    # Act: run the session to its end
    session.start()
    await asyncio.wait_for(session.wait_finished(), timeout=10)

    # Assert
    assert graph.seen.model == menu_models()[0].model
    assert graph.seen.rescue_model == game_model(graph.seen.model).rescue_model


async def test_house_model_selection_uses_server_credentials(quiet_session):
    # Arrange: a model chosen with no key, so the house pays
    graph = _SelectionEchoGraph()
    model = "gemini-3.6-flash"
    session = quiet_session(graph, model=model)

    # Act: run the session to its end
    session.start()
    await asyncio.wait_for(session.wait_finished(), timeout=10)

    # Assert
    assert graph.seen == GameLLM(
        model=model, rescue_model=game_model(model).rescue_model)


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
    game = GameLLM(api_key="ds-key-3", model=DEEPSEEK, rescue_model=HAIKU,
                   backup_key="sk-ant-backup")

    # Act: build the main client, the rescue client, and a client for a third company
    main = _with_override(game, lambda: create_chat_model(DEEPSEEK, temperature=0.44))
    rescue = _with_override(game, get_llm_game_fallback)
    other = _with_override(game, lambda: create_chat_model("openai/gpt-6-luna", temperature=1.0))

    # Assert
    assert main.openai_api_key.get_secret_value() == "ds-key-3"
    assert rescue.anthropic_api_key.get_secret_value() == "sk-ant-backup"
    assert rescue in game.clients.values()  # kept with the game, like the key's own clients
    assert other.openai_api_key.get_secret_value() == "server-openai-key"  # a third company
    assert "sk-ant-backup" not in repr(game)


def test_neither_key_shows_in_the_selections_printed_form():
    # Arrange
    game = GameLLM(api_key="sk-main-key", model=DEEPSEEK, rescue_model=HAIKU,
                   backup_key="sk-ant-backup")

    # Act and assert, for each way of printing the selection
    for shown in (repr(game), str(game), f"{game}"):
        assert "sk-main-key" not in shown
        assert "sk-ant-backup" not in shown
    assert DEEPSEEK in repr(game)  # the model is still shown, which is what a log line needs


async def test_session_runs_its_rescue_on_the_backup(quiet_session):
    # Arrange
    graph = _SelectionEchoGraph()
    session = quiet_session(graph, api_key="sk-player-123", model=DEEPSEEK,
                            backup_model=HAIKU, backup_key="sk-ant-backup")

    # Act: run the session to its end
    session.start()
    await asyncio.wait_for(session.wait_finished(), timeout=10)

    # Assert
    assert (graph.seen.rescue_model, graph.seen.backup_key) == (HAIKU, "sk-ant-backup")
    # the game is over: both keys are let go with it
    assert session._secrets == () and session._llm_selection.backup_key == ""


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
