"""The agent-decision engine — how an actor node makes a memory-informed decision.

Extracted from the old runtime.py (which was 100% non-graph-node helpers). The
actor nodes in Agents/nodes/ call into this; nothing here is a LangGraph node.

  agent.py    — _run_agent: the core LLM call (dynamic target enum, retry, the
                proactive-novelty gate) + prompt_log (leak-test capture)
  actions.py  — _run_memory_informed_action / _night_action: enrich-then-act wrappers
  action_space.py — legal-target computation + dynamic target-enum schema
  novelty_agent.py — the proactive-novelty gate (judge llm.invoke + prompt)
  eval.py     — EvalCase private-context snapshot
  adoption.py — strategy-adoption store write-back (retrieved/used counts)
"""

from Agents.engine.actions import (  # noqa: F401
    _run_memory_informed_action,
    _run_memory_informed_night_action,
)
from Agents.engine.agent import _run_agent, prompt_log  # noqa: F401
from Agents.engine.novelty_agent import NOVELTY_JUDGE_PROMPT, judge_proactive_novelty  # noqa: F401
