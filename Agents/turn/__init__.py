"""The turn system — who gets the turn, and how it executes.

The graph nodes in Agents/nodes/ are pure wiring; they delegate every agent turn
here. Two halves, connected only by data (`firing_reason` rides the Send):

WHO (policy — day discussion only; votes and night actions are fan-out, so there
is nothing to schedule):
  scheduler.py — speaker selection: reactive obligations, proactive ranking,
                 pass-based termination. Pure functions, no LLM.

HOW (the execution pipeline: enrich → decide → record — all actions, day + night):
  pipeline.py      — _run_memory_informed_action / _night_action: the pipeline
  decision.py      — _run_agent: the decision path (constrain → generate → interpret)
  action_space.py  — legal-move enforcement (valid targets + dynamic target enum)
  novelty_agent.py — the proactive-novelty speak-gate (judge llm.invoke + prompt)
  adoption.py      — record: strategy-adoption store write-back (memory impact)
  eval.py          — record: EvalCase private-context snapshot + leak-test capture
                     (prompt_log / reads_log) + reads-completeness monitor
"""

from Agents.turn.pipeline import (  # noqa: F401
    _run_memory_informed_action,
    _run_memory_informed_night_action,
)
from Agents.turn.decision import _run_agent  # noqa: F401
from Agents.turn.eval import prompt_log, reads_log  # noqa: F401
from Agents.turn.novelty_agent import NOVELTY_JUDGE_PROMPT, judge_proactive_novelty  # noqa: F401
from Agents.turn.scheduler import (  # noqa: F401
    build_reactive_queue,
    cycle_seed,
    rank_proactive,
    select_next_speaker,
)
