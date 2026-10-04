"""How an OpenAI-protocol model is asked for a schema (Agents/llm_factory/backends.py, STRUCTURED_MODES),
and when DeepSeek may think: its thinking mode rejects a forced tool call, so thinking is on only
when the model's mode doesn't force one."""
import pytest
from langchain_core.exceptions import OutputParserException
from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableLambda
from pydantic import BaseModel

from Agents.llm_factory import backends
from Agents.llm_factory.backends import _ToolCallStructuredChatOpenAI, _build_chat_model


class Vote(BaseModel):
    target: str


def test_json_reply_is_validated_and_a_fence_is_tolerated():
    assert backends._parse_json_reply(Vote, AIMessage('{"target": "Mia"}')) == Vote(target="Mia")
    assert backends._parse_json_reply(Vote, AIMessage('```json\n{"target": "Mia"}\n```')) == Vote(target="Mia")
    with pytest.raises(OutputParserException):
        backends._parse_json_reply(Vote, AIMessage("I vote for Mia."))


def test_auto_tool_reply_without_the_tool_call_is_a_parse_failure():
    called = AIMessage("", tool_calls=[{"name": "Vote", "args": {"target": "Omar"}, "id": "1"}])
    assert backends._first_tool_call(Vote, called) == Vote(target="Omar")
    with pytest.raises(OutputParserException):
        backends._first_tool_call(Vote, AIMessage("Omar, obviously."))


def test_json_mode_appends_the_schema_last_and_turns_on_json_output(monkeypatch):
    seen = {}

    def fake_bind(self, **kwargs):
        seen["bind"] = kwargs
        return RunnableLambda(lambda messages: seen.setdefault("messages", messages) and AIMessage('{"target": "Ivy"}'))

    monkeypatch.setattr(_ToolCallStructuredChatOpenAI, "bind", fake_bind)
    llm = _ToolCallStructuredChatOpenAI(model="m", api_key="k", structured_mode="json_mode")
    assert llm.with_structured_output(Vote).invoke("Who do you vote for?") == Vote(target="Ivy")
    assert seen["bind"] == {"response_format": {"type": "json_object"}}
    first, last = seen["messages"][0], seen["messages"][-1]
    assert first.content == "Who do you vote for?"  # the prompt's prefix is untouched
    assert "JSON schema" in last.content and '"target"' in last.content


def _deepseek(monkeypatch, **kwargs):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key")
    return _build_chat_model("deepseek/deepseek-v4-pro", temperature=1.0, **kwargs)


def test_deepseek_thinks_only_when_its_mode_does_not_force_the_tool_call(monkeypatch):
    thinking = lambda llm: llm.extra_body["thinking"]["type"]
    assert thinking(_deepseek(monkeypatch, thinking_level="medium")) == "disabled"  # default forced_tool
    llm = _deepseek(monkeypatch, thinking_level="medium", structured_mode="json_mode")
    assert (thinking(llm), llm.structured_mode) == ("enabled", "json_mode")
    assert thinking(_deepseek(monkeypatch, thinking_level="minimal", structured_mode="auto_tool")) == "disabled"


def test_the_catalogue_mode_applies_and_an_explicit_mode_overrides_it(monkeypatch):
    monkeypatch.setitem(backends.STRUCTURED_MODE_BY_MODEL, "deepseek/deepseek-v4-pro", "auto_tool")
    assert _deepseek(monkeypatch).structured_mode == "auto_tool"
    assert _deepseek(monkeypatch, structured_mode="forced_tool").structured_mode == "forced_tool"


def test_a_bench_arm_sets_the_mode_by_env_and_gemini_ignores_it(monkeypatch):
    monkeypatch.setenv("LLM_STRUCTURED_MODE", "json_mode")
    assert _deepseek(monkeypatch).structured_mode == "json_mode"
    _build_chat_model("gemini-3.5-flash-lite")  # no error: the env is for OpenAI-protocol models


def test_a_mode_is_rejected_where_it_means_nothing(monkeypatch):
    with pytest.raises(ValueError):
        _deepseek(monkeypatch, structured_mode="strict")
    with pytest.raises(ValueError):
        _build_chat_model("gemini-3.5-flash-lite", structured_mode="json_mode")


def test_an_openrouter_model_is_pinned_to_its_makers_servers_with_reasoning_mapped(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    llm = _build_chat_model("openrouter/qwen/qwen3.8-flash", temperature=1.0, thinking_level="medium")
    assert llm.model_name == "qwen/qwen3.8-flash"
    assert llm.extra_body == {"provider": {"order": ["alibaba"], "allow_fallbacks": False},
                              "reasoning": {"effort": "medium"}}
    off = _build_chat_model("openrouter/z-ai/glm-5.3-flash", thinking_level="minimal")
    assert off.extra_body["reasoning"] == {"enabled": False}
    with pytest.raises(ValueError):  # a family with no pinned host is refused, not left to routing
        _build_chat_model("openrouter/some-lab/some-model")


def test_openai_reasoning_effort_follows_the_thinking_level(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    assert _build_chat_model("openai/gpt-6-luna", thinking_level="low").reasoning_effort == "low"
    assert _build_chat_model("openai/gpt-6-luna", thinking_level="minimal").reasoning_effort == "none"
    assert _build_chat_model("openai/gpt-6-luna").reasoning_effort is None


def test_json_schema_mode_asks_for_the_providers_strict_structured_output(monkeypatch):
    seen = {}

    def fake(self, schema=None, **kwargs):
        seen.update(kwargs)
        return "runnable"

    monkeypatch.setattr(backends.ChatOpenAI, "with_structured_output", fake)
    llm = _ToolCallStructuredChatOpenAI(model="m", api_key="k", structured_mode="json_schema")
    assert llm.with_structured_output(Vote) == "runnable"
    assert seen == {"method": "json_schema", "strict": True}
