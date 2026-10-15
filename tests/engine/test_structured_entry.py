"""The offline entry (Agents/llm_factory/structured.py): a Claude model goes through the Anthropic SDK
(one Message Batch for many calls); any other through its live chat model, a "batch" being
concurrent direct calls, a failed one mapping to None as in a batch."""

from pydantic import BaseModel

from Agents.llm_factory import structured
from Agents.llm_factory.providers import anthropic


class _Verdict(BaseModel):
    ok: bool


def test_a_claude_batch_is_one_message_batch(monkeypatch):
    sent = {}
    monkeypatch.setattr(anthropic, "batch_parse",
                        lambda requests, model, thinking, **kw: sent.update(requests=requests, kw=kw) or {"a": None})
    structured.batch_structured({"a": ("p", _Verdict, "pre")}, "claude-haiku-5-5", cache_ttl="1h", schema_in_prompt=True)
    assert sent["requests"] == {"a": ("p", _Verdict, "pre")}
    assert sent["kw"]["cache_ttl"] == "1h" and sent["kw"]["schema_in_prompt"] is True


def test_another_provider_batch_is_concurrent_direct_calls(monkeypatch):
    def fake_call(prompt, schema, model, **kw):
        if prompt == "bad":
            raise RuntimeError("provider error")
        return schema(ok=True), {}

    monkeypatch.setattr(structured, "structured_call", fake_call)
    out = structured.batch_structured({"a": ("good", _Verdict), "b": ("bad", _Verdict)}, "gemini-3.8-flash")
    assert out == {"a": _Verdict(ok=True), "b": None}
