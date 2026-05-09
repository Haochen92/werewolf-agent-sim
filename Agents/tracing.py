import uuid
from langfuse import get_client
from langfuse.langchain import CallbackHandler


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