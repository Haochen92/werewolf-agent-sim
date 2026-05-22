"""Replay the production discussion/vote action prompt for one frozen turn."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel

from Agents.agents import _run_agent
from Agents.prompts import (
    HEALER_DAY_DISCUSS,
    HEALER_DAY_VOTE,
    INVESTIGATOR_DAY_DISCUSS,
    INVESTIGATOR_DAY_VOTE,
    VILLAGER_DAY_DISCUSS,
    VILLAGER_DAY_VOTE,
    WOLF_DAY_DISCUSS,
    WOLF_DAY_VOTE,
)
from Agents.schemas import DayChannel, DayDiscussOutput, DayVote, DayVoteOutput
from Agents.schemas.evaluation import EvalCase
from evaluation.components.situation_summary import eval_case_to_agent_payload


@dataclass(frozen=True)
class ActionSpec:
    prompt_template: Any
    output_schema: type[BaseModel]
    output_key: str


ACTION_SPECS: dict[tuple[str, str], ActionSpec] = {
    ("villager", "day_discussion"): ActionSpec(
        VILLAGER_DAY_DISCUSS,
        DayDiscussOutput,
        "day_channel",
    ),
    ("healer", "day_discussion"): ActionSpec(
        HEALER_DAY_DISCUSS,
        DayDiscussOutput,
        "day_channel",
    ),
    ("investigator", "day_discussion"): ActionSpec(
        INVESTIGATOR_DAY_DISCUSS,
        DayDiscussOutput,
        "day_channel",
    ),
    ("wolf", "day_discussion"): ActionSpec(
        WOLF_DAY_DISCUSS,
        DayDiscussOutput,
        "day_channel",
    ),
    ("villager", "day_vote"): ActionSpec(VILLAGER_DAY_VOTE, DayVoteOutput, "day_votes"),
    ("healer", "day_vote"): ActionSpec(HEALER_DAY_VOTE, DayVoteOutput, "day_votes"),
    ("investigator", "day_vote"): ActionSpec(
        INVESTIGATOR_DAY_VOTE,
        DayVoteOutput,
        "day_votes",
    ),
    ("wolf", "day_vote"): ActionSpec(WOLF_DAY_VOTE, DayVoteOutput, "day_votes"),
}


def action_spec_for(case: EvalCase) -> ActionSpec:
    key = (case.player_role, case.action_phase)
    try:
        return ACTION_SPECS[key]
    except KeyError as exc:
        raise ValueError(
            f"Unsupported application replay role/action: {key!r}"
        ) from exc


def run_application_action(
    case: EvalCase,
    *,
    retrieved_observations: list[Any] | None = None,
    strategy_points: list[Any] | None = None,
) -> tuple[dict[str, Any] | None, DayChannel | None, DayVote | None, str]:
    payload = eval_case_to_agent_payload(case)
    if retrieved_observations is not None:
        payload["retrieved_observations"] = retrieved_observations
    if strategy_points is not None:
        payload["strategy_points"] = strategy_points

    spec = action_spec_for(case)
    result = _run_agent(
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

    if spec.output_key == "day_channel":
        messages = result.get("day_channel", [])
        if messages:
            agent_message = messages[0]
        strategies = result.get("agent_strategies", {})
        if isinstance(strategies, dict):
            updated_strategy = strategies.get(case.player_id, "") or ""
    elif spec.output_key == "day_votes":
        votes = result.get("day_votes", [])
        if votes:
            agent_vote = votes[0]

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
