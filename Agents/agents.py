import os
from functools import lru_cache
from typing import Any

from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel

from Agents.formatters import (
    format_day_channel,
    format_investigator_results,
    format_wolf_channel,
)
from Agents.prompts import (
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
    HealerNightGraph,
    InvestigatorDayState,
    InvestigatorNightGraph,
    VillagerDayState,
    WolfChannel,
    WolfDayState,
    WolfNightState,
)

load_dotenv()


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


def _run_agent(
    payload: dict[str, Any],
    prompt_template: ChatPromptTemplate,
    output_schema: type[BaseModel],
    output_key: str,
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
        "day_channel": format_day_channel(payload.get("day_channel", [])),
        "wolf_channel": format_wolf_channel(payload.get("wolf_channel", [])),
        "investigator_results": format_investigator_results(
            payload.get("investigator_results", [])
        ),
    }

    result = chain.invoke(prompt_input)

    if output_key == "day_channel":
        return {
            "day_channel": [
                DayChannel(
                    day=payload.get("current_day", 1),
                    round=payload.get("current_round", 1),
                    player=payload["player_id"],
                    message=result.message,
                )
            ]
        }
    if output_key == "day_votes":
        return {
            "day_votes": [
                DayVote(
                    voter=payload["player_id"],
                    votee=result.vote_target,
                )
            ]
        }
    if output_key == "wolf_channel":
        return {
            "wolf_channel": [
                WolfChannel(
                    day=payload.get("current_day", 1),
                    round=payload.get("current_round", 1),
                    wolf=payload["player_id"],
                    message=result.message,
                    vote=result.vote_target,
                )
            ]
        }
    if output_key == "healer_target":
        return {"healer_target": result.healer_target}
    if output_key == "investigator_target":
        return {"investigator_target": result.investigator_target}
    return None


def villager_discuss(payload: VillagerDayState):
    return _run_agent(payload, VILLAGER_DAY_DISCUSS, DayDiscussOutput, "day_channel")


def wolf_discuss(payload: WolfDayState):
    return _run_agent(payload, WOLF_DAY_DISCUSS, DayDiscussOutput, "day_channel")


def investigator_discuss(payload: InvestigatorDayState):
    return _run_agent(
        payload, INVESTIGATOR_DAY_DISCUSS, DayDiscussOutput, "day_channel"
    )


def villager_vote(payload: VillagerDayState):
    return _run_agent(payload, VILLAGER_DAY_VOTE, DayVoteOutput, "day_votes")


def wolf_vote(payload: WolfDayState):
    return _run_agent(payload, WOLF_DAY_VOTE, DayVoteOutput, "day_votes")


def investigator_vote(payload: InvestigatorDayState):
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
