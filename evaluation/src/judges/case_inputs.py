"""Format one frozen ``EvalCase`` into the shared prompt inputs every judge uses.

This is judge-side glue, not part of the read-side ``data/`` package: it renders
a captured case into the fields the situation / retrieval / application judges
interpolate into their prompts.
"""

from __future__ import annotations

from typing import Any

from Agents.prompts.prompt_formatters import (
    format_agent_action,
    format_day_channel,
)
from Agents.schemas.evaluation import EvalCase
from evaluation.src.core.formatters import (
    format_eval_private_context,
    format_eval_retrieved_observations,
    format_eval_retrieved_strategy_points,
    format_eval_situations,
)


def eval_case_to_judge_inputs(case: EvalCase) -> dict[str, Any]:
    """Format one frozen case into the shared prompt inputs used by judges."""
    if case.adopted_strategy_keys:
        adoption_report = (
            f"Agent reported strategy points "
            f"[{', '.join(str(k) for k in case.adopted_strategy_keys)}] "
            f"as influential to its decision."
        )
    else:
        adoption_report = "(not captured)"

    return {
        "player_role": case.player_role,
        "day": case.day,
        "round": case.round,
        "action_phase": case.action_phase,
        "day_channel_excerpt": format_day_channel(case.visible_discussion),
        "private_context": format_eval_private_context(case.private_context),
        "situations": format_eval_situations(case.situations),
        "observations_formatted": format_eval_retrieved_observations(
            case.retrieved_observations
        ),
        "strategy_points_formatted": format_eval_retrieved_strategy_points(
            case.retrieved_strategy_points
        ),
        "num_observations": len(case.retrieved_observations),
        "num_strategy_points": len(case.retrieved_strategy_points),
        "agent_decision": format_agent_action(
            case.action_phase,
            message=case.agent_message,
            vote=case.agent_vote,
        ),
        "agent_updated_strategy": case.updated_strategy,
        "agent_adoption_report": adoption_report,
    }
