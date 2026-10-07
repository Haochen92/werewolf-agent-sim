"""The retry-exhaustion model fallback: a failing primary seat is rescued by the fallback backend
before the random-action fallback fires; same-model configurations skip the rescue entirely.

Born from a live deepseek-v4-pro game (2026-07-26): unconstrained tool-calling backends emit
off-schema output that can exhaust every retry, and a random discussion turn is seat damage the
fallback model avoids.
"""

from langchain_core.runnables import RunnableLambda

from Agents.llm_factory import accessors
from Agents.prompts.day_discuss import VILLAGER_DAY_DISCUSS
from Agents.prompts.night import HEALER_NIGHT
from Agents.prompts.night import WOLF_NIGHT_DISCUSS
from Agents.schemas.game_events import DiscussionPassReason, FiringReason
from Agents.schemas.output import DayDiscussOutput, WolfNightDiscussOutput
from Agents.schemas.output import PlayerRead
from Agents.schemas.output import HealerOutput
from Agents.schemas.turn import ResolvedDayDiscussion, ResolvedWolfDiscussion
from Agents.turn import agent_player as agent_mod


class _BrokenLLM:
    def with_structured_output(self, _schema):
        def _boom(_input):
            raise ValueError("off-schema output")
        return RunnableLambda(_boom)


class _WorkingLLM:
    def __init__(self, result):
        self._result = result

    def with_structured_output(self, _schema):
        return RunnableLambda(lambda _input: self._result)


def _payload():
    return {
        "player_id": "player_1", "player_role": "healer", "current_day": 2,
        "surviving_players": ["player_2", "player_3"],
        "dead_roster": [], "cast_role_counts": {},
    }


def _result():
    return HealerOutput(
        strategy_verdicts=[], memory_applicability=[],
        reads=[PlayerRead(player=p, why="quiet", suspected_role="unclear", confidence="low")
               for p in ("player_2", "player_3")],
        updated_strategy="", healer_target="player_3",
    )


def test_fallback_model_rescues_an_exhausted_seat(monkeypatch, caplog):
    monkeypatch.setattr(agent_mod, "get_llm", lambda: _BrokenLLM())
    monkeypatch.setattr(agent_mod, "get_llm_game_fallback", lambda: _WorkingLLM(_result()))
    with caplog.at_level("WARNING"):
        out = agent_mod.run_agent(_payload(), HEALER_NIGHT, HealerOutput, "healer_target")
    assert out.entry == "player_3"
    assert any("rescued by the fallback model" in r.message for r in caplog.records)
    assert not any("random fallback" in r.message for r in caplog.records)


def test_no_fallback_model_still_degrades_to_random(monkeypatch, caplog):
    monkeypatch.setattr(agent_mod, "get_llm", lambda: _BrokenLLM())
    monkeypatch.setattr(agent_mod, "get_llm_game_fallback", lambda: None)
    with caplog.at_level("ERROR"):
        out = agent_mod.run_agent(_payload(), HEALER_NIGHT, HealerOutput, "healer_target")
    assert out.entry in ("player_2", "player_3")
    assert any("random fallback" in r.message for r in caplog.records)


def test_broken_fallback_still_degrades_to_random(monkeypatch):
    monkeypatch.setattr(agent_mod, "get_llm", lambda: _BrokenLLM())
    monkeypatch.setattr(agent_mod, "get_llm_game_fallback", lambda: _BrokenLLM())
    out = agent_mod.run_agent(_payload(), HEALER_NIGHT, HealerOutput, "healer_target")
    assert out.entry in ("player_2", "player_3")


def test_exhausted_day_discussion_records_technical_pass(monkeypatch, caplog):
    payload = {
        **_payload(),
        "day_channel": [],
        "day_summaries": [],
        "firing_reason": FiringReason(tier="reactive", owes=["player_2"]),
    }
    monkeypatch.setattr(agent_mod, "get_llm", lambda: _BrokenLLM())
    monkeypatch.setattr(agent_mod, "get_llm_game_fallback", lambda: _BrokenLLM())

    with caplog.at_level("ERROR"):
        out = agent_mod.run_agent(
            payload,
            VILLAGER_DAY_DISCUSS,
            DayDiscussOutput,
            "day_channel",
        )

    assert isinstance(out, ResolvedDayDiscussion)
    assert out.entry is not None
    assert out.entry.passed is True
    assert out.entry.pass_reason == DiscussionPassReason.GENERATION_FAILED
    assert out.entry.firing_reason == payload["firing_reason"]
    assert any("recording technical pass" in record.message for record in caplog.records)


