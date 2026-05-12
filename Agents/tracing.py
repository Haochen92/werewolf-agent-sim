import uuid
from typing import TypedDict

from langfuse import get_client
from langfuse.langchain import CallbackHandler
from pydantic import BaseModel, Field


langfuse = get_client()

DEFAULT_MEMORY_CONFIG = {
    "wolf": False,
    "villager": False,
    "healer": False,
    "investigator": False,
}


def build_game_config(
    memory_config: dict | None = None,
    session_id: str | None = None,
) -> dict:
    memory_config = memory_config or DEFAULT_MEMORY_CONFIG
    game_id = str(uuid.uuid4())

    handler = CallbackHandler()

    return {
        "callbacks": [handler],
        "recursion_limit": 100,
        "configurable": {
            "game_id": game_id,
            "memory_config": memory_config,
            "session_id": session_id,
        },
    }


def flush():
    langfuse.flush()


def compute_and_push_scores(result: dict, trace_id: str):
    pass


class DayResolutionMetric(BaseModel):
    day: int
    votes: list[dict[str, str]]
    voted_player: str | None
    voted_player_role: str | None
    vote_counts: dict[str, int]
    tied_players: list[str]
    no_vote: bool


class NightResolutionMetric(BaseModel):
    day: int
    wolves_target: str | None
    wolf_target_role: str | None
    healer_target: str | None
    investigator_target: str | None
    investigator_target_role: str | None
    kill_successful: bool
    healer_saved: bool


class Metrics(BaseModel):
    day_resolutions: list[DayResolutionMetric] = Field(default_factory=list)
    night_resolutions: list[NightResolutionMetric] = Field(default_factory=list)


class GraphContext(TypedDict):
    metrics: Metrics
