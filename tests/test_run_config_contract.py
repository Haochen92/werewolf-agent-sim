"""Behavior-preservation contract for build_game_config (today's root RunnableConfig builder).

Pins the EXACT shape of the config `build_game_config` emits BEFORE the config/ refactor, so the
move to `build_runnable_config(RunConfig)` can be proven a no-op: same top-level keys, same
`configurable` bag (keys + value types), same defaults, same id behavior. Graph-side readers index
`config["configurable"][...]` and expect dicts (not model instances) — that's the contract these
tests lock. When the refactor lands, this file should stay GREEN unchanged (except the import path).
"""
from __future__ import annotations

from Agents.tracing import (
    DEFAULT_FILTERING_CONFIG,
    DEFAULT_MEMORY_CONFIG,
    DEFAULT_RERANKING_CONFIG,
    DEFAULT_RETRIEVAL_TYPES_CONFIG,
    build_game_config,
)

EXPECTED_TOP_KEYS = {"callbacks", "configurable", "metadata", "recursion_limit"}
EXPECTED_CONFIGURABLE_KEYS = {
    "filtering_config",
    "game_config",
    "game_id",
    "memory_config",
    "memory_persistence_config",
    "reranking_config",
    "retrieval_types_config",
    "session_id",
    "sp_exploration_slot",
    "sp_proven_tiering",
}


def test_top_level_shape():
    cfg = build_game_config()
    assert set(cfg.keys()) == EXPECTED_TOP_KEYS
    assert cfg["recursion_limit"] == 100
    assert len(cfg["callbacks"]) == 1  # the Langfuse handler
    assert set(cfg["metadata"].keys()) == {"runtime_fingerprint"}


def test_configurable_keys_and_value_types():
    conf = build_game_config()["configurable"]
    assert set(conf.keys()) == EXPECTED_CONFIGURABLE_KEYS
    # Graph readers expect DICTS here, not GameConfig / pydantic instances.
    assert isinstance(conf["game_config"], dict)
    assert isinstance(conf["memory_persistence_config"], dict)


def test_defaults_applied_when_omitted():
    conf = build_game_config()["configurable"]
    assert conf["memory_config"] == DEFAULT_MEMORY_CONFIG
    assert conf["reranking_config"] == DEFAULT_RERANKING_CONFIG
    assert conf["filtering_config"] == DEFAULT_FILTERING_CONFIG
    assert conf["retrieval_types_config"] == DEFAULT_RETRIEVAL_TYPES_CONFIG


def test_supplied_overrides_win():
    mem = {"custom": True}
    conf = build_game_config(memory_config=mem, session_id="sess-1")["configurable"]
    assert conf["memory_config"] == mem
    assert conf["session_id"] == "sess-1"


def test_sp_flags_explicit_false_preserved():
    """False is a real off-arm choice: the builder uses an explicit None-check, not `or`, so an
    explicit False must survive rather than fall back to the default True."""
    conf = build_game_config(
        sp_proven_tiering=False, sp_exploration_slot=False
    )["configurable"]
    assert conf["sp_proven_tiering"] is False
    assert conf["sp_exploration_slot"] is False


def test_game_id_supplied_is_used():
    conf = build_game_config(game_id="game-abc")["configurable"]
    assert conf["game_id"] == "game-abc"


def test_game_id_generated_when_omitted_is_unique_nonempty():
    a = build_game_config()["configurable"]["game_id"]
    b = build_game_config()["configurable"]["game_id"]
    assert a and b and len(a) == 36  # uuid4
    assert a != b  # the replay seed anchor is freshly minted per call


def test_empty_game_id_backfills_a_fresh_id():
    """Lenient contract (kept through the refactor): an empty `game_id` is treated like an omitted
    one and backfilled with a fresh uuid — `""` and `None` both mean "mint me a seed anchor". The
    config/ refactor preserves this via a RunConfig before-validator (a plain default_factory would
    only fire on an omitted field, not on an explicit "")."""
    conf = build_game_config(game_id="")["configurable"]
    assert conf["game_id"] and len(conf["game_id"]) == 36