def test_exhausted_wolf_discussion_records_technical_pass(monkeypatch):
    payload = {
        "player_id": "wolf_1",
        "player_role": "wolf",
        "current_day": 2,
        "current_round": 1,
        "surviving_wolves": ["wolf_1", "wolf_2"],
        "surviving_villagers": ["player_2", "player_3"],
        "day_channel": [],
        "day_summaries": [],
        "wolf_channel": [],
        "dead_roster": [],
        "cast_role_counts": {},
    }
    monkeypatch.setattr(agent_mod, "get_llm", lambda: _BrokenLLM())
    monkeypatch.setattr(agent_mod, "get_llm_game_fallback", lambda: None)

    out = agent_mod.run_agent(
        payload,
        WOLF_NIGHT_DISCUSS,
        WolfNightDiscussOutput,
        "wolf_channel",
    )

    assert isinstance(out, ResolvedWolfDiscussion)
    assert out.entry.passed is True
    assert out.entry.message == ""
    assert out.entry.vote == ""
    assert out.entry.pass_reason == DiscussionPassReason.GENERATION_FAILED


def test_same_model_configuration_skips_the_rescue(monkeypatch):
    # Fallback == primary -> accessor returns None (a re-roll on the same model isn't a rescue).
    # Accessors are uncached since BYOK (memoization lives in create_chat_model, keyed by
    # the per-game key), so the env change takes effect with no cache_clear.
    monkeypatch.setenv("GOOGLE_GENAI_MODEL", "gemini-3.5-flash-lite")
    monkeypatch.setenv("GAME_FALLBACK_MODEL", "gemini-3.5-flash-lite")
    assert accessors.get_llm_game_fallback() is None


# ---- stalls: a slow or full primary goes to the rescue at once, then is skipped for a while -----
#
# Vertex's shared pool held requests for minutes on 2026-09-30 (429 RESOURCE_EXHAUSTED after a
# long wait); with the request budget those surface as transient errors, and the game's health
# count sends the next turns straight to the rescue model.

import httpx
import pytest
from google.genai import errors as genai_errors

from Agents.llm_factory import health as health_mod
from Agents.llm_factory.backends import GAME_LLM, GameLLM
from Agents.llm_factory.embeddings import is_transient_provider_error


class _StalledLLM:
    """A primary whose every call is bounced by the provider; counts the calls."""

    def __init__(self, exc):
        self.calls = 0
        self._exc = exc

    def with_structured_output(self, _schema):
        def _stall(_input):
            self.calls += 1
            raise self._exc
        return RunnableLambda(_stall)


class _CountingLLM(_WorkingLLM):
    def __init__(self, result):
        super().__init__(result)
        self.calls = 0

    def with_structured_output(self, _schema):
        def _answer(_input):
            self.calls += 1
            return self._result
        return RunnableLambda(_answer)


def _bounce_429():
    return genai_errors.ClientError(
        429, {"error": {"code": 429, "message": "Resource exhausted. Please try again later.",
                        "status": "RESOURCE_EXHAUSTED"}})


@pytest.fixture
def game_health():
    """A fresh per-game selection with a short cooldown, so no test sees another's stalls."""
    selection = GameLLM(
        model="gemini-3.6-flash", rescue_model="gemini-3.5-flash",
        health=health_mod.ModelHealth(rescue_after=2, cooldown_s=300),
    )
    token = GAME_LLM.set(selection)
    try:
        yield selection.health
    finally:
        GAME_LLM.reset(token)


def test_transient_errors_are_the_provider_being_slow_or_full():
    assert is_transient_provider_error(_bounce_429())
    assert is_transient_provider_error(httpx.ReadTimeout("The read operation timed out"))
    assert is_transient_provider_error(TimeoutError())
    assert not is_transient_provider_error(ValueError("off-schema output"))


def test_a_stalled_primary_is_not_asked_again_and_the_rescue_takes_the_turn(
        monkeypatch, caplog, game_health):
    primary = _StalledLLM(_bounce_429())
    rescue = _CountingLLM(_result())
    monkeypatch.setattr(agent_mod, "get_llm", lambda: primary)
    monkeypatch.setattr(agent_mod, "get_llm_game_fallback", lambda: rescue)
    with caplog.at_level("WARNING"):
        out = agent_mod.run_agent(_payload(), HEALER_NIGHT, HealerOutput, "healer_target")
    assert out.entry == "player_3"
    assert primary.calls == 1  # one request budget, not the two attempts a wrong answer gets
    assert rescue.calls == 1
    assert game_health.stalls == 1
    assert not game_health.prefer_rescue()  # one stall is not yet a pattern
    assert any("stalled" in r.message for r in caplog.records)


