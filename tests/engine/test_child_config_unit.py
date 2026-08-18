"""Direct contract for the child-config helper (`Agents.config.child_runnable_config`).

WHY a UNIT test and not just the interrupt integration test: LangGraph propagates the checkpointer
to subgraphs via AMBIENT contextvars, independent of what config the wrapper forwards. So an
`interrupt()`-survives integration test passes even if the helper drops the whole `configurable`
bag — the ambient path masks it (see tests/test_subgraph_interrupt.py). This file is therefore the
ONLY thing that actually tests the helper: it pins that the child config is a pure function of the
explicit parent arg and preserves every field, including opaque framework keys.

The helper wraps LangChain's `patch_config`. It inherits the parent recursion limit by default
(falling back to 100), overrides it only on an explicit kwarg, and never mutates the parent.
"""
from __future__ import annotations

from langchain_core.runnables.config import var_child_runnable_config

from Agents.config import child_runnable_config


def _parent():
    return {
        "recursion_limit": 100,
        "tags": ["root"],
        "metadata": {"runtime_fingerprint": "fp-abc"},
        "callbacks": ["CB"],
        "run_name": "werewolf-game",
        "configurable": {
            "game_id": "game-1",
            "game_config": {"max_days": 12},
            # opaque framework keys LangGraph injects at runtime — MUST survive:
            "__pregel_checkpointer": object(),
            "checkpoint_ns": "N:xyz",
            "thread_id": "game-1",
            # a sentinel for an UNKNOWN key, so the test doesn't rot when LangGraph
            # renames its internals — we assert "arbitrary configurable key survives".
            "__unknown_sentinel__": "keep-me",
        },
    }


def test_preserves_all_top_level_fields():
    parent = _parent()
    child = child_runnable_config(parent)
    for key in ("tags", "callbacks", "run_name"):
        assert child[key] == parent[key], f"top-level {key} not preserved"
    # metadata is PRESERVED but not byte-equal: patch_config folds non-dunder configurable keys
    # (e.g. checkpoint_ns) into metadata for trace propagation — benign and framework-standard. The
    # contract is that no parent metadata is LOST, not that nothing is added.
    for k, v in parent["metadata"].items():
        assert child["metadata"][k] == v, f"parent metadata {k} not preserved"


def test_preserves_configurable_including_opaque_and_unknown():
    parent = _parent()
    child = child_runnable_config(parent)
    pconf, cconf = parent["configurable"], child["configurable"]
    # every configurable key survives, including opaque + unknown framework keys
    assert set(cconf.keys()) == set(pconf.keys())
    assert cconf["__pregel_checkpointer"] is pconf["__pregel_checkpointer"]
    assert cconf["checkpoint_ns"] == "N:xyz"
    assert cconf["thread_id"] == "game-1"
    assert cconf["__unknown_sentinel__"] == "keep-me"


def test_recursion_limit_default_when_absent():
    parent = _parent()
    del parent["recursion_limit"]
    assert child_runnable_config(parent)["recursion_limit"] == 100


def test_recursion_limit_preserved_when_present():
    parent = _parent()
    parent["recursion_limit"] = 250
    assert child_runnable_config(parent)["recursion_limit"] == 250


def test_call_does_not_mutate_parent():
    parent = _parent()
    before_top = set(parent.keys())
    before_conf = dict(parent["configurable"])
    child_runnable_config(parent)
    assert set(parent.keys()) == before_top
    assert parent["configurable"] == before_conf


def test_output_derives_only_from_explicit_arg_not_ambient():
    """The helper must be a pure function of its explicit `config` arg — it must NOT silently fold in
    the ambient runnable config. (This is exactly the masking risk the interrupt test can't catch:
    if a future impl started merging ambient, a caller passing a stripped config would get surprising
    keys.) Pin that an ambient sentinel does NOT leak into the output."""
    token = var_child_runnable_config.set(
        {"configurable": {"__ambient_leak__": "should-not-appear"}}
    )
    try:
        child = child_runnable_config(_parent())
    finally:
        var_child_runnable_config.reset(token)
    assert "__ambient_leak__" not in child["configurable"]


def test_explicit_recursion_override_wins():
    """The `recursion_limit=` kwarg (the day phase's cap-derived limit) must win over the
    inherited/default limit, without disturbing configurable."""
    parent = _parent()  # parent carries recursion_limit=100
    child = child_runnable_config(parent, recursion_limit=999)
    assert child["recursion_limit"] == 999
    assert child["configurable"]["thread_id"] == "game-1"
