import os
import uuid
from typing import Any

from langfuse import get_client
from langfuse.langchain import CallbackHandler

from Agents.game_config import game_config_dict
from Agents.memory.persistence import normalize_memory_persistence_config
from Agents.run_fingerprint import git_revision, runtime_fingerprint
from Agents.schemas.metrics import (  # noqa: F401 — re-exported for backward compat
    DayResolutionMetric,
    GraphContext,
    Metrics,
    NightResolutionMetric,
)


# Stamp every trace with the code version via Langfuse's first-class `release`
# field (filterable in the UI). Must be set before the first get_client() —
# the OTel resource is created once per process. setdefault keeps an explicit
# LANGFUSE_RELEASE override working.
os.environ.setdefault("LANGFUSE_RELEASE", git_revision()["git_commit"])

langfuse = get_client()

DEFAULT_MEMORY_CONFIG = {
    "wolf": False,
    "villager": False,
    "healer": False,
    "investigator": False,
}

DEFAULT_RERANKING_CONFIG = {
    "observations": {
        "wolf": False,
        "villager": False,
        "healer": False,
        "investigator": False,
    },
    "strategy_points": {
        "wolf": False,
        "villager": False,
        "healer": False,
        "investigator": False,
    },
}

DEFAULT_FILTERING_CONFIG = {
    "wolf": False,
    "villager": False,
    "healer": False,
    "investigator": False,
}

DEFAULT_RETRIEVAL_TYPES_CONFIG = {
    "observations": True,
    "strategy_points": True,
}

# Proven-first SP tiering (§0.4): default ON — inert on stores without credit counters, so ON is safe;
# an explicit False is the A/B off-arm. Declared here (not only read with a fallback in plan_gating) so
# the RECORDED game config always carries the resolved value — tiering-on vs tiering-off runs must be
# distinguishable from the run record alone (epoch-bundle member: it changes live-game behavior).
DEFAULT_SP_PROVEN_TIERING = True

# Exploration slot at the SP cap (§0.4): default ON, same rationale as tiering — inert unless a kept set
# is all-proven with an unproven candidate, so ON is safe; an explicit False is the A/B off-arm. Declared
# here so the RECORDED game config always carries the resolved value (slot-on vs slot-off distinguishable
# from the run record alone; it changes live-game behavior — an epoch-bundle member).
DEFAULT_SP_EXPLORATION_SLOT = True


def build_game_config(
    memory_config: dict | None = None,
    session_id: str | None = None,
    game_config: Any = None,
    memory_persistence_config: Any = None,
    reranking_config: dict | None = None,
    filtering_config: dict | None = None,
    retrieval_types_config: dict | None = None,
    game_id: str | None = None,
    sp_proven_tiering: bool | None = None,
    sp_exploration_slot: bool | None = None,
) -> dict:
    memory_config = memory_config or DEFAULT_MEMORY_CONFIG
    reranking_config = reranking_config or DEFAULT_RERANKING_CONFIG
    filtering_config = filtering_config or DEFAULT_FILTERING_CONFIG
    retrieval_types_config = retrieval_types_config or DEFAULT_RETRIEVAL_TYPES_CONFIG
    # Explicit None-check (not `or`): False is a valid, recordable off-arm choice.
    if sp_proven_tiering is None:
        sp_proven_tiering = DEFAULT_SP_PROVEN_TIERING
    if sp_exploration_slot is None:
        sp_exploration_slot = DEFAULT_SP_EXPLORATION_SLOT
    normalized_game_config = game_config_dict(game_config)
    normalized_memory_persistence_config = normalize_memory_persistence_config(
        memory_persistence_config
    ).model_dump(mode="json")
    # Pin game_id for reproducible replay (scheduler seed derives from it); random otherwise.
    game_id = game_id or str(uuid.uuid4())

    handler = CallbackHandler()

    return {
        "callbacks": [handler],
        "recursion_limit": 100,
        # Lands in trace metadata: the exact (code, prompts, models, params,
        # backend) bundle this game ran with. See Agents/run_fingerprint.py.
        "metadata": {"runtime_fingerprint": runtime_fingerprint()},
        "configurable": {
            "game_id": game_id,
            "memory_config": memory_config,
            "reranking_config": reranking_config,
            "filtering_config": filtering_config,
            "retrieval_types_config": retrieval_types_config,
            "sp_proven_tiering": sp_proven_tiering,
            "sp_exploration_slot": sp_exploration_slot,
            "game_config": normalized_game_config,
            "memory_persistence_config": normalized_memory_persistence_config,
            "session_id": session_id,
        },
    }


def flush():
    langfuse.flush()
