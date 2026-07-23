"""Adaptation layer: convert `RunConfig` settings to a LangGraph `RunnableConfig`, derive child
configs for subgraphs, and read settings back out.

This is the ONLY config module that knows about LangGraph. It deliberately takes callbacks and
metadata as INJECTED parameters rather than importing tracing — that keeps the dependency arrow
config -> (game, run) and never config -> tracing, so settings stay framework/observability-free.
"""
from __future__ import annotations

from typing import Any

from langchain_core.runnables import RunnableConfig
from langchain_core.runnables.config import patch_config

from Agents.config.game import GameConfig, game_config_dict, normalize_game_config
from Agents.config.run import RunConfig

DEFAULT_RECURSION_LIMIT = 100


def build_runnable_config(
    run: RunConfig,
    *,
    callbacks: list | None = None,
    metadata: dict | None = None,
) -> RunnableConfig:
    """Assemble the ROOT RunnableConfig for a game. Settings are dumped into `configurable` as the
    plain dicts graph nodes read (game_config / memory_persistence become dicts, not models);
    callbacks and metadata are injected by the caller (the entry point attaches the Langfuse handler
    + runtime fingerprint), keeping this function free of observability imports."""
    return {
        "callbacks": callbacks or [],
        "recursion_limit": DEFAULT_RECURSION_LIMIT,
        "metadata": metadata or {},
        "configurable": {
            "game_id": run.game_id,
            # One checkpoint thread per game. REQUIRED: the parent graph is compiled with a
            # checkpointer, so every invoke must carry a thread_id or LangGraph raises. Deriving it
            # from game_id (the replay anchor) keeps one game == one resumable thread.
            "thread_id": run.game_id,
            "memory_config": run.memory_config,
            "reranking_config": run.reranking_config,
            "filtering_config": run.filtering_config,
            "retrieval_types_config": run.retrieval_types_config,
            "sp_proven_tiering": run.sp_proven_tiering,
            "sp_exploration_slot": run.sp_exploration_slot,
            "game_config": game_config_dict(run.game),
            "memory_persistence_config": run.memory_persistence.model_dump(mode="json"),
            "session_id": run.session_id,
        },
    }


def child_runnable_config(
    parent: RunnableConfig | None,
    *,
    recursion_limit: int | None = None,
) -> RunnableConfig:
    """Derive a subgraph config from the parent for an imperative `subgraph.invoke(...)`.

    Uses LangChain's `patch_config`, which preserves ALL of the parent's fields — callbacks,
    metadata, tags, and crucially every `configurable` key including the opaque `__pregel_*`
    framework plumbing that carries the checkpointer/thread down to the subgraph. Never mutates the
    parent. The recursion limit is INHERITED from the parent by default (falling back to
    DEFAULT_RECURSION_LIMIT so a self-looping subgraph always has a budget), and overridden only
    when a caller passes one explicitly (the day phase derives a cap-based limit).

    Note: propagation of the checkpointer works via ambient contextvars too, so this helper's
    correctness is pinned by tests/test_child_config_unit.py, NOT by the interrupt integration test.
    """
    if recursion_limit is None:
        recursion_limit = (parent or {}).get("recursion_limit", DEFAULT_RECURSION_LIMIT)
    return patch_config(parent or {}, recursion_limit=recursion_limit)


def game_config_from_runnable(config: dict[str, Any] | None) -> GameConfig:
    """Read the game rules back out of the runtime config, INSIDE a graph node.

    This is a per-node READ accessor, not part of config assembly — the inverse of
    build_runnable_config's one-time write. build_runnable_config dumps the GameConfig into
    `configurable["game_config"]` as a plain dict at the root; every node that needs a rule (voting
    logic, the discussion scheduler) receives only the serialized `config` LangGraph threads down,
    and calls this to recover a typed GameConfig from that dict. It lives beside the builders because
    it is the same RunnableConfig<->domain adaptation concern, but it runs at node execution time,
    not at graph-build time.
    """
    configurable = config.get("configurable", {}) if config else {}
    return normalize_game_config(configurable.get("game_config"))


def discussion_recursion_limit(game: GameConfig, num_survivors: int) -> int:
    """LangGraph recursion_limit for the day SCHEDULE self-loop.

    Each cycle = 2 super-steps (SCHEDULE node + role node). A cycle may be a real utterance OR a
    pass marker: passes consume super-steps but do NOT count toward the cap, and up to
    proactive_budget-1 passes can occur between real utterances before a trailing-pass run
    terminates the day. Worst case is therefore ~proactive_budget cycles per utterance slot, so size
    the limit at 2 * proactive_budget * cap (+headroom) to guarantee the graceful cap /
    trailing-pass termination always fires before an ungraceful GraphRecursionError.
    """
    return 2 * game.proactive_budget * game.utterance_cap(num_survivors) + 10
