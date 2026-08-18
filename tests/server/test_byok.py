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

from Agents.llm_factory import GAME_LLM, GameLLM, get_llm_game_fallback
from Agents.llm_factory.backends import create_chat_model
from server.runtime import SUPPORTED_GAME_MODELS

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
    client_a = _with_override(
        GameLLM(api_key="byok-key-A", model=GEMINI),
        lambda: create_chat_model(GEMINI, temperature=0.42))
    same_a = _with_override(
        GameLLM(api_key="byok-key-A", model=GEMINI),
        lambda: create_chat_model(GEMINI, temperature=0.42))
    client_b = _with_override(
        GameLLM(api_key="byok-key-B", model=GEMINI),
        lambda: create_chat_model(GEMINI, temperature=0.42))

    assert client_a is same_a  # memoized within a key
    assert client_b is not client_a  # same args, different key -> different client
    assert client_a.google_api_key.get_secret_value() == "byok-key-A"
    assert client_b.google_api_key.get_secret_value() == "byok-key-B"


def test_deepseek_selection_routes_the_key_to_deepseek():
    client = _with_override(
        GameLLM(api_key="ds-key-1", model=DEEPSEEK),
        lambda: create_chat_model(DEEPSEEK, temperature=0.42))
    assert client.openai_api_key.get_secret_value() == "ds-key-1"
    assert "deepseek" in str(client.openai_api_base)


def test_off_family_models_never_receive_the_game_key():
    # A DeepSeek game's key must not leak into a Gemini-family client (e.g. the pro
    # extraction models) — those fall back to server credentials.
    client = _with_override(
        GameLLM(api_key="ds-key-2", model=DEEPSEEK),
        lambda: create_chat_model("gemini-2.5-pro", temperature=0.42))
    google_key = getattr(client, "google_api_key", None)
    if google_key is not None and google_key:  # vertex builds carry no key at all
        assert google_key.get_secret_value() != "ds-key-2"


# ---- rescue: derived from the registry, same credential ----------------------------------

def test_rescue_follows_the_registry_row():
    gemini_rescue = _with_override(
        GameLLM(api_key="k", model=GEMINI,
                rescue_model=SUPPORTED_GAME_MODELS[GEMINI].rescue),
        get_llm_game_fallback)
    assert gemini_rescue is not None
    assert gemini_rescue.model == SUPPORTED_GAME_MODELS[GEMINI].rescue
    assert gemini_rescue.google_api_key.get_secret_value() == "k"  # same credential

    deepseek_rescue = _with_override(
        GameLLM(api_key="k", model=DEEPSEEK,
                rescue_model=SUPPORTED_GAME_MODELS[DEEPSEEK].rescue),
        get_llm_game_fallback)
    assert deepseek_rescue is None  # no tested same-credential rescue -> no rescue


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
    graph = _SelectionEchoGraph()
    session = quiet_session(graph, api_key="sk-player-123", model=DEEPSEEK)
    session.start()
    await asyncio.wait_for(session.wait_finished(), timeout=10)

    assert graph.seen == GameLLM(api_key="sk-player-123", model=DEEPSEEK,
                                 rescue_model=None)
    assert GAME_LLM.get() == GameLLM()  # task-local: the caller's context is untouched


async def test_bare_key_runs_the_default_registry_model(quiet_session):
    graph = _SelectionEchoGraph()
    session = quiet_session(graph, api_key="sk-player-123")
    session.start()
    await asyncio.wait_for(session.wait_finished(), timeout=10)

    assert graph.seen.model == next(iter(SUPPORTED_GAME_MODELS))
    assert graph.seen.rescue_model == SUPPORTED_GAME_MODELS[graph.seen.model].rescue


# ---- failure: surfaced, but redacted ------------------------------------------------------

class _AuthBoomGraph:
    async def astream(self, payload, *, config, context, stream_mode, subgraphs, version):
        raise ValueError("401: API key not valid: sk-player-123")
        yield


async def test_dead_game_error_never_echoes_the_key(quiet_session):
    session = quiet_session(_AuthBoomGraph(), api_key="sk-player-123")
    session.start()
    await asyncio.wait_for(session.wait_finished(), timeout=10)

    assert session.error is not None  # surfaced: the player restarts with a valid key
    assert "sk-player-123" not in session.error
    assert "***" in session.error
