import os
from functools import lru_cache
from logging import getLogger
from typing import Any, Literal
import random

from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableConfig
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.runtime import Runtime
from pydantic import BaseModel, create_model

from Agents.tracing import GraphContext, langfuse

from Agents.formatters import (
    format_day_channel,
    format_day_summaries,
    format_investigator_results,
    format_wolf_channel,
)
from Agents.memory import (
    retrieve_observations_for_agent,
    retrieve_strategy_points_for_agent,
)
from Agents.prompts import (
    HEALER_DAY_DISCUSS,
    HEALER_DAY_VOTE,
    HEALER_NIGHT,
    HEALER_SITUATION_SUMMARY,
    INVESTIGATOR_DAY_DISCUSS,
    INVESTIGATOR_DAY_VOTE,
    INVESTIGATOR_NIGHT,
    INVESTIGATOR_SITUATION_SUMMARY,
    VILLAGER_SITUATION_SUMMARY,
    VILLAGER_DAY_DISCUSS,
    VILLAGER_DAY_VOTE,
    WOLF_SITUATION_SUMMARY,
    WOLF_DAY_DISCUSS,
    WOLF_DAY_VOTE,
    WOLF_NIGHT_DISCUSS,
)
from Agents.prompt_inputs import build_agent_prompt_input as _build_agent_prompt_input
from Agents.schemas import (
    DayDiscussOutput,
    DayVoteOutput,
    EvalCase,
    EvalPrivateContext,
    HealerOutput,
    InvestigatorOutput,
    SituationSummary,
    WolfNightDiscussOutput,
)
from Agents.schemas.game_events import (
    DayChannel,
    DayVote,
    WolfChannel,
)
from Agents.state import (
    HealerDayState,
    HealerNightGraph,
    InvestigatorDayState,
    InvestigatorNightGraph,
    VillagerDayState,
    WolfDayState,
    WolfNightState,
)

load_dotenv()
logger = getLogger(__name__)
prompt_log: list[dict] = []

DEFAULT_GAME_MODEL = "gemini-3.1-flash-lite"
DEFAULT_GAME_THINKING_LEVEL = "minimal"
DEFAULT_PRO_BACKUP_MODEL = "gemini-3.1-pro"
VALID_THINKING_LEVELS = {"minimal", "low", "medium", "high"}


def _thinking_level_from_env(
    env_var: str,
    default: str | None = None,
) -> str | None:
    value = os.getenv(env_var, default)
    if value is None:
        return None

    normalized = value.strip().lower()
    if normalized in {"", "none", "default"}:
        return None
    if normalized not in VALID_THINKING_LEVELS:
        valid = ", ".join(sorted(VALID_THINKING_LEVELS))
        raise ValueError(f"{env_var} must be one of: {valid}")
    return normalized


@lru_cache(maxsize=1)
def get_llm():
    google_api_key = os.getenv("GOOGLE_API_KEY")
    kwargs: dict[str, Any] = {
        "model": os.getenv("GOOGLE_GENAI_MODEL", DEFAULT_GAME_MODEL),
        "temperature": float(os.getenv("GOOGLE_GENAI_TEMPERATURE", "1.0")),
    }
    thinking_level = _thinking_level_from_env(
        "GOOGLE_GENAI_THINKING_LEVEL",
        DEFAULT_GAME_THINKING_LEVEL,
    )
    if thinking_level:
        kwargs["thinking_level"] = thinking_level
    if google_api_key:
        kwargs["google_api_key"] = google_api_key
    return ChatGoogleGenerativeAI(**kwargs)

@lru_cache(maxsize=1)
def get_llm_pro():
    google_api_key = os.getenv("GOOGLE_API_KEY")
    kwargs: dict[str, Any] = {
        "model": os.getenv("GOOGLE_GENAI_PRO_MODEL", "gemini-2.5-pro"),
        "temperature": float(os.getenv("GOOGLE_GENAI_TEMPERATURE", "1.0")),
    }
    if google_api_key:
        kwargs["google_api_key"] = google_api_key
    return ChatGoogleGenerativeAI(**kwargs)


