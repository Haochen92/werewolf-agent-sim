"""Claude seats (Agents/llm_factory/claude.py): where the request is marked for caching, and when a
seat may think (a forced tool call cannot be combined with thinking)."""
from langchain_core.messages import HumanMessage, SystemMessage

from Agents.llm_factory.chat import _build_chat_model
from Agents.llm_factory.providers.anthropic import ClaudeChat, _marked_message

TRANSCRIPT = "== Dead ==\nnone\n\n== Today's discussion ==\nplayer_1: hi\nplayer_2: hello\n=========================\nYour turn."


def _payload(text: str) -> dict:
    llm = ClaudeChat(model="claude-haiku-5-5", api_key="k")
    return llm._get_request_payload([SystemMessage("the rules"), HumanMessage(text)])


def test_the_system_message_and_the_transcripts_last_line_are_marked():
    payload = _payload(TRANSCRIPT)
    assert payload["system"][-1]["cache_control"] == {"type": "ephemeral"}
    pieces = payload["messages"][-1]["content"]
    marked = [p["text"] for p in pieces if "cache_control" in p]
    assert marked == ["player_2: hello\n"]
    assert pieces[-1]["text"].startswith("=====") and "".join(p["text"] for p in pieces) == TRANSCRIPT


def test_a_longer_transcript_keeps_the_pieces_of_the_shorter_one():
    shorter = _marked_message(TRANSCRIPT)
    longer = _marked_message(TRANSCRIPT.replace("player_2: hello\n", "player_2: hello\nplayer_3: hey\n"))
    texts = [p["text"] for p in longer]
    assert texts[: len(shorter) - 1] == [p["text"] for p in shorter[:-1]]


def test_no_piece_is_blank_and_a_message_without_a_transcript_is_sent_whole():
    assert all(p["text"].strip() for p in _marked_message(TRANSCRIPT))
    assert _payload("Just a question.")["messages"][-1]["content"] == "Just a question."


def test_claude_thinks_only_when_its_mode_does_not_force_the_tool_call(monkeypatch):
    monkeypatch.setenv("CLAUDE_API_KEY", "k")
    forced = _build_chat_model("anthropic/claude-haiku-5-5", thinking_level="medium", structured_mode="forced_tool")
    schema = _build_chat_model("anthropic/claude-haiku-5-5", thinking_level="medium", structured_mode="json_schema")
    off = _build_chat_model("anthropic/claude-haiku-5-5", thinking_level="minimal", structured_mode="json_schema")
    assert forced.thinking == {"type": "disabled"} and off.thinking == {"type": "disabled"}
    assert off.temperature is None  # Haiku 5.5 refuses a temperature
    assert schema.thinking == {"type": "adaptive"} and schema.reasoning_effort == "medium"
    assert schema.model == "claude-haiku-5-5"


def test_sonnet_5_5_with_thinking_off_asks_for_between_tools_and_sends_no_temperature(monkeypatch):
    monkeypatch.setenv("CLAUDE_API_KEY", "k")
    llm = _build_chat_model("anthropic/claude-sonnet-5-5", thinking_level=None)
    assert llm.thinking == {"type": "between_tools"} and llm.temperature is None
    assert llm.structured_mode == "json_schema"


def test_json_mode_puts_the_schema_after_the_transcripts_mark_and_validates_in_code(monkeypatch):
    # Claude counts an enforced schema in its cache key; json_mode sends none and appends the schema to
    # the last user message, so the transcript's mark survives and the schema sits after it.
    from typing import Literal

    from langchain_core.messages import AIMessage
    from pydantic import BaseModel

    class Vote(BaseModel):
        target: Literal["player_1", "player_2"]

    llm = ClaudeChat(model="claude-haiku-5-5", api_key="k", structured_mode="json_mode")
    sent = {}

    def fake_generate(self, messages, *args, **kwargs):
        from langchain_core.outputs import ChatGeneration, ChatResult
        sent["payload"] = self._get_request_payload(messages)
        thinking = {"type": "thinking", "thinking": "", "signature": "s"}
        return ChatResult(generations=[ChatGeneration(message=AIMessage(
            content=[thinking, {"type": "text", "text": 'Here: {"target": "player_2"}'}]))])

    monkeypatch.setattr(ClaudeChat, "_generate", fake_generate)
    out = llm.with_structured_output(Vote).invoke([SystemMessage("the rules"), HumanMessage(TRANSCRIPT)])
    assert out.target == "player_2"  # thinking block skipped, the sentence around the object tolerated
    pieces = sent["payload"]["messages"][-1]["content"]
    assert [p["text"] for p in pieces if "cache_control" in p] == ["player_2: hello\n"]
    assert '"player_1"' in pieces[-1]["text"] and "output_config" not in sent["payload"]


def test_json_mode_rejects_a_target_outside_the_schema():
    import pytest
    from typing import Literal

    from langchain_core.exceptions import OutputParserException
    from langchain_core.messages import AIMessage
    from pydantic import BaseModel

    from Agents.llm_factory.providers.common import _parse_json_reply

    class Vote(BaseModel):
        target: Literal["player_1", "player_2"]

    with pytest.raises(OutputParserException):
        _parse_json_reply(Vote, AIMessage('{"target": "player_9"}'))
