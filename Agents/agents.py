import os
from functools import lru_cache
from logging import getLogger
from typing import Any
import random

from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel

from Agents.formatters import (
    format_day_channel_for_day,
    format_day_summaries,
    format_investigator_results,
    format_retrieved_observations,
    format_strategy_points,
    format_wolf_channel,
)
from Agents.memory import (
    retrieve_observations_for_agent,
    retrieve_strategy_points_for_agent,
    store,
)
from Agents.prompts import (
    HEALER_DAY_DISCUSS,
    HEALER_DAY_VOTE,
    HEALER_NIGHT,
    INVESTIGATOR_DAY_DISCUSS,
    INVESTIGATOR_DAY_VOTE,
    INVESTIGATOR_NIGHT,
    VILLAGER_DAY_DISCUSS,
    VILLAGER_DAY_VOTE,
    WOLF_DAY_DISCUSS,
    WOLF_DAY_VOTE,
    WOLF_NIGHT_DISCUSS,
)
from Agents.schemas import (
    DayDiscussOutput,
    DayVoteOutput,
    HealerOutput,
    InvestigatorOutput,
    WolfNightDiscussOutput,
)
from Agents.state import (
    DayChannel,
    DayVote,
    HealerDayState,
    HealerNightGraph,
    InvestigatorDayState,
    InvestigatorNightGraph,
    VillagerDayState,
    WolfChannel,
    WolfDayState,
    WolfNightState,
)

load_dotenv()
logger = getLogger(__name__)
prompt_log: list[dict] = []


@lru_cache(maxsize=1)
def get_llm():
    google_api_key = os.getenv("GOOGLE_API_KEY")
    kwargs: dict[str, Any] = {
        "model": os.getenv("GOOGLE_GENAI_MODEL", "gemini-2.5-flash"),
        "temperature": float(os.getenv("GOOGLE_GENAI_TEMPERATURE", "1.0")),
    }
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

def _validate_target(target: str, valid_targets: list[str], player_id: str) -> str | None:
    """Returns the target if valid, None if not."""
    if target in valid_targets and target != player_id:
        return target
    return None


def _run_agent(
    payload: dict[str, Any],
    prompt_template: ChatPromptTemplate,
    output_schema: type[BaseModel],
    output_key: str,
    max_retries: int = 1
) -> dict[str, Any] | None:
    chain = prompt_template | get_llm().with_structured_output(output_schema)

    prompt_input = {
        "player_id": payload.get("player_id", ""),
        "player_role": payload.get("player_role", ""),
        "current_day": payload.get("current_day", 1),
        "current_round": payload.get("current_round", 1),
        "surviving_players": ", ".join(payload.get("surviving_players", [])),
        "surviving_wolves": ", ".join(payload.get("surviving_wolves", [])),
        "surviving_villagers": ", ".join(payload.get("surviving_villagers", [])),
        "day_channel": format_day_channel_for_day(
            payload.get("day_channel", []),
            payload.get("current_day", 1),
        ),
        "day_summaries": format_day_summaries(
            payload.get("day_summaries", []),
            before_day=payload.get("current_day", 1),
        ),
        "wolf_channel": format_wolf_channel(payload.get("wolf_channel", [])),
        "investigator_results": format_investigator_results(
            payload.get("investigator_results", [])
        ),
        "previous_strategy": payload.get("previous_strategy", ""),
        "strategy_points": payload.get(
            "strategy_points", "No dynamic strategy points available."
        ),
        "retrieved_observations": payload.get(
            "retrieved_observations", "No past observations available."
        ),
    }
    
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
            result = chain.invoke(prompt_input)
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
                payload.get("surviving_players", []),
                player_id,
            )
            if validated:
                return {"day_votes": [DayVote(voter=player_id, votee=validated)]}
            logger.warning(f"{player_id} voted for invalid target: {result.vote_target}")
            continue
        
        if output_key == "wolf_channel":
            validated = _validate_target(
                result.vote_target,
                payload.get("surviving_villagers", []),
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
                payload.get("surviving_players", []),
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
                payload.get("surviving_players", []),
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
        fallback = random.choice([t for t in payload.get("surviving_players", []) if t != player_id])
        return {"day_votes": [DayVote(voter=player_id, votee=fallback)]}
    if output_key in ("healer_target", "investigator_target"):
        fallback = random.choice([t for t in payload.get("surviving_players", []) if t != player_id])
        return {output_key: fallback}
    if output_key == "wolf_channel":
        fallback = random.choice([t for t in payload.get("surviving_villagers", []) if t != player_id])
        return {"wolf_channel": [WolfChannel(
            day=payload.get("current_day", 1),
            round=payload.get("current_round", 1),
            wolf=player_id,
            message="...",
            vote=fallback,
        )]}

    return None


def _with_retrieved_observations(
    payload: VillagerDayState | HealerDayState | WolfDayState | InvestigatorDayState,
) -> dict[str, Any]:
    enriched_payload = dict(payload)

    if payload["current_day"] == 1:
        enriched_payload["retrieved_observations"] = "No past observations available."
        enriched_payload["strategy_points"] = payload.get(
            "strategy_points",
            "No dynamic strategy points available.",
        )
        return enriched_payload

    retrieval_result = retrieve_observations_for_agent(
        store=store,
        role=payload["player_role"],
        day_channel=payload["day_channel"],
        current_day=payload["current_day"],
        current_round=payload["current_round"],
        previous_strategy=payload.get("previous_strategy", ""),
    )
    enriched_payload["retrieved_observations"] = format_retrieved_observations(
        retrieval_result["retrieved_observations"]
    )
    enriched_payload["strategy_points"] = format_strategy_points(
        retrieve_strategy_points_for_agent(
            store=store,
            role=payload["player_role"],
            situations=retrieval_result["situations"],
        )
    )
    return enriched_payload


def villager_discuss(payload: VillagerDayState):
    payload = _with_retrieved_observations(payload)
    return _run_agent(payload, VILLAGER_DAY_DISCUSS, DayDiscussOutput, "day_channel")


def healer_discuss(payload: HealerDayState):
    payload = _with_retrieved_observations(payload)
    return _run_agent(payload, HEALER_DAY_DISCUSS, DayDiscussOutput, "day_channel")


def wolf_discuss(payload: WolfDayState):
    payload = _with_retrieved_observations(payload)
    return _run_agent(payload, WOLF_DAY_DISCUSS, DayDiscussOutput, "day_channel")


def investigator_discuss(payload: InvestigatorDayState):
    payload = _with_retrieved_observations(payload)
    return _run_agent(
        payload, INVESTIGATOR_DAY_DISCUSS, DayDiscussOutput, "day_channel"
    )


def villager_vote(payload: VillagerDayState):
    payload = _with_retrieved_observations(payload)
    return _run_agent(payload, VILLAGER_DAY_VOTE, DayVoteOutput, "day_votes")


def healer_vote(payload: HealerDayState):
    payload = _with_retrieved_observations(payload)
    return _run_agent(payload, HEALER_DAY_VOTE, DayVoteOutput, "day_votes")


def wolf_vote(payload: WolfDayState):
    payload = _with_retrieved_observations(payload)
    return _run_agent(payload, WOLF_DAY_VOTE, DayVoteOutput, "day_votes")


def investigator_vote(payload: InvestigatorDayState):
    payload = _with_retrieved_observations(payload)
    return _run_agent(payload, INVESTIGATOR_DAY_VOTE, DayVoteOutput, "day_votes")


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
