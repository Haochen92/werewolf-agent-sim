"""Synthesis on a Claude model goes through the Anthropic SDK helper, never the factory's pro model,
and a tick with a Claude synthesis model keeps the factory pinned to the cheap dedup model."""

from types import SimpleNamespace
from unittest.mock import patch

import Agents.memory.strategy_synthesis as synth_mod
from Agents.memory.consolidation.config import TickConfig

_OBS = {"o1": SimpleNamespace(value={"situation": "s", "net_verdict": "positive",
                                     "approach": "watched the quiet one", "outcome": "o"})}


def test_a_claude_model_is_called_through_the_sdk_helper():
    calls = []

    def fake_parse(prompt, schema, model, thinking_level=None, cache_prefix=None):
        calls.append(model)
        return schema(strategy_points=[]), {"input_tokens": 1, "output_tokens": 1}

    def no_factory():
        raise AssertionError("the factory's pro model must not be built for a Claude model")

    with patch.object(synth_mod, "parse_with_claude", fake_parse), \
            patch.object(synth_mod, "get_llm_pro", no_factory), \
            patch.object(synth_mod, "get_llm_pro_backup", no_factory):
        out = synth_mod.synthesize_cluster_sps("sentinel", "night_action", ["o1"], _OBS,
                                               model="claude-sonnet-5-5")
    assert out == [] and calls == ["claude-sonnet-5-5"]


def test_a_claude_tick_pins_the_factory_to_the_dedup_model():
    env = TickConfig(model="claude-sonnet-5-5").env()
    assert env["GOOGLE_GENAI_PRO_MODEL"] == env["GOOGLE_GENAI_PRO_BACKUP_MODEL"] == "gemini-3.1-flash-lite"
    assert TickConfig().env()["GOOGLE_GENAI_PRO_MODEL"] == "gemini-3.1-flash-lite"


def test_a_batched_tick_sends_every_cluster_in_one_batch_and_retries_the_misses_directly():
    from Agents.memory.consolidation import store_ops
    import Agents.llm_factory.providers.anthropic as cs

    tasks = [("sentinel", "night_action", ["o1"], _OBS, "", []) for _ in range(3)]
    sent = {}

    def fake_batch(requests, model, thinking_level=None, cache_prefix=None, poll_seconds=30):
        sent.update(requests)
        schema = next(iter(requests.values()))[1]
        return {"t0": schema(strategy_points=[]), "t1": None, "t2": schema(strategy_points=[])}

    direct = []

    def run_one(t):
        direct.append(t)
        return t, ["retried"]

    from concurrent.futures import ThreadPoolExecutor
    with patch.object(cs, "batch_parse", fake_batch), ThreadPoolExecutor(2) as pool:
        out = store_ops._batch_results(tasks, TickConfig(model="claude-sonnet-5-5", batch=True), run_one, pool)
    assert sorted(sent) == ["t0", "t1", "t2"]
    assert len(direct) == 1 and [sps for _t, sps in out] == [[], ["retried"], []]


def test_the_cache_prefix_is_the_start_of_every_canonical_synthesis_prompt():
    prompt, _schema = synth_mod.synthesis_request("sentinel", "night_action", ["o1"], _OBS)
    assert prompt.startswith(synth_mod.synthesis_cache_prefix())
