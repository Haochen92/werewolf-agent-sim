"""Claude calls that share a prefix under different schemas (decisions §11): an enforced schema is part
of Claude's cache key, so ``schema_in_prompt`` writes the schema as text after the cached part,
validates the reply here, and asks again with the schema enforced when it does not validate."""

from types import SimpleNamespace

from pydantic import BaseModel

from Agents.llm_factory.providers import anthropic as cs


class _Verdict(BaseModel):
    verdict: str
    score: int


def _usage():
    return SimpleNamespace(input_tokens=10, output_tokens=5, cache_read_input_tokens=0,
                           cache_creation_input_tokens=0, cache_creation=None)


def test_the_schema_is_written_after_the_cached_prefix():
    content = cs._content(cs._with_schema("PREFIX tail", _Verdict), "PREFIX ", "1h")
    assert content[0] == {"type": "text", "text": "PREFIX ", "cache_control": {"type": "ephemeral", "ttl": "1h"}}
    assert content[1]["text"].startswith("tail") and '"score"' in content[1]["text"]


def test_a_reply_is_validated_and_a_fenced_one_tolerated():
    assert cs._validated('```json\n{"verdict": "fits", "score": 2}\n```', _Verdict) == _Verdict(verdict="fits", score=2)
    before = cs.usage_totals["unvalidated_replies"]
    assert cs._validated('{"verdict": "fits"}', _Verdict) is None
    assert cs.usage_totals["unvalidated_replies"] == before + 1


def test_a_reply_that_does_not_validate_is_asked_for_again_with_the_schema_enforced(monkeypatch):
    calls = []

    class _Messages:
        def create(self, **kw):
            calls.append(("create", "output_format" in kw))
            return SimpleNamespace(usage=_usage(), content=[SimpleNamespace(type="text", text="no json here")])

        def parse(self, **kw):
            calls.append(("parse", kw["output_format"] is _Verdict))
            return SimpleNamespace(usage=_usage(), parsed_output=_Verdict(verdict="ok", score=1))

    monkeypatch.setattr(cs, "_client", lambda: SimpleNamespace(messages=_Messages()))
    monkeypatch.setattr(cs, "_trace", lambda *a, **k: None)
    parsed, _ = cs.parse_with_claude("p", _Verdict, "claude-haiku-5-5", "off", schema_in_prompt=True)
    assert parsed == _Verdict(verdict="ok", score=1)
    assert calls == [("create", False), ("parse", True)]


def test_a_batch_with_the_schema_in_the_prompt_sends_no_enforced_format(monkeypatch):
    sent = {}

    class _Batches:
        def create(self, requests):
            sent["requests"] = requests
            return SimpleNamespace(id="b", processing_status="ended")

        def results(self, _id):
            text = {"r1": '{"verdict": "a", "score": 1}', "r2": "oops"}
            return [SimpleNamespace(custom_id=k, result=SimpleNamespace(type="succeeded", message=SimpleNamespace(
                usage=_usage(), content=[SimpleNamespace(type="text", text=v)], stop_reason="end_turn")))
                for k, v in text.items()]

    monkeypatch.setattr(cs, "_client", lambda: SimpleNamespace(messages=SimpleNamespace(batches=_Batches())))
    monkeypatch.setattr(cs, "_trace", lambda *a, **k: None)
    out = cs.batch_parse({"r1": ("P x", _Verdict, "P "), "r2": ("P y", _Verdict, "P ")}, "claude-haiku-5-5",
                         "off", cache_ttl="1h", schema_in_prompt=True)
    assert all("output_config" not in r["params"] or "format" not in r["params"]["output_config"]
               for r in sent["requests"])
    assert out == {"r1": _Verdict(verdict="a", score=1), "r2": None}
