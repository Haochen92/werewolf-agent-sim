from logging import getLogger
from typing import Any
import random

from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel

from Agents.llm_factory import get_llm


from Agents.prompts.prompt_inputs import build_agent_prompt_input as _build_agent_prompt_input
from Agents.schemas.game_events import (
    DayChannel,
    DayVote,
    WolfChannel,
)
from Agents.turn.novelty_agent import judge_proactive_novelty
from Agents.turn.action_space import (
    _valid_targets_for_action,
    _validate_target,
    _with_dynamic_target_enum,
)

load_dotenv()
logger = getLogger(__name__)
prompt_log: list[dict] = []


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

        # Extract strategy, adoption, and per-memory verdicts if present on the result. The
        # _memory_applicability carrier rides the curated output the same way _adopted_strategy_keys
        # does — _run_agent drops everything off `result` that isn't explicitly carried, and actions.py
        # reads these carriers into the EvalCase.
        strategy_update = getattr(result, "updated_strategy", None)
        adopted_indices = getattr(result, "adopted_strategy_keys", []) or []
        memory_verdicts = getattr(result, "memory_applicability", []) or []

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
                    if memory_verdicts:
                        output["_memory_applicability"] = memory_verdicts
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
            if memory_verdicts:
                output["_memory_applicability"] = memory_verdicts
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
                if memory_verdicts:
                    output["_memory_applicability"] = memory_verdicts
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
                if memory_verdicts:
                    output["_memory_applicability"] = memory_verdicts
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
                if memory_verdicts:
                    output["_memory_applicability"] = memory_verdicts
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
                if memory_verdicts:
                    output["_memory_applicability"] = memory_verdicts
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
                if memory_verdicts:
                    output["_memory_applicability"] = memory_verdicts
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
                if memory_verdicts:
                    output["_memory_applicability"] = memory_verdicts
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


