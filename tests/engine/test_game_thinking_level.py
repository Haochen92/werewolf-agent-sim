"""Each flash-lite game turn reasons at the level that makes it reason (discussion_evidence.md §6.7):
with structured output both flash-lites reason for 0 tokens at "minimal", and 3.5 also at "low"."""
from Agents.llm_factory import accessors
from Agents.llm_factory.backends import GAME_LLM, GameLLM


def _levels(monkeypatch, **override):
    seen = []
    monkeypatch.setattr(accessors, "create_chat_model", lambda model, **kw: seen.append((model, kw["thinking_level"])))
    monkeypatch.delenv("GOOGLE_GENAI_THINKING_LEVEL", raising=False)
    token = GAME_LLM.set(GameLLM(**override))
    try:
        accessors.get_llm()
        accessors.get_llm_game_fallback()
    finally:
        GAME_LLM.reset(token)
    return seen


def test_each_flash_lite_and_its_rescue_get_their_own_level(monkeypatch):
    assert _levels(monkeypatch, model="gemini-3.5-flash-lite", rescue_model="gemini-3.1-flash-lite") == [
        ("gemini-3.5-flash-lite", "medium"), ("gemini-3.1-flash-lite", "low")]
    assert _levels(monkeypatch, model="gemini-3.1-flash-lite", rescue_model="gemini-3.5-flash-lite") == [
        ("gemini-3.1-flash-lite", "low"), ("gemini-3.5-flash-lite", "medium")]


def test_other_models_keep_the_default_and_the_env_still_overrides(monkeypatch):
    assert accessors.game_thinking_level("gemini-3.6-flash") == "minimal"
    monkeypatch.setenv("GOOGLE_GENAI_THINKING_LEVEL", "minimal")
    assert accessors.game_thinking_level("gemini-3.5-flash-lite") == "minimal"
