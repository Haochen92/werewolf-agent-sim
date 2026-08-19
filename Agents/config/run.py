"""Experiment layer: the complete application settings for ONE simulation run.

`RunConfig` is the single canonical description of what a run does — the game rules plus the memory
pipeline arm selection (memory/rerank/filter/retrieval-type flags, SP tiering), the persistence
seed, and the run identity. It is application settings ONLY: no LangGraph objects, no callback
handlers, no tracing. Conversion to a LangGraph `RunnableConfig` (and attaching observability) is
`Agents.config.langgraph`'s job — this keeps settings serializable and framework-free.

The pipeline-arm default dicts live here (their only consumer is `RunConfig`) and are re-exported
from `Agents.config`. ``normalize_run_config`` is the coercion boundary used by the application
entry point; a before-validator drops explicit ``None`` options so field defaults apply.
"""
from __future__ import annotations

from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field, model_validator

from Agents.config.game import GameConfig
from Agents.memory.persistence.config import (
    MemoryPersistenceConfig,
    normalize_memory_persistence_config,
)

# --- Pipeline arm defaults (memory OFF baseline) --------------------------------------
DEFAULT_MEMORY_CONFIG = {
    "wolf": False,
    "villager": False,
    "healer": False,
    "investigator": False,
}

DEFAULT_RERANKING_CONFIG = {
    "observations": {"wolf": False, "villager": False, "healer": False, "investigator": False},
    "strategy_points": {"wolf": False, "villager": False, "healer": False, "investigator": False},
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

# Proven-first SP tiering (§0.4): default ON — inert on stores without credit counters, so ON is
# safe; an explicit False is the A/B off-arm. The RECORDED run config always carries the resolved
# value so tiering-on vs tiering-off runs are distinguishable from the record alone (epoch-bundle
# member: it changes live-game behavior).
DEFAULT_SP_PROVEN_TIERING = True
# Exploration slot at the SP cap (§0.4): default ON, same rationale — inert unless a kept set is
# all-proven with an unproven candidate. Explicit False is the A/B off-arm; recorded for the same
# distinguishability reason.
DEFAULT_SP_EXPLORATION_SLOT = True


class RunConfig(BaseModel):
    """Everything about one run except framework wiring. Nested domain models (GameConfig,
    MemoryPersistenceConfig) coerce from dicts, so `RunConfig(game={...})` and
    `RunConfig(game=GameConfig(...))` both validate."""

    game: GameConfig = Field(default_factory=GameConfig)
    memory_config: dict[str, Any] = Field(default_factory=lambda: dict(DEFAULT_MEMORY_CONFIG))
    reranking_config: dict[str, Any] = Field(
        default_factory=lambda: dict(DEFAULT_RERANKING_CONFIG)
    )
    filtering_config: dict[str, Any] = Field(
        default_factory=lambda: dict(DEFAULT_FILTERING_CONFIG)
    )
    retrieval_types_config: dict[str, Any] = Field(
        default_factory=lambda: dict(DEFAULT_RETRIEVAL_TYPES_CONFIG)
    )
    memory_persistence: MemoryPersistenceConfig = Field(
        default_factory=lambda: normalize_memory_persistence_config(None)
    )
    sp_proven_tiering: bool = DEFAULT_SP_PROVEN_TIERING
    sp_exploration_slot: bool = DEFAULT_SP_EXPLORATION_SLOT
    game_id: str = ""
    session_id: str | None = None
    human_player: int = 0
    """How many human seats initialize_game deals (random distinct seats; each human turn pauses
    the graph via interrupt()). Legacy bool call sites still work — True coerces to 1. Default 0 =
    a fully automated all-LLM game (every eval/batch run) — no seat is flagged human, so
    interrupt() never fires."""
    human_role: str | None = None
    """Optional role preference for the human seat (e.g. "wolf"). None = play whatever role the
    random seat drew. Honored only when human_player is exactly 1 (solo) — in a shared room role
    choice leaks/races, so multi-human games always deal random roles; must be in the cast."""

    @model_validator(mode="before")
    @classmethod
    def _coalesce_options(cls, data: Any) -> Any:
        """Treat ``None`` as "use the default", then ensure every run has a game ID.

        An empty, absent, or null game_id means "mint a seed anchor". Explicit ``False`` values (for
        example an SP off-arm) are preserved.
        """
        if isinstance(data, dict):
            data = {k: v for k, v in data.items() if v is not None}
            if not data.get("game_id"):
                data["game_id"] = str(uuid4())
        return data


def normalize_run_config(
    config: RunConfig | dict[str, Any] | None,
) -> RunConfig:
    """Return one validated application-level configuration for a game run."""
    if config is None:
        return RunConfig()
    if isinstance(config, RunConfig):
        return config
    return RunConfig.model_validate(config)
