"""The de-halo pass after extraction: configured from the environment (on, claude-haiku-5-5 by
default in production), it rewrites the verdicts its judge revises, keeps the originals in its
record, and never breaks extraction. The judge is stubbed: no model is called."""

from types import SimpleNamespace

from Agents.memory.extraction import dehalo
from Agents.memory.persistence.config import DehaloConfig, ExtractionConfig
from Agents.schemas.dehalo import Judgment, Judgments

_INPUTS = {"lineup": [], "formatted_discussions": "record", "formatted_strategy_notes": "notes",
           "game_outcome": "villagers"}


def _obs(verdict: str):
    return SimpleNamespace(perspective="vigilante", action_phase="night_action", net_verdict=verdict,
                           approach="held fire", immediate_response="nothing happened",
                           impact_on_final_game_outcome="town won")


def test_the_defaults_come_from_the_environment(monkeypatch):
    for name in ("MEMORY_DEHALO_ENABLED", "MEMORY_DEHALO_MODEL", "MEMORY_DEHALO_THINKING_LEVEL"):
        monkeypatch.delenv(name, raising=False)
    config = ExtractionConfig().dehalo
    assert (config.enabled, config.model, config.thinking_level) == (True, "claude-haiku-5-5", None)
    monkeypatch.setenv("MEMORY_DEHALO_ENABLED", "0")
    monkeypatch.setenv("MEMORY_DEHALO_MODEL", "gemini-3.8-flash")
    monkeypatch.setenv("MEMORY_DEHALO_THINKING_LEVEL", "low")
    config = DehaloConfig()
    assert (config.enabled, config.model, config.thinking_level) == (False, "gemini-3.8-flash", "low")


def test_revised_verdicts_are_applied_and_the_originals_kept(monkeypatch):
    calls = []

    def fake_judge(prompt, config):
        calls.append(prompt)
        return Judgments(judgments=[
            Judgment(index=1, halo=True, revised_verdict="unclear", reason="no link"),
            Judgment(index=2, halo=False, revised_verdict="negative", reason="the record shows it"),
            Judgment(index=9, halo=True, revised_verdict="unclear", reason="no such lesson"),
        ]), {"input_tokens": 10, "output_tokens": 5}

    monkeypatch.setattr(dehalo, "judge", fake_judge)
    observations = [_obs("positive"), _obs("negative")]
    record = dehalo.dehalo_observations(observations, _INPUTS, DehaloConfig(enabled=True, model="claude-haiku-5-5"))
    assert [o.net_verdict for o in observations] == ["unclear", "negative"]
    assert record["revised"] == 1 and record["judged"] == 2
    assert record["judgments"][0]["original_verdict"] == "positive"
    assert "[1] vigilante / night_action — verdict: positive" in calls[0] and "GAME OUTCOME: villagers" in calls[0]


def test_disabled_or_failing_passes_leave_the_verdicts_alone(monkeypatch):
    observations = [_obs("positive")]
    assert dehalo.dehalo_observations(observations, _INPUTS, DehaloConfig(enabled=False)) is None

    def broken(prompt, config):
        raise RuntimeError("quota")

    monkeypatch.setattr(dehalo, "judge", broken)
    assert dehalo.dehalo_observations(observations, _INPUTS, DehaloConfig(enabled=True)) is None
    assert observations[0].net_verdict == "positive"


def test_a_claude_judge_maps_the_thinking_level(monkeypatch):
    sent = {}

    class FakeMessages:
        def parse(self, **kwargs):
            sent.update(kwargs)
            return SimpleNamespace(parsed_output=Judgments(judgments=[]),
                                   usage=SimpleNamespace(input_tokens=1, output_tokens=1))

    import anthropic
    monkeypatch.setenv("CLAUDE_API_KEY", "test")
    monkeypatch.setattr(anthropic, "Anthropic", lambda api_key: SimpleNamespace(messages=FakeMessages()))
    dehalo.judge("p", DehaloConfig(model="claude-haiku-5-5", thinking_level="low"))
    assert sent["thinking"] == {"type": "adaptive"} and sent["output_config"] == {"effort": "low"}
    dehalo.judge("p", DehaloConfig(model="claude-haiku-5-5", thinking_level="minimal"))
    assert sent["thinking"] == {"type": "disabled"}