@lru_cache(maxsize=1)
def get_llm_pro_backup():
    google_api_key = os.getenv("GOOGLE_API_KEY")
    kwargs: dict[str, Any] = {
        "model": os.getenv("GOOGLE_GENAI_PRO_BACKUP_MODEL", DEFAULT_PRO_BACKUP_MODEL),
        "temperature": float(os.getenv("GOOGLE_GENAI_TEMPERATURE", "1.0")),
    }
    thinking_level = _thinking_level_from_env(
        "GOOGLE_GENAI_PRO_BACKUP_THINKING_LEVEL",
    )
    if thinking_level:
        kwargs["thinking_level"] = thinking_level
    if google_api_key:
        kwargs["google_api_key"] = google_api_key
    return ChatGoogleGenerativeAI(**kwargs)


def _validate_target(target: str, valid_targets: list[str], player_id: str) -> str | None:
    """Returns the target if valid, None if not."""
    if target in valid_targets and target != player_id:
        return target
    return None


def _valid_targets_for_action(payload: dict[str, Any], output_key: str) -> list[str]:
    player_id = payload.get("player_id", "")
    if output_key == "wolf_channel":
        targets = payload.get("surviving_villagers", [])
    elif output_key in {"day_votes", "healer_target", "investigator_target"}:
        targets = payload.get("surviving_players", [])
    else:
        return []
    return [target for target in targets if target != player_id]


def _target_field_for_output_key(output_key: str) -> str | None:
    if output_key in {"day_votes", "wolf_channel"}:
        return "vote_target"
    if output_key in {"healer_target", "investigator_target"}:
        return output_key
    return None


def _with_dynamic_target_enum(
    output_schema: type[BaseModel],
    output_key: str,
    valid_targets: list[str],
) -> type[BaseModel]:
    target_field = _target_field_for_output_key(output_key)
    if not target_field or not valid_targets:
        return output_schema

    target_literal = Literal[tuple(valid_targets)]
    fields: dict[str, tuple[Any, Any]] = {}
    for field_name, field in output_schema.model_fields.items():
        annotation = target_literal if field_name == target_field else field.annotation
        default = ... if field.is_required() else field.default
        fields[field_name] = (annotation, default)

    return create_model(
        f"{output_schema.__name__}_{output_key}_TargetEnum",
        **fields,
    )


