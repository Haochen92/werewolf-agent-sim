from logging import getLogger
from typing import Any, Literal
import random

from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime
from pydantic import BaseModel, create_model

from Agents.llm_factory import get_llm, get_llm_judge

from Agents.tracing import GraphContext, langfuse

from Agents.formatters import (
    format_day_channel,
    format_day_summaries,
    format_investigator_results,
    format_wolf_channel,
)
from Agents.memory.enrichment import _enrich_payload_with_memory
from Agents.prompts import (
    HEALER_DAY_DISCUSS,
    HEALER_DAY_VOTE,
    HEALER_NIGHT,
    INVESTIGATOR_DAY_DISCUSS,
    INVESTIGATOR_DAY_VOTE,
    INVESTIGATOR_NIGHT,
    SERIAL_KILLER_DAY_DISCUSS,
    SERIAL_KILLER_DAY_VOTE,
    SERIAL_KILLER_NIGHT,
    VIGILANTE_DAY_DISCUSS,
    VIGILANTE_DAY_VOTE,
    VIGILANTE_NIGHT,
    VILLAGER_DAY_DISCUSS,
    VILLAGER_DAY_VOTE,
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
    EvalProvenance,
    HealerOutput,
    InvestigatorOutput,
    NightAction,
    NoveltyJudgment,
    SerialKillerOutput,
    VigilanteOutput,
    WolfNightDiscussOutput,
)
from Agents.schemas.game_events import (
    DayChannel,
    DayVote,
    WolfChannel,
)
from Agents.schemas.memory import StrategyAdoption
from Agents.graphs.state import (
    HealerDayState,
    HealerNightGraph,
    InvestigatorDayState,
    InvestigatorNightGraph,
    SerialKillerNightGraph,
    VigilanteNightGraph,
    VillagerDayState,
    WolfDayState,
    WolfNightState,
)

load_dotenv()
logger = getLogger(__name__)
prompt_log: list[dict] = []


NOVELTY_JUDGE_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """You judge whether a new message in an ongoing Werewolf day discussion adds NEW substance.

NOVEL (novel=true) — it introduces at least one of:
- a new argument, observation, or piece of evidence not already raised,
- a new or changed suspicion, or a concrete proposal/question that moves things forward,
- a direct response to a specific player (answering or defending).

NOT NOVEL (novel=false) — it merely:
- restates or agrees with a point already made,
- echoes the general sentiment ("let's be cautious", "watch for X") without adding anything,
- reinforces an existing accusation with no new angle or evidence.

Lean toward novel=true when genuinely uncertain; only gate clear restatement/echo.""",
        ),
        (
            "human",
            """Discussion so far:
{day_channel}

New message from {player_id}:
"{candidate_message}"

Does this add new substance, or is it restatement/echo?""",
        ),
    ]
)


def judge_proactive_novelty(candidate_message: str, payload: dict[str, Any], current_day: int) -> bool:
    """External novelty judge for a PROACTIVE utterance. True = keep, False = gate to a pass.

    Disinterested third-party judge (not self-assessment — the form Smoke 2/3 validated).
    Fails open (True) on the opener (nothing to echo yet) or any judge error, so the gate
    never silences a legitimate turn due to its own failure.
    """
    today = [
        m for m in payload.get("day_channel", [])
        if m.day == current_day and m.player != "game_master" and not getattr(m, "passed", False)
    ]
    if not today:
        return True
    try:
        result = (
            NOVELTY_JUDGE_PROMPT | get_llm_judge().with_structured_output(NoveltyJudgment)
        ).invoke(
            {
                "day_channel": format_day_channel(today),
                "candidate_message": candidate_message,
                "player_id": payload.get("player_id", ""),
            },
            config={"run_name": f"novelty_judge_{payload.get('player_id', '')}"},
        )
        return bool(result.novel)
    except Exception as exc:
        logger.warning(f"novelty judge failed: {exc}; defaulting to novel")
        return True


def _validate_target(target: str, valid_targets: list[str], player_id: str) -> str | None:
    """Returns the target if valid, None if not."""
    if target in valid_targets and target != player_id:
        return target
    return None


