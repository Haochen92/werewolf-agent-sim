"""Claude seats (Agents/llm_factory/claude.py): where the request is marked for caching, and when a
seat may think (a forced tool call cannot be combined with thinking)."""
from langchain_core.messages import HumanMessage, SystemMessage

from Agents.llm_factory.backends import _build_chat_model
from Agents.llm_factory.claude import ClaudeChat, _marked_message

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
    assert schema.thinking == {"type": "adaptive"} and schema.reasoning_effort == "medium"
    assert schema.model == "claude-haiku-5-5"