def test_repeated_stalls_send_the_next_turns_straight_to_the_rescue(
        monkeypatch, caplog, game_health):
    primary = _StalledLLM(httpx.ReadTimeout("The read operation timed out"))
    rescue = _CountingLLM(_result())
    monkeypatch.setattr(agent_mod, "get_llm", lambda: primary)
    monkeypatch.setattr(agent_mod, "get_llm_game_fallback", lambda: rescue)
    for _ in range(2):
        agent_mod.run_agent(_payload(), HEALER_NIGHT, HealerOutput, "healer_target")
    assert primary.calls == 2 and game_health.prefer_rescue()

    with caplog.at_level("WARNING"):
        out = agent_mod.run_agent(_payload(), HEALER_NIGHT, HealerOutput, "healer_target")
    assert out.entry == "player_3"
    assert primary.calls == 2  # the third turn never touched the primary
    assert rescue.calls == 3
    assert any("starts on the rescue model" in r.message and "2 turns in a row" in r.message
               for r in caplog.records)


def test_a_good_answer_from_the_primary_clears_the_count(monkeypatch, game_health):
    game_health.note_stall()
    monkeypatch.setattr(agent_mod, "get_llm", lambda: _WorkingLLM(_result()))
    monkeypatch.setattr(agent_mod, "get_llm_game_fallback", lambda: _BrokenLLM())
    agent_mod.run_agent(_payload(), HEALER_NIGHT, HealerOutput, "healer_target")
    assert game_health.stalls == 0 and not game_health.prefer_rescue()


def test_after_the_cooldown_the_primary_is_tried_again(monkeypatch, game_health):
    now = [1000.0]
    monkeypatch.setattr(health_mod.time, "monotonic", lambda: now[0])
    game_health.note_stall(); game_health.note_stall()
    assert game_health.prefer_rescue()
    now[0] += 301
    assert not game_health.prefer_rescue()
    # one more stall re-arms the rescue at once: the count is still at the threshold
    game_health.note_stall()
    assert game_health.prefer_rescue()
    game_health.note_ok()
    assert not game_health.prefer_rescue() and game_health.stalls == 0


def test_a_turn_on_the_rescue_leaves_the_count_alone(monkeypatch, game_health):
    game_health.note_stall(); game_health.note_stall()
    primary = _StalledLLM(_bounce_429())
    monkeypatch.setattr(agent_mod, "get_llm", lambda: primary)
    monkeypatch.setattr(agent_mod, "get_llm_game_fallback", lambda: _WorkingLLM(_result()))
    agent_mod.run_agent(_payload(), HEALER_NIGHT, HealerOutput, "healer_target")
    assert primary.calls == 0 and game_health.stalls == 2 and game_health.prefer_rescue()


def test_the_game_model_carries_the_request_budget(monkeypatch):
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key")
    monkeypatch.delenv("GAME_LLM_TIMEOUT_S", raising=False)
    monkeypatch.delenv("GAME_LLM_ATTEMPTS", raising=False)
    token = GAME_LLM.set(GameLLM(model="gemini-3.6-flash", rescue_model="gemini-3.5-flash"))
    try:
        llm, rescue, summary = (accessors.get_llm(), accessors.get_llm_game_fallback(),
                                accessors.get_llm_summary())
    finally:
        GAME_LLM.reset(token)
    assert (llm.timeout, llm.max_retries) == (30.0, 2)
    assert (rescue.timeout, rescue.max_retries) == (30.0, 2)
    assert (summary.timeout, summary.max_retries) == (90.0, 2)


def test_openai_and_xai_prefixes_build_openai_protocol_clients(monkeypatch):
    """The bench's non-Gemini arms: openai/<model> and xai/<model> need their own key, and build a
    tool-calling ChatOpenAI pointed at the provider (no network at construction)."""
    import pytest

    from Agents.llm_factory.backends import _build_chat_model

    for prefix, key, url in (("openai", "OPENAI_API_KEY", "api.openai.com"),
                             ("xai", "XAI_API_KEY", "api.x.ai")):
        monkeypatch.delenv(key, raising=False)
        with pytest.raises(ValueError, match=key):
            _build_chat_model(f"{prefix}/some-model")
        monkeypatch.setenv(key, "test-key")
        llm = _build_chat_model(f"{prefix}/some-model", temperature=1.0)
        assert llm.model_name == "some-model" and url in str(llm.openai_api_base)


def test_an_exhausted_round_turn_keeps_its_round_on_the_technical_pass(monkeypatch):
    # Seen in a step 8 game (2026-10-07): the accused's closing turn failed every attempt and its
    # pass marker landed in the transcript as day_round "discussion" after the closing's call
    # (fixed the same day: the technical pass copies the payload's day_round).
    payload = {
        **_payload(),
        "day_channel": [],
        "day_summaries": [],
        "day_round": "closing",
    }
    monkeypatch.setattr(agent_mod, "get_llm", lambda: _BrokenLLM())
    monkeypatch.setattr(agent_mod, "get_llm_game_fallback", lambda: _BrokenLLM())

    out = agent_mod.run_agent(payload, VILLAGER_DAY_DISCUSS, DayDiscussOutput, "day_channel")

    assert out.entry.pass_reason == DiscussionPassReason.GENERATION_FAILED
    assert out.entry.day_round == "closing"
