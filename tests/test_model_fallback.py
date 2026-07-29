"""The retry-exhaustion model fallback: a failing primary seat is rescued by the fallback backend
before the random-action fallback fires; same-model configurations skip the rescue entirely.

Born from a live deepseek-v4-pro game (2026-07-26): unconstrained tool-calling backends emit
off-schema output that can exhaust every retry, and a random discussion turn is seat damage the
fallback model avoids.
"""

from langchain_core.runnables import RunnableLambda

from Agents.llm_factory import accessors
from Agents.prompts.night import HEALER_NIGHT
from Agents.schemas.output import PlayerRead
from Agents.schemas.output import HealerOutput
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


def test_same_model_configuration_skips_the_rescue(monkeypatch):
    # Fallback == primary -> accessor returns None (a re-roll on the same model isn't a rescue).
    monkeypatch.setenv("GOOGLE_GENAI_MODEL", "gemini-3.5-flash-lite")
    monkeypatch.setenv("GAME_FALLBACK_MODEL", "gemini-3.5-flash-lite")
    accessors.get_llm_game_fallback.cache_clear()
    try:
        assert accessors.get_llm_game_fallback() is None
    finally:
        accessors.get_llm_game_fallback.cache_clear()
