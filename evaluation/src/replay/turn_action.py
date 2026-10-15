"""Replay the production discussion/vote action prompt for one frozen turn."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel

from Agents.turn import run_agent
from Agents.prompts import day_discuss_template, day_vote_template
from Agents.schemas import DayChannel, DayVote
from Agents.schemas.evaluation import EvalCase
from Agents.schemas.lineup_output import day_discuss_output, day_vote_output
from Agents.schemas.roles import ROLE_SPECS
from evaluation.src.replay.situation_summary import case_lineup, eval_case_to_agent_payload


@dataclass(frozen=True)
class ActionSpec:
    prompt_template: Any
    output_schema: type[BaseModel]
    output_key: str


# The day turns, built per case from the role's card and the case's lineup (ten-seat game).
# A nine-seat case (villager, wolf) has no card any more and is refused.
_DAY_BUILDERS = {
    "day_discussion": (day_discuss_template, day_discuss_output, "day_channel"),
    "day_vote": (day_vote_template, day_vote_output, "day_votes"),
}


def action_spec_for(case: EvalCase) -> ActionSpec:
    key = (case.player_role, case.action_phase)
    spec = ROLE_SPECS.get(case.player_role)
    lineup = case_lineup(case)
    if (
        case.action_phase not in _DAY_BUILDERS or spec is None or spec.retired
        or case.player_role not in lineup
    ):
        raise ValueError(
            f"Unsupported application replay role/action: {key!r}"
        )
    template, schema, output_key = _DAY_BUILDERS[case.action_phase]
    return ActionSpec(template(case.player_role), schema(lineup), output_key)


def run_application_action(
    case: EvalCase,
    *,
    retrieved_observations: list[Any] | None = None,
    strategy_points: list[Any] | None = None,
) -> tuple[Any | None, DayChannel | None, DayVote | None, str]:
    payload = eval_case_to_agent_payload(case)
    if retrieved_observations is not None:
        payload["retrieved_observations"] = retrieved_observations
    if strategy_points is not None:
        payload["strategy_points"] = strategy_points

    spec = action_spec_for(case)
    result = run_agent(
        payload,
        spec.prompt_template,
        spec.output_schema,
        spec.output_key,
    )

    agent_message = None
    agent_vote = None
    updated_strategy = ""
    if not result:
        return result, agent_message, agent_vote, updated_strategy

    # run_agent returns a resolved turn: the message or the vote is its entry.
    if spec.output_key == "day_channel":
        agent_message = result.entry
    elif spec.output_key == "day_votes":
        agent_vote = result.entry
    updated_strategy = result.effects.strategy or ""

    return result, agent_message, agent_vote, updated_strategy


def application_case_for_judge(
    case: EvalCase,
    *,
    agent_message: DayChannel | None,
    agent_vote: DayVote | None,
    updated_strategy: str,
) -> EvalCase:
    return case.model_copy(
        update={
            "agent_message": agent_message,
            "agent_vote": agent_vote,
            "updated_strategy": updated_strategy,
        }
    )
