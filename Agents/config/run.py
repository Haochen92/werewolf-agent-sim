"""Experiment layer: the complete application settings for ONE simulation run.

`RunConfig` is the single canonical description of what a run does — the game rules plus the memory
pipeline arm selection (memory/rerank/filter/retrieval-type flags, SP tiering), the persistence
seed, and the run identity. It is application settings ONLY: no LangGraph objects, no callback
handlers, no tracing. Conversion to a LangGraph `RunnableConfig` (and attaching observability) is
`Agents.config.langgraph`'s job — this keeps settings serializable and framework-free.

The pipeline-arm default dicts live here (their only consumer is `RunConfig`); they are re-exported
from `Agents.tracing` for backward compat with existing call sites and tests.
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
    def _backfill_game_id(cls, data: Any) -> Any:
        """A missing OR empty game_id is minted a fresh uuid — `""` and `None` both mean "give me a
        seed anchor". (A plain default_factory only fires on an omitted field, not an explicit "".)"""
        if isinstance(data, dict) and not data.get("game_id"):
            data = {**data, "game_id": str(uuid4())}
        return data

    @classmethod
    def from_options(
        cls,
        *,
        game_config: Any = None,
        memory_config: dict | None = None,
        reranking_config: dict | None = None,
        filtering_config: dict | None = None,
        retrieval_types_config: dict | None = None,
        memory_persistence_config: Any = None,
        sp_proven_tiering: bool | None = None,
        sp_exploration_slot: bool | None = None,
        game_id: str | None = None,
        session_id: str | None = None,
    ) -> "RunConfig":
        """Build a RunConfig from loose optional options (the legacy build_game_config surface):
        a None value means "use the default", so it is dropped and the field default applies.
        An explicit False on the SP flags is a real off-arm choice and is preserved."""
        provided = {
            "game": game_config,
            "memory_config": memory_config,
            "reranking_config": reranking_config,
            "filtering_config": filtering_config,
            "retrieval_types_config": retrieval_types_config,
            "memory_persistence": memory_persistence_config,
            "sp_proven_tiering": sp_proven_tiering,
            "sp_exploration_slot": sp_exploration_slot,
            "game_id": game_id,
            "session_id": session_id,
        }
        return cls(**{k: v for k, v in provided.items() if v is not None})