def _run_agent(
    payload: dict[str, Any],
    prompt_template: ChatPromptTemplate,
    output_schema: type[BaseModel],
    output_key: str,
    max_retries: int = 1
) -> dict[str, Any] | None:
    valid_targets = _valid_targets_for_action(payload, output_key)
    effective_output_schema = _with_dynamic_target_enum(
        output_schema,
        output_key,
        valid_targets,
    )
    chain = prompt_template | get_llm().with_structured_output(effective_output_schema)
    prompt_input = _build_agent_prompt_input(payload)

    player_id = payload.get("player_id", "")
    prompt_log.append(
        {
            "player_id": player_id,
            "player_role": payload.get("player_role", ""),
            "output_key": output_key,
            "day": payload.get("current_day", 1),
            "round": payload.get("current_round", 1),
            "prompt_input": prompt_input.copy(),
        }
    )

    for attempt in range(max_retries + 1):
        try:
            result = chain.invoke(
                prompt_input,
                config={"run_name": f"{output_key}_{player_id}"},
            )
        except Exception as e:
            logger.warning(f"LLM call failed for {player_id}: {e}")
            if attempt < max_retries:
                continue
            break

        # Extract strategy if present on the result
        strategy_update = getattr(result, "updated_strategy", None)

        if output_key == "day_channel":
            message = result.message.strip() if result.message else None
            if not message or message.lower() == "null":
                # Agent chose silence — still update strategy, no public message
                output = {}
                if strategy_update:
                    output["agent_strategies"] = {player_id: strategy_update}
                return output if output else None
            output = {
                "day_channel": [
                    DayChannel(
                        day=payload.get("current_day", 1),
                        round=payload.get("current_round", 1),
                        player=player_id,
                        message=message,
                    )
                ]
            }
            if strategy_update:
                output["agent_strategies"] = {player_id: strategy_update}
            return output

        if output_key == "day_votes":
            validated = _validate_target(
                result.vote_target,
                valid_targets,
                player_id,
            )
            if validated:
                return {"day_votes": [DayVote(voter=player_id, votee=validated)]}
            logger.warning(f"{player_id} voted for invalid target: {result.vote_target}")
            continue

        if output_key == "wolf_channel":
            validated = _validate_target(
                result.vote_target,
                valid_targets,
                player_id,
            )
            if validated:
                output = {
                    "wolf_channel": [
                        WolfChannel(
                            day=payload.get("current_day", 1),
                            round=payload.get("current_round", 1),
                            wolf=player_id,
                            message=result.message,
                            vote=validated,
                        )
                    ]
                }
                if strategy_update:
                    output["agent_strategies"] = {player_id: strategy_update}
                return output
            logger.warning(f"{player_id} voted for invalid target: {result.vote_target}")
            continue

        if output_key == "healer_target":
            validated = _validate_target(
                result.healer_target,
                valid_targets,
                player_id,
            )
            if validated:
                output = {"healer_target": validated}
                if strategy_update:
                    output["updated_strategy"] = strategy_update
                return output
            logger.warning(f"Healer targeted invalid player: {result.healer_target}")
            continue

        if output_key == "investigator_target":
            validated = _validate_target(
                result.investigator_target,
                valid_targets,
                player_id,
            )
            if validated:
                output = {"investigator_target": validated}
                if strategy_update:
                    output["updated_strategy"] = strategy_update
                return output
            logger.warning(f"Investigator targeted invalid player: {result.investigator_target}")
            continue

    # All retries exhausted — random fallback
    logger.error(f"{player_id} failed all retries, using random fallback")
    if output_key == "day_votes":
        fallback = random.choice(valid_targets)
        return {"day_votes": [DayVote(voter=player_id, votee=fallback)]}
    if output_key in ("healer_target", "investigator_target"):
        fallback = random.choice(valid_targets)
        return {output_key: fallback}
    if output_key == "wolf_channel":
        fallback = random.choice(valid_targets)
        return {"wolf_channel": [WolfChannel(
            day=payload.get("current_day", 1),
            round=payload.get("current_round", 1),
            wolf=player_id,
            message="...",
            vote=fallback,
        )]}

    return None


def _generate_situations_for_agent(
    payload: VillagerDayState | HealerDayState | WolfDayState | InvestigatorDayState,
    max_retries: int = 1,
) -> list[str]:
    player_id = payload["player_id"]
    role = payload["player_role"]
    current_day = payload["current_day"]
    current_round = payload["current_round"]
    prompt_template = {
        "villager": VILLAGER_SITUATION_SUMMARY,
        "healer": HEALER_SITUATION_SUMMARY,
        "investigator": INVESTIGATOR_SITUATION_SUMMARY,
        "wolf": WOLF_SITUATION_SUMMARY,
    }.get(role, VILLAGER_SITUATION_SUMMARY)
    chain = prompt_template | get_llm().with_structured_output(SituationSummary)

    for attempt in range(max_retries + 1):
        try:
            result = chain.invoke(
                _build_agent_prompt_input(payload),
                config={
                    "run_name": (
                        f"situation_summary_{role}_day_{current_day}_round_{current_round}"
                    )
                },
            )
            return result.situations
        except Exception as e:
            logger.warning(f"Situation summary LLM call failed for {player_id}: {e}")
            if attempt < max_retries:
                continue
            break

    logger.error(f"{player_id} situation summary failed all retries, using fallback")
    return [f"Day {current_day} as {role}, round {current_round}"]


