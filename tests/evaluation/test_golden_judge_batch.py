"""A Claude golden judge runs as one Message Batch (judging is offline, owner 2026-10-12): every job goes
in the batch with the instructions as the cached head, verdicts come back in job order, and a job the
batch lost is judged directly."""

import Agents.llm_factory.providers.anthropic as cs
from evaluation.src.judges.golden_expectation import SYSTEM, GoldenVerdict, is_claude, judge_golden_batch


def test_jobs_go_in_one_batch_and_a_lost_one_is_judged_directly(monkeypatch):
    seen = {}

    def fake_batch(requests, model, thinking_level=None, cache_prefix=None, poll_seconds=30):
        seen.update(model=model, prefix=cache_prefix, n=len(requests))
        assert all(p.startswith(cache_prefix) for p, _ in requests.values())
        return {"0": GoldenVerdict(quote="", reason="a", verdict="meets"), "1": None}

    def fake_direct(prompt, schema, model, thinking_level=None, cache_prefix=None):
        assert "second text" in prompt
        return GoldenVerdict(quote="q", reason="b", verdict="violates"), {}

    monkeypatch.setattr(cs, "batch_parse", fake_batch)
    monkeypatch.setattr(cs, "parse_with_claude", fake_direct)
    verdicts = judge_golden_batch([("g", "message", "first text"), ("g", "reads", "second text")],
                                  "anthropic/claude-sonnet-5-5")
    assert [v.verdict for v in verdicts] == ["meets", "violates"]
    assert seen == {"model": "claude-sonnet-5-5", "prefix": SYSTEM + "\n\n", "n": 2}


def test_only_claude_models_take_the_batch():
    assert is_claude("anthropic/claude-sonnet-5-5") and is_claude("claude-haiku-5-5")
    assert not is_claude("gemini-3.5-flash")
