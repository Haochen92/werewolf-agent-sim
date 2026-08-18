"""Integration SMOKE test: an interrupt() deep inside an imperatively-invoked subgraph pauses and
resumes when the parent is compiled with a checkpointer and the wrapper forwards config via the real
`child_runnable_config` helper. This is the end-to-end HITL path this codebase's *_phase wrappers use.

READ THIS BEFORE TRUSTING IT: this test does NOT validate that the helper preserved anything.
LangGraph propagates the checkpointer via ambient contextvars, so this passes even if the helper
returned an empty config (verified: scratchpad ambient spike). The helper's correctness is pinned by
tests/test_child_config_unit.py. Keep this test for what it IS: proof the wrapper/checkpointer wiring
is intact and interrupts survive the imperative subgraph boundary + resume cleanly across TWO calls
on one thread (the real game re-invokes each phase every day).
"""
from __future__ import annotations

from typing import TypedDict

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt

from Agents.config import child_runnable_config


class _Sub(TypedDict, total=False):
    val: str


def _sub_node(state):
    answer = interrupt({"ask": "human decision?"})
    return {"val": answer}


_sub = StateGraph(_Sub)
_sub.add_node("ASK", _sub_node)
_sub.add_edge(START, "ASK")
_sub.add_edge("ASK", END)
_sub_compiled = _sub.compile()  # no checkpointer — inherits the parent's


class _Par(TypedDict, total=False):
    day: int
    out: str


def _wrapper(state, config):
    # the real parent.py pattern: imperatively invoke the subgraph, forward config via the helper
    res = _sub_compiled.invoke({"val": ""}, config=child_runnable_config(config))
    return {"out": res["val"]}


def _build_parent():
    g = StateGraph(_Par)
    g.add_node("PHASE", _wrapper)
    g.add_edge(START, "PHASE")
    g.add_edge("PHASE", END)
    return g.compile(checkpointer=MemorySaver())


def test_interrupt_pauses_and_resumes_through_imperative_subgraph():
    parent = _build_parent()
    cfg = {"configurable": {"thread_id": "game-hitl"}}

    first = parent.invoke({"day": 1}, config=cfg)
    assert "__interrupt__" in first
    assert first["__interrupt__"][0].value == {"ask": "human decision?"}

    resumed = parent.invoke(Command(resume="LYNCH player_3"), config=cfg)
    assert resumed["out"] == "LYNCH player_3"


def test_repeated_phase_calls_on_one_thread_resume_independently():
    """Two phases on the same thread (the game re-invokes phases each day): each interrupt must
    resume with its OWN answer, no Day-1 checkpoint bleeding into Day-2."""
    parent = _build_parent()
    cfg = {"configurable": {"thread_id": "game-hitl-2days"}}

    parent.invoke({"day": 1}, config=cfg)
    r1 = parent.invoke(Command(resume="answer_1"), config=cfg)
    assert r1["out"] == "answer_1"

    parent.invoke({"day": 2}, config=cfg)
    r2 = parent.invoke(Command(resume="answer_2"), config=cfg)
    assert r2["out"] == "answer_2"
