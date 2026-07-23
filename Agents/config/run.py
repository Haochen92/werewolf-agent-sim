"""Experiment layer: the complete application settings for ONE simulation run.

`RunConfig` is the single canonical description of what a run does — the game rules plus the memory
pipeline arm selection (memory/rerank/filter/retrieval-type flags, SP tiering), the persistence
seed, and the run identity. It is application settings ONLY: no LangGraph objects, no callback
handlers, no tracing. Conversion to a LangGraph `RunnableConfig` (and attaching observability) is
`Agents.config.langgraph`'s job — this keeps settings serializable and framework-free.

The pipeline-arm default dicts live here (their only consumer is `RunConfig`) and are re-exported
from `Agents.config`. Loose optional-arg callers (run_game) construct `RunConfig(**opts)` directly:
a before-validator drops None options so field defaults apply — there is no separate builder.
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

    @model_validator(mode="before")
    @classmethod
    def _coalesce_options(cls, data: Any) -> Any:
        """Support loose optional-arg entry points (run_game passes each unset option as None): a
        None means "use the default", so drop it and let the field default apply. Then backfill an
        empty OR absent game_id with a fresh uuid — `""` and `None` both mean "mint me a seed
        anchor" (a plain default_factory only fires on an omitted field, not an explicit ""). An
        explicit False (the SP off-arm) is not None, so it is preserved, not dropped."""
        if isinstance(data, dict):
            data = {k: v for k, v in data.items() if v is not None}
            if not data.get("game_id"):
                data["game_id"] = str(uuid4())
        return data