def _valid_targets_for_action(payload: dict[str, Any], output_key: str) -> list[str]:
    player_id = payload.get("player_id", "")
    if output_key == "wolf_channel":
        targets = payload.get("surviving_villagers", [])
    elif output_key in {
        "day_votes",
        "healer_target",
        "investigator_target",
        "serial_killer_target",
        "vigilante_target",
    }:
        targets = payload.get("surviving_players", [])
    else:
        return []
    valid = [target for target in targets if target != player_id]
    # Relaxed voting: "abstain" is a sentinel target that competes in the tally; an
    # abstain plurality (or tie) yields no lynch. Dropped on a forced day.
    if output_key == "day_votes" and payload.get("allow_abstain"):
        valid.append("abstain")
    # The vigilante may hold fire to save a bullet (the SK is compulsive — no sentinel).
    if output_key == "vigilante_target":
        valid.append("hold_fire")
    return valid


def _target_field_for_output_key(output_key: str) -> str | None:
    if output_key in {"day_votes", "wolf_channel"}:
        return "vote_target"
    if output_key in {
        "healer_target",
        "investigator_target",
        "serial_killer_target",
        "vigilante_target",
    }:
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

        # Extract strategy and adoption data if present on the result
        strategy_update = getattr(result, "updated_strategy", None)
        adopted_indices = getattr(result, "adopted_strategy_keys", []) or []

        if output_key == "day_channel":
            current_day = payload.get("current_day", 1)
            firing_reason = payload.get("firing_reason")  # scheduler trace; rides the Send
            seq = sum(1 for m in payload.get("day_channel", []) if m.day == current_day)

            # Reactive picks must answer: a reactive pass wouldn't discharge the obligation,
            # so the scheduler would just re-pick them. Honor pass_turn only when not reactive.
            is_reactive = firing_reason is not None and firing_reason.tier == "reactive"
            pass_turn = getattr(result, "pass_turn", False) and not is_reactive

            if pass_turn:
                # Proactive decline -> hidden pass marker (the stateless scheduler reads it).
                entry = DayChannel(
                    day=current_day, seq=seq, player=player_id,
                    message="", passed=True, firing_reason=firing_reason,
                )
            else:
                message = result.message.strip() if result.message else None
                if not message or message.lower() == "null":
                    output = {}
                    if strategy_update:
                        output["agent_strategies"] = {player_id: strategy_update}
                    if adopted_indices:
                        output["_adopted_strategy_keys"] = adopted_indices
                    return output if output else None
                # Proactive novelty gate: a low-novelty (echo/restatement) proactive turn is
                # converted to a hidden pass. Reactive turns are never gated (accountability),
                # and the day's first `opener_floor` real utterances bypass the gate so every
                # day gets a substantive opening before echo-gating engages.
                is_proactive = firing_reason is not None and firing_reason.tier == "proactive"
                today_real = sum(
                    1 for m in payload.get("day_channel", [])
                    if m.day == current_day and m.player != "game_master" and not getattr(m, "passed", False)
                )
                past_opener_floor = today_real >= payload.get("opener_floor", 0)
                if (is_proactive and past_opener_floor
                        and not judge_proactive_novelty(message, payload, current_day)):
                    entry = DayChannel(
                        day=current_day, seq=seq, player=player_id,
                        message="", passed=True, firing_reason=firing_reason,
                    )
                else:
                    entry = DayChannel(
                        day=current_day, seq=seq, player=player_id,
                        message=message,
                        addressed_targets=getattr(result, "addressed_targets", []),
                        firing_reason=firing_reason,
                    )

            output = {"day_channel": [entry]}
            if strategy_update:
                output["agent_strategies"] = {player_id: strategy_update}
            if adopted_indices:
                output["_adopted_strategy_keys"] = adopted_indices
            return output

        if output_key == "day_votes":
            validated = _validate_target(
                result.vote_target,
                valid_targets,
                player_id,
            )
            if validated:
                output = {"day_votes": [DayVote(voter=player_id, votee=validated)]}
                if strategy_update:
                    output["agent_strategies"] = {player_id: strategy_update}
                if adopted_indices:
                    output["_adopted_strategy_keys"] = adopted_indices
                return output
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
                if adopted_indices:
                    output["_adopted_strategy_keys"] = adopted_indices
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
                if adopted_indices:
                    output["_adopted_strategy_keys"] = adopted_indices
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
                if adopted_indices:
                    output["_adopted_strategy_keys"] = adopted_indices
                return output
            logger.warning(f"Investigator targeted invalid player: {result.investigator_target}")
            continue

        if output_key == "serial_killer_target":
            validated = _validate_target(
                result.serial_killer_target,
                valid_targets,
                player_id,
            )
            if validated:
                output = {"serial_killer_target": validated}
                if strategy_update:
                    output["updated_strategy"] = strategy_update
                if adopted_indices:
                    output["_adopted_strategy_keys"] = adopted_indices
                return output
            logger.warning(f"Serial killer targeted invalid player: {result.serial_killer_target}")
            continue

        if output_key == "vigilante_target":
            # "hold_fire" is a valid sentinel target (the vigilante banks the bullet).
            validated = _validate_target(
                result.vigilante_target,
                valid_targets,
                player_id,
            )
            if validated:
                output = {"vigilante_target": validated}
                if strategy_update:
                    output["updated_strategy"] = strategy_update
                if adopted_indices:
                    output["_adopted_strategy_keys"] = adopted_indices
                return output
            logger.warning(f"Vigilante targeted invalid player: {result.vigilante_target}")
            continue

    # All retries exhausted — random fallback
    logger.error(f"{player_id} failed all retries, using random fallback")
    if output_key == "day_votes":
        fallback = random.choice(valid_targets)
        return {"day_votes": [DayVote(voter=player_id, votee=fallback)]}
    if output_key in (
        "healer_target",
        "investigator_target",
        "serial_killer_target",
        "vigilante_target",
    ):
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


