"""Each flash-lite game turn reasons at the level that makes it reason (discussion_evidence.md §6.7):
with structured output both flash-lites reason for 0 tokens at "minimal", and 3.5 also at "low"."""
import importlib

from Agents.llm_factory import GameModels, accessors

# The module that builds a game's clients. The package also exports a function of the same name
# (`game_models`), which hides the module from a plain import.
game_models_mod = importlib.import_module("Agents.llm_factory.game_models")


def _levels(monkeypatch, **game):
    seen = []
    monkeypatch.setattr(game_models_mod, "create_chat_model", lambda model, **kw: seen.append((model, kw["thinking_level"])))
    monkeypatch.delenv("GOOGLE_GENAI_THINKING_LEVEL", raising=False)
    models = GameModels(**game)
    models.seat()
    models.seat_rescue()
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


def test_the_admitted_models_play_at_their_bench_levels_and_glm_summarises_without_thinking(monkeypatch):
    # Arrange: a model factory that records each model and its thinking level
    seen = []
    monkeypatch.setattr(game_models_mod, "create_chat_model", lambda model, **kw: seen.append((model, kw["thinking_level"])))
    monkeypatch.delenv("GOOGLE_GENAI_THINKING_LEVEL", raising=False)
    monkeypatch.delenv("GOOGLE_GENAI_SUMMARY_THINKING_LEVEL", raising=False)

    # Round 1: the levels the game's turns play at
    assert accessors.game_thinking_level("openai/gpt-6-luna") == "low"
    assert accessors.game_thinking_level("openrouter/z-ai/glm-5.3-flash") == "minimal"
    assert accessors.game_thinking_level("anthropic/claude-haiku-5-5") == "low"

    # Round 2: the summary model built for each of two game models
    for model in ("openrouter/z-ai/glm-5.3-flash", "openai/gpt-6-luna"):
        GameModels(model=model).summary()
    assert seen == [("openrouter/z-ai/glm-5.3-flash", "minimal"), ("openai/gpt-6-luna", "medium")]