def _memory_enabled_for_role(config: RunnableConfig, role: str) -> bool:
    configurable = config.get("configurable", {}) if config else {}
    memory_config = configurable.get("memory_config")
    if not isinstance(memory_config, dict):
        return True
    return bool(memory_config.get(role, False))


def _enrich_payload_with_memory(
    payload: VillagerDayState | HealerDayState | WolfDayState | InvestigatorDayState,
    config: RunnableConfig,
    runtime: Runtime[GraphContext],
    action_type: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    enriched_payload = dict(payload)

    active_store = runtime.store
    skip_reason = None
    if payload["current_day"] == 1:
        skip_reason = "day_1"
    elif active_store is None:
        skip_reason = "no_store"
    elif not _memory_enabled_for_role(config, payload["player_role"]):
        skip_reason = "memory_disabled_for_role"

    if skip_reason:
        enriched_payload["retrieved_observations"] = []
        enriched_payload["strategy_points"] = payload.get(
            "strategy_points",
            [],
        )
        return enriched_payload, {
            "memory_enabled": False,
            "retrieval_skipped_reason": skip_reason,
            "situations": [],
            "retrieved_observations": [],
            "retrieved_strategy_points": [],
            "num_situations": 0,
            "num_observations": 0,
            "num_strategy_points": 0,
        }

    situations = _generate_situations_for_agent(payload)
    with langfuse.start_as_current_observation(
        as_type="retriever",
        name=(
            f"memory_retrieval_{payload['player_id']}"
            f"_day_{payload['current_day']}_round_{payload['current_round']}"
        ),
        input={"situations": situations},
        metadata={
            "player_id": payload["player_id"],
            "player_role": payload["player_role"],
            "current_day": payload["current_day"],
            "current_round": payload["current_round"],
            "action_type": action_type,
        },
    ) as span:
        retrieved_observations = retrieve_observations_for_agent(
            store=active_store,
            role=payload["player_role"],
            situations=situations,
        )
        retrieved_strategy_points = retrieve_strategy_points_for_agent(
            store=active_store,
            role=payload["player_role"],
            situations=situations,
        )
        retrieved_observations_json = [
            item.model_dump(mode="json") for item in retrieved_observations
        ]
        retrieved_strategy_points_json = [
            item.model_dump(mode="json") for item in retrieved_strategy_points
        ]
        span.update(
            output={
                "retrieved_observations": retrieved_observations_json,
                "retrieved_strategy_points": retrieved_strategy_points_json,
            },
            metadata={
                "num_situations": len(situations),
                "num_observations": len(retrieved_observations),
                "num_strategy_points": len(retrieved_strategy_points),
                "observation_scores": [item.score for item in retrieved_observations],
                "strategy_point_scores": [item.score for item in retrieved_strategy_points],
            }
        )

    enriched_payload["retrieved_observations"] = retrieved_observations
    enriched_payload["strategy_points"] = retrieved_strategy_points
    return enriched_payload, {
        "memory_enabled": True,
        "retrieval_skipped_reason": None,
        "situations": situations,
        "retrieved_observations": retrieved_observations_json,
        "retrieved_strategy_points": retrieved_strategy_points_json,
        "num_situations": len(situations),
        "num_observations": len(retrieved_observations),
        "num_strategy_points": len(retrieved_strategy_points),
    }


def _run_memory_informed_action(
    payload: VillagerDayState | HealerDayState | WolfDayState | InvestigatorDayState,
    config: RunnableConfig,
    runtime: Runtime[GraphContext],
    action_type: str,
    prompt_template: ChatPromptTemplate,
    output_schema: type[BaseModel],
    output_key: str,
) -> dict[str, Any] | None:
    player_id = payload["player_id"]
    role = payload["player_role"]
    day = payload["current_day"]
    round_num = payload["current_round"]

    recent_messages = [message for message in payload["day_channel"] if message.day == day]
    visible_discussion = (
        format_day_channel(recent_messages)
        if recent_messages
        else "No events yet today."
    )

    span_name = (
        f"agent_action_eval_{player_id}"
        f"_day_{day}_round_{round_num}_{action_type}"
    )
    with langfuse.start_as_current_observation(
        as_type="span",
        name=span_name,
        input={
            "player_id": player_id,
            "player_role": role,
            "day": day,
            "round": round_num,
            "action_type": action_type,
            "visible_discussion": visible_discussion,
            "previous_strategy": payload.get("previous_strategy", "") or "",
            "day_summaries": format_day_summaries(
                payload.get("day_summaries", []),
                before_day=day,
            ),
            "wolf_channel": format_wolf_channel(payload.get("wolf_channel", [])),
            "investigator_results": format_investigator_results(
                payload.get("investigator_results", [])
            ),
            "surviving_players": payload.get("surviving_players", []),
            "surviving_wolves": payload.get("surviving_wolves", []),
            "surviving_villagers": payload.get("surviving_villagers", []),
        },
        metadata={
            "eval_schema": "retrieval_action_v1",
            "retrieval_top_k": 3,
        },
    ) as eval_span:
        enriched_payload, retrieval_meta = _enrich_payload_with_memory(
            payload,
            config,
            runtime,
            action_type,
        )
        result = _run_agent(
            enriched_payload,
            prompt_template,
            output_schema,
            output_key,
        )

        applied_output = None
        applied_game_update: dict[str, Any] | None = None
        agent_message: DayChannel | None = None
        agent_vote: DayVote | None = None
        updated_strategy = ""
        if result:
            applied_game_update = {}
            if output_key == "day_channel":
                messages = result.get("day_channel", [])
                if messages:
                    agent_message = messages[0]
                applied_output = [
                    message.model_dump(mode="json")
                    if hasattr(message, "model_dump")
                    else message
                    for message in messages
                ]
                if applied_output:
                    applied_game_update["day_channel"] = applied_output
                strategies = result.get("agent_strategies", {})
                if isinstance(strategies, dict):
                    updated_strategy = strategies.get(player_id, "") or ""
                if updated_strategy:
                    applied_game_update["agent_strategies"] = {
                        player_id: updated_strategy
                    }
            elif output_key == "day_votes":
                votes = result.get("day_votes", [])
                if votes:
                    agent_vote = votes[0]
                applied_output = [
                    vote.model_dump(mode="json")
                    if hasattr(vote, "model_dump")
                    else vote
                    for vote in votes
                ]
                if applied_output:
                    applied_game_update["day_votes"] = applied_output

        eval_case = EvalCase(
            span_name=span_name,
            player_id=player_id,
            player_role=role,
            day=day,
            round=round_num,
            action_type=action_type,
            visible_discussion=recent_messages,
            private_context=EvalPrivateContext(
                previous_strategy=payload.get("previous_strategy", "") or "",
                day_summaries=[
                    summary
                    for summary in payload.get("day_summaries", [])
                    if summary.day < day
                ],
                wolf_channel=payload.get("wolf_channel", []),
                investigator_results=payload.get("investigator_results", []),
                surviving_players=payload.get("surviving_players", []),
                surviving_wolves=payload.get("surviving_wolves", []),
                surviving_villagers=payload.get("surviving_villagers", []),
            ),
            memory_enabled=retrieval_meta["memory_enabled"],
            retrieval_skipped_reason=retrieval_meta["retrieval_skipped_reason"],
            situations=retrieval_meta["situations"],
            retrieved_observations=retrieval_meta["retrieved_observations"],
            retrieved_strategy_points=retrieval_meta["retrieved_strategy_points"],
            agent_message=agent_message,
            agent_vote=agent_vote,
            updated_strategy=updated_strategy,
        )

        eval_span.update(
            output={
                "eval_case": eval_case.model_dump(mode="json"),
                "applied_game_update": applied_game_update,
            },
            metadata={
                "eval_schema": eval_case.schema_version,
                "retrieval_top_k": 3,
                "memory_enabled": eval_case.memory_enabled,
                "retrieval_skipped_reason": eval_case.retrieval_skipped_reason,
                "action_type": eval_case.action_type,
                "player_id": eval_case.player_id,
                "player_role": eval_case.player_role,
                "day": eval_case.day,
                "round": eval_case.round,
            },
        )

    return result


def villager_discuss(
    payload: VillagerDayState,
    config: RunnableConfig,
    runtime: Runtime[GraphContext],
):
    return _run_memory_informed_action(
        payload,
        config,
        runtime,
        "discussion",
        VILLAGER_DAY_DISCUSS,
        DayDiscussOutput,
        "day_channel",
    )


def healer_discuss(
    payload: HealerDayState,
    config: RunnableConfig,
    runtime: Runtime[GraphContext],
):
    return _run_memory_informed_action(
        payload,
        config,
        runtime,
        "discussion",
        HEALER_DAY_DISCUSS,
        DayDiscussOutput,
        "day_channel",
    )


def wolf_discuss(
    payload: WolfDayState,
    config: RunnableConfig,
    runtime: Runtime[GraphContext],
):
    return _run_memory_informed_action(
        payload,
        config,
        runtime,
        "discussion",
        WOLF_DAY_DISCUSS,
        DayDiscussOutput,
        "day_channel",
    )


def investigator_discuss(
    payload: InvestigatorDayState,
    config: RunnableConfig,
    runtime: Runtime[GraphContext],
):
    return _run_memory_informed_action(
        payload,
        config,
        runtime,
        "discussion",
        INVESTIGATOR_DAY_DISCUSS,
        DayDiscussOutput,
        "day_channel",
    )


def villager_vote(
    payload: VillagerDayState,
    config: RunnableConfig,
    runtime: Runtime[GraphContext],
):
    return _run_memory_informed_action(
        payload,
        config,
        runtime,
        "vote",
        VILLAGER_DAY_VOTE,
        DayVoteOutput,
        "day_votes",
    )


def healer_vote(
    payload: HealerDayState,
    config: RunnableConfig,
    runtime: Runtime[GraphContext],
):
    return _run_memory_informed_action(
        payload,
        config,
        runtime,
        "vote",
        HEALER_DAY_VOTE,
        DayVoteOutput,
        "day_votes",
    )


def wolf_vote(
    payload: WolfDayState,
    config: RunnableConfig,
    runtime: Runtime[GraphContext],
):
    return _run_memory_informed_action(
        payload,
        config,
        runtime,
        "vote",
        WOLF_DAY_VOTE,
        DayVoteOutput,
        "day_votes",
    )


def investigator_vote(
    payload: InvestigatorDayState,
    config: RunnableConfig,
    runtime: Runtime[GraphContext],
):
    return _run_memory_informed_action(
        payload,
        config,
        runtime,
        "vote",
        INVESTIGATOR_DAY_VOTE,
        DayVoteOutput,
        "day_votes",
    )


def wolf_night_discuss(payload: WolfNightState):
    return _run_agent(
        payload, WOLF_NIGHT_DISCUSS, WolfNightDiscussOutput, "wolf_channel"
    )


def healer_act(payload: HealerNightGraph):
    return _run_agent(payload, HEALER_NIGHT, HealerOutput, "healer_target")


def investigator_act(payload: InvestigatorNightGraph):
    return _run_agent(
        payload, INVESTIGATOR_NIGHT, InvestigatorOutput, "investigator_target"
    )
