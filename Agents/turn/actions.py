from logging import getLogger
from typing import Any

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime
from pydantic import BaseModel


from Agents.tracing import GraphContext, langfuse

from Agents.prompts.prompt_formatters import (
    format_day_channel,
    format_day_summaries,
    format_investigator_results,
    format_wolf_channel,
)
from Agents.memory.enrichment import enrich_payload_with_memory
from Agents.observability import action_eval_span_name, freeze_case
from Agents.schemas import (
    EvalCase,
    EvalProvenance,
    NightAction,
)
from Agents.schemas.game_events import (
    DayChannel,
    DayVote,
)
from Agents.state import (
    HealerDayState,
    InvestigatorDayState,
    VillagerDayState,
    WolfDayState,
)
from Agents.turn.agent import _run_agent
from Agents.turn.adoption import _process_strategy_adoption
from Agents.turn.eval import _build_eval_private_context

logger = getLogger(__name__)


def _run_memory_informed_action(
    payload: VillagerDayState | HealerDayState | WolfDayState | InvestigatorDayState,
    config: RunnableConfig,
    runtime: Runtime[GraphContext],
    action_phase: str,
    prompt_template: ChatPromptTemplate,
    output_schema: type[BaseModel],
    output_key: str,
) -> dict[str, Any] | None:
    player_id = payload["player_id"]
    role = payload["player_role"]
    day = payload["current_day"]
    round_num = payload["current_round"]
    prompt_payload = dict(payload)

    recent_messages = [message for message in payload["day_channel"] if message.day == day]
    visible_discussion = (
        format_day_channel(recent_messages)
        if recent_messages
        else "No events yet today."
    )

    span_name = action_eval_span_name(player_id, day, round_num, action_phase)
    with langfuse.start_as_current_observation(
        as_type="span",
        name=span_name,
        input={
            "player_id": player_id,
            "player_role": role,
            "day": day,
            "round": round_num,
            "action_phase": action_phase,
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
        enriched_payload, retrieval_meta = enrich_payload_with_memory(
            prompt_payload,
            config,
            runtime,
            action_phase,
        )
        result = _run_agent(
            enriched_payload,
            prompt_template,
            output_schema,
            output_key,
        )

        # --- Adoption processing ---
        # Capture the full verdict list for the EvalCase BEFORE adoption pops the carrier off `result`.
        strategy_verdicts = (result or {}).get("_strategy_verdicts", [])
        raw_adopted_indices, adopted_store_keys, strategy_adoptions = (
            _process_strategy_adoption(
                result,
                enriched_payload,
                runtime,
                player_id=player_id,
                role=role,
                action_phase=action_phase,
                day=day,
                round_num=round_num,
            )
        )

        # --- Process output for graph state ---
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
                strategies = result.get("agent_strategies", {})
                if isinstance(strategies, dict):
                    updated_strategy = strategies.get(player_id, "") or ""
                if updated_strategy:
                    applied_game_update["agent_strategies"] = {
                        player_id: updated_strategy
                    }

            if strategy_adoptions:
                result["strategy_adoptions"] = strategy_adoptions

        eval_case = EvalCase(
            span_name=span_name,
            player_id=player_id,
            player_role=role,
            day=day,
            round=round_num,
            action_phase=action_phase,
            visible_discussion=recent_messages,
            private_context=_build_eval_private_context(payload, day),
            memory_enabled=retrieval_meta["memory_enabled"],
            retrieval_skipped_reason=retrieval_meta["retrieval_skipped_reason"],
            situations=retrieval_meta["situations"],
            retrieved_observations=retrieval_meta["retrieved_observations"],
            retrieved_strategy_points=retrieval_meta["retrieved_strategy_points"],
            candidate_observations=retrieval_meta["candidate_observations"],
            candidate_strategy_points=retrieval_meta["candidate_strategy_points"],
            provenance=EvalProvenance(
                store_dir=retrieval_meta["store_dir"],
                reranking_enabled=retrieval_meta["reranking_enabled"],
                filtering_enabled=retrieval_meta["filtering_enabled"],
            ),
            agent_message=agent_message,
            agent_vote=agent_vote,
            updated_strategy=updated_strategy,
            adopted_strategy_keys=raw_adopted_indices,
            adopted_strategy_store_keys=adopted_store_keys,
            strategy_verdicts=strategy_verdicts,
            memory_applicability=(result or {}).get("_memory_applicability", []),
        )

        eval_span.update(
            output={
                "eval_case": freeze_case(
                    eval_span,
                    eval_case,
                    kind="agent_action_eval",
                    case_key="eval_case",
                    sink=runtime.context.get("eval_sink"),
                ),
                "applied_game_update": applied_game_update,
            },
            metadata={
                "eval_schema": eval_case.schema_version,
                "retrieval_top_k": 3,
                "memory_enabled": eval_case.memory_enabled,
                "retrieval_skipped_reason": eval_case.retrieval_skipped_reason,
                "action_phase": eval_case.action_phase,
                "player_id": eval_case.player_id,
                "player_role": eval_case.player_role,
                "day": eval_case.day,
                "round": eval_case.round,
                "adopted_count": len(adopted_store_keys),
            },
        )

    return result


def _run_memory_informed_night_action(
    payload: dict[str, Any],
    config: RunnableConfig,
    runtime: Runtime[GraphContext],
    prompt_template: ChatPromptTemplate,
    output_schema: type[BaseModel],
    output_key: str,
) -> dict[str, Any] | None:
    """Night counterpart of ``_run_memory_informed_action`` for single-target roles.

    A night action selects a target instead of producing a message/vote, so the
    eval case carries ``agent_night_action`` rather than ``agent_message``/
    ``agent_vote``. Retrieval, adoption bookkeeping, and the eval span are
    otherwise identical to the day path (and gated by the same ``memory_config``).
    """
    player_id = payload["player_id"]
    role = payload["player_role"]
    day = payload["current_day"]
    round_num = payload.get("current_round", 0)
    action_phase = "night_action"

    span_name = action_eval_span_name(player_id, day, round_num, action_phase)
    with langfuse.start_as_current_observation(
        as_type="span",
        name=span_name,
        input={
            "player_id": player_id,
            "player_role": role,
            "day": day,
            "round": round_num,
            "action_phase": action_phase,
            "previous_strategy": payload.get("previous_strategy", "") or "",
            "day_summaries": format_day_summaries(
                payload.get("day_summaries", []),
                before_day=day,
            ),
            "wolf_channel": format_wolf_channel(payload.get("wolf_channel", [])),
            "investigator_results": format_investigator_results(
                payload.get("investigator_results", [])
            ),
            "vigilante_results": payload.get("vigilante_results", []),
            "surviving_players": payload.get("surviving_players", []),
        },
        metadata={
            "eval_schema": "retrieval_action_v1",
            "retrieval_top_k": 3,
        },
    ) as eval_span:
        enriched_payload, retrieval_meta = enrich_payload_with_memory(
            payload,
            config,
            runtime,
            action_phase,
        )
        result = _run_agent(
            enriched_payload,
            prompt_template,
            output_schema,
            output_key,
        )

        strategy_verdicts = (result or {}).get("_strategy_verdicts", [])
        raw_adopted_indices, adopted_store_keys, strategy_adoptions = (
            _process_strategy_adoption(
                result,
                enriched_payload,
                runtime,
                player_id=player_id,
                role=role,
                action_phase=action_phase,
                day=day,
                round_num=round_num,
            )
        )

        applied_game_update: dict[str, Any] | None = None
        target: str | None = None
        updated_strategy = ""
        if result:
            applied_game_update = {}
            if output_key == "wolf_channel":
                # Wolf night is a discussion turn that carries a kill vote; the
                # decision we evaluate is this wolf's vote. The turn produces a
                # WolfChannel (message + vote) and folds its strategy update into
                # agent_strategies (not a flat updated_strategy), so unpack both.
                messages = result.get("wolf_channel", [])
                applied_game_update["wolf_channel"] = messages
                if messages:
                    first = messages[0]
                    target = (
                        first.get("vote") if isinstance(first, dict)
                        else getattr(first, "vote", None)
                    )
                strategies = result.get("agent_strategies", {})
                if isinstance(strategies, dict):
                    updated_strategy = strategies.get(player_id, "") or ""
                if updated_strategy:
                    applied_game_update["agent_strategies"] = strategies
            else:
                target = result.get(output_key)
                applied_game_update[output_key] = target
                updated_strategy = result.get("updated_strategy", "") or ""
            if strategy_adoptions:
                result["strategy_adoptions"] = strategy_adoptions

        eval_case = EvalCase(
            span_name=span_name,
            player_id=player_id,
            player_role=role,
            day=day,
            round=round_num,
            action_phase=action_phase,
            visible_discussion=[],
            private_context=_build_eval_private_context(payload, day),
            memory_enabled=retrieval_meta["memory_enabled"],
            retrieval_skipped_reason=retrieval_meta["retrieval_skipped_reason"],
            situations=retrieval_meta["situations"],
            retrieved_observations=retrieval_meta["retrieved_observations"],
            retrieved_strategy_points=retrieval_meta["retrieved_strategy_points"],
            candidate_observations=retrieval_meta["candidate_observations"],
            candidate_strategy_points=retrieval_meta["candidate_strategy_points"],
            provenance=EvalProvenance(
                store_dir=retrieval_meta["store_dir"],
                reranking_enabled=retrieval_meta["reranking_enabled"],
                filtering_enabled=retrieval_meta["filtering_enabled"],
            ),
            agent_night_action=NightAction(role=role, target=target),
            updated_strategy=updated_strategy,
            adopted_strategy_keys=raw_adopted_indices,
            adopted_strategy_store_keys=adopted_store_keys,
            strategy_verdicts=strategy_verdicts,
            memory_applicability=(result or {}).get("_memory_applicability", []),
        )

        eval_span.update(
            output={
                "eval_case": freeze_case(
                    eval_span,
                    eval_case,
                    kind="agent_action_eval",
                    case_key="eval_case",
                    sink=runtime.context.get("eval_sink"),
                ),
                "applied_game_update": applied_game_update,
            },
            metadata={
                "eval_schema": eval_case.schema_version,
                "retrieval_top_k": 3,
                "memory_enabled": eval_case.memory_enabled,
                "retrieval_skipped_reason": eval_case.retrieval_skipped_reason,
                "action_phase": eval_case.action_phase,
                "player_id": eval_case.player_id,
                "player_role": eval_case.player_role,
                "day": eval_case.day,
                "round": eval_case.round,
                "adopted_count": len(adopted_store_keys),
            },
        )

    return result