def _process_strategy_adoption(
    result: dict[str, Any] | None,
    enriched_payload: dict[str, Any],
    runtime: Runtime[GraphContext],
    *,
    player_id: str,
    role: str,
    action_phase: str,
    day: int,
    round_num: int,
) -> tuple[list[int], list[str], list[StrategyAdoption]]:
    """Record which retrieved strategy points were surfaced and adopted.

    Bumps ``retrieved_count`` on every surfaced point and ``used_count`` on the
    adopted ones, and returns ``(raw_adopted_indices, adopted_store_keys,
    strategy_adoptions)``. Shared by the day and night memory-informed paths.
    Mutates ``result`` by popping the ``_adopted_strategy_keys`` marker.
    """
    index_map = enriched_payload.get("strategy_point_index_map", {})
    raw_adopted_indices: list[int] = []
    adopted_store_keys: list[str] = []
    strategy_adoptions: list[StrategyAdoption] = []

    if not (result and index_map):
        return raw_adopted_indices, adopted_store_keys, strategy_adoptions

    raw_adopted_indices = result.pop("_adopted_strategy_keys", [])
    sp_namespace = ("strategy_points", role, action_phase)
    active_store = runtime.store
    if active_store is None:
        return raw_adopted_indices, adopted_store_keys, strategy_adoptions

    for key in index_map.values():
        item = active_store.get(sp_namespace, key)
        if item is not None:
            value = dict(item.value)
            value["retrieved_count"] = value.get("retrieved_count", 0) + 1
            active_store.put(sp_namespace, key, value, index=False)

    for idx in raw_adopted_indices:
        key = index_map.get(idx)
        if key is None:
            logger.warning(
                f"Hallucinated adoption index {idx} from {player_id} "
                f"(day={day}, round={round_num}, phase={action_phase}, "
                f"valid=[1..{len(index_map)}]), skipping"
            )
            continue
        adopted_store_keys.append(key)
        item = active_store.get(sp_namespace, key)
        if item is not None:
            value = dict(item.value)
            value["used_count"] = value.get("used_count", 0) + 1
            active_store.put(sp_namespace, key, value, index=False)

    strategy_adoptions = [
        StrategyAdoption(
            strategy_key=key,
            player_id=player_id,
            role=role,
            day=day,
            round=round_num,
            action_phase=action_phase,
        )
        for key in adopted_store_keys
    ]
    return raw_adopted_indices, adopted_store_keys, strategy_adoptions


