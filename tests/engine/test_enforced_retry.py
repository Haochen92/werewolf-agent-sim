"""A json_mode model whose reply breaks the schema is asked again with the schema enforced, in the
lookup's situation summary and the day summary as on a seat's turn (test_model_fallback.py)."""
from types import SimpleNamespace

from langchain_core.runnables import RunnableLambda

from Agents.memory.retrieval import situation_agent
from Agents.nodes.day import summary_agent


class _JsonModeLLM:
    """Breaks the schema unenforced; enforced, answers ``answer``."""

    def __init__(self, answer):
        self.answer, self.enforced_calls = answer, 0

    def with_structured_output(self, _schema):
        def _boom(_input):
            raise ValueError("off-schema output")
        return RunnableLambda(_boom)

    def enforced_structured_output(self, _schema):
        def _answer(_input):
            self.enforced_calls += 1
            return self.answer
        return RunnableLambda(_answer)


def test_the_lookups_situation_summary_retries_enforced(monkeypatch):
    llm = _JsonModeLLM(SimpleNamespace(situations=[]))
    monkeypatch.setattr(situation_agent, "get_llm", lambda: llm)
    monkeypatch.setattr(situation_agent, "V6_SITUATION_SUMMARY", RunnableLambda(lambda x: x))
    monkeypatch.setattr(situation_agent, "build_agent_prompt_input", lambda p: {})
    monkeypatch.setattr(situation_agent, "compose_cell_guidance", lambda *a: {})
    monkeypatch.setattr(situation_agent, "_known_board_facts", lambda *a: "")
    monkeypatch.setattr(situation_agent, "_private_state", lambda *a: "")
    payload = {"player_id": "player_1", "player_role": "healer", "current_day": 2}
    # The enforced reply is used: no generic "Day 2 as healer" fallback query.
    assert situation_agent._generate_situations_for_agent(payload, "night_action") == ([], [])
    assert llm.enforced_calls == 1


def test_the_day_summary_retries_enforced(monkeypatch):
    llm = _JsonModeLLM(summary_agent._SUMMARY_SCHEMA.model_construct(accusations=[], role_claims=[]))
    monkeypatch.setattr(summary_agent, "get_llm_summary", lambda: llm)
    _, _, structured = summary_agent.run_day_summary_agent(2, [])
    assert structured == {"accusations": [], "role_claims": []}  # not the raw-channel fallback's {}
    assert llm.enforced_calls == 1