def _build_eval_private_context(
    payload: dict[str, Any],
    day: int,
) -> EvalPrivateContext:
    """Snapshot the private context an agent acted on, for the eval case.

    Reads everything via ``.get`` so it works for both day payloads (which carry
    faction-split survivor lists) and night payloads (flat ``surviving_players``,
    plus ``vigilante_results`` for the vigilante).
    """
    return EvalPrivateContext(
        previous_strategy=payload.get("previous_strategy", "") or "",
        day_summaries=[
            summary
            for summary in payload.get("day_summaries", [])
            if summary.day < day
        ],
        wolf_channel=payload.get("wolf_channel", []),
        investigator_results=payload.get("investigator_results", []),
        vigilante_results=payload.get("vigilante_results", []),
        surviving_players=payload.get("surviving_players", []),
        surviving_wolves=payload.get("surviving_wolves", []),
        surviving_villagers=payload.get("surviving_villagers", []),
    )


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

    span_name = (
        f"agent_action_eval_{player_id}"
        f"_day_{day}_round_{round_num}_{action_phase}"
    )
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
        enriched_payload, retrieval_meta = _enrich_payload_with_memory(
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

    span_name = (
        f"agent_action_eval_{player_id}"
        f"_day_{day}_round_{round_num}_{action_phase}"
    )
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
        enriched_payload, retrieval_meta = _enrich_payload_with_memory(
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
                "action_phase": eval_case.action_phase,
                "player_id": eval_case.player_id,
                "player_role": eval_case.player_role,
                "day": eval_case.day,
                "round": eval_case.round,
                "adopted_count": len(adopted_store_keys),
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
        "day_discussion",
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
        "day_discussion",
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
        "day_discussion",
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
        "day_discussion",
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
        "day_vote",
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
        "day_vote",
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
        "day_vote",
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
        "day_vote",
        INVESTIGATOR_DAY_VOTE,
        DayVoteOutput,
        "day_votes",
    )


def serial_killer_discuss(
    payload: VillagerDayState,
    config: RunnableConfig,
    runtime: Runtime[GraphContext],
):
    return _run_memory_informed_action(
        payload,
        config,
        runtime,
        "day_discussion",
        SERIAL_KILLER_DAY_DISCUSS,
        DayDiscussOutput,
        "day_channel",
    )


def vigilante_discuss(
    payload: VillagerDayState,
    config: RunnableConfig,
    runtime: Runtime[GraphContext],
):
    return _run_memory_informed_action(
        payload,
        config,
        runtime,
        "day_discussion",
        VIGILANTE_DAY_DISCUSS,
        DayDiscussOutput,
        "day_channel",
    )


def serial_killer_vote(
    payload: VillagerDayState,
    config: RunnableConfig,
    runtime: Runtime[GraphContext],
):
    return _run_memory_informed_action(
        payload,
        config,
        runtime,
        "day_vote",
        SERIAL_KILLER_DAY_VOTE,
        DayVoteOutput,
        "day_votes",
    )


def vigilante_vote(
    payload: VillagerDayState,
    config: RunnableConfig,
    runtime: Runtime[GraphContext],
):
    return _run_memory_informed_action(
        payload,
        config,
        runtime,
        "day_vote",
        VIGILANTE_DAY_VOTE,
        DayVoteOutput,
        "day_votes",
    )


def wolf_night_discuss(
    payload: WolfNightState,
    config: RunnableConfig,
    runtime: Runtime[GraphContext],
):
    # Wolf night is the one multi-agent night action (a parallel discussion), but
    # each wolf's turn is still a single memory-informed decision — its kill vote.
    # Route it through the same night path as the single-target roles so it does
    # flag-gated retrieval and emits an EvalCase (action_phase "night_action"),
    # making wolf-night decisions part of the eval/memory sample.
    return _run_memory_informed_night_action(
        payload, config, runtime,
        WOLF_NIGHT_DISCUSS, WolfNightDiscussOutput, "wolf_channel",
    )


def healer_act(
    payload: HealerNightGraph,
    config: RunnableConfig,
    runtime: Runtime[GraphContext],
):
    return _run_memory_informed_night_action(
        payload, config, runtime, HEALER_NIGHT, HealerOutput, "healer_target"
    )


def investigator_act(
    payload: InvestigatorNightGraph,
    config: RunnableConfig,
    runtime: Runtime[GraphContext],
):
    return _run_memory_informed_night_action(
        payload, config, runtime,
        INVESTIGATOR_NIGHT, InvestigatorOutput, "investigator_target",
    )


def serial_killer_act(
    payload: SerialKillerNightGraph,
    config: RunnableConfig,
    runtime: Runtime[GraphContext],
):
    return _run_memory_informed_night_action(
        payload, config, runtime,
        SERIAL_KILLER_NIGHT, SerialKillerOutput, "serial_killer_target",
    )


def vigilante_act(
    payload: VigilanteNightGraph,
    config: RunnableConfig,
    runtime: Runtime[GraphContext],
):
    return _run_memory_informed_night_action(
        payload, config, runtime, VIGILANTE_NIGHT, VigilanteOutput, "vigilante_target"
    )
