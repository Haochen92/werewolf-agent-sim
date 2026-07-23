"""Contract for the root RunnableConfig builder: RunConfig -> build_runnable_config.

Pins the shape the graph runs on: the top-level RunnableConfig keys, the `configurable` bag (keys +
value types), the RunConfig defaults, and the game_id behavior. Graph-side readers index
`config["configurable"][...]` and expect DICTS (not model instances) — that's the contract locked
here. Observability (callbacks) and metadata are INJECTED at the entry point, so this file exercises
both the injected path (mirroring main.run_game) and the bare-builder default (empty).
"""
from __future__ import annotations

from Agents.config import (
    DEFAULT_FILTERING_CONFIG,
    DEFAULT_MEMORY_CONFIG,
    DEFAULT_RERANKING_CONFIG,
    DEFAULT_RETRIEVAL_TYPES_CONFIG,
    RunConfig,
    build_runnable_config,
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


def _config(callbacks=("CB",), metadata=None, **run_kwargs):
    """Mirror the entry-point composition (main.run_game): a RunConfig adapted with injected
    observability + fingerprint metadata."""
    return build_runnable_config(
        RunConfig(**run_kwargs),
        callbacks=list(callbacks),
        metadata=metadata if metadata is not None else {"runtime_fingerprint": "fp"},
    )


def test_top_level_shape():
    cfg = _config()
    assert set(cfg.keys()) == EXPECTED_TOP_KEYS
    assert cfg["recursion_limit"] == 100
    assert len(cfg["callbacks"]) == 1  # the injected Langfuse handler
    assert set(cfg["metadata"].keys()) == {"runtime_fingerprint"}


def test_bare_builder_has_no_injected_observability():
    """Without injection the builder is framework/observability-free: empty callbacks + metadata.
    (The entry point is what attaches the handler + fingerprint.)"""
    cfg = build_runnable_config(RunConfig())
    assert cfg["callbacks"] == []
    assert cfg["metadata"] == {}
    assert cfg["recursion_limit"] == 100


def test_configurable_keys_and_value_types():
    conf = _config()["configurable"]
    assert set(conf.keys()) == EXPECTED_CONFIGURABLE_KEYS
    # Graph readers expect DICTS here, not GameConfig / pydantic instances.
    assert isinstance(conf["game_config"], dict)
    assert isinstance(conf["memory_persistence_config"], dict)


def test_defaults_applied_when_omitted():
    conf = _config()["configurable"]
    assert conf["memory_config"] == DEFAULT_MEMORY_CONFIG
    assert conf["reranking_config"] == DEFAULT_RERANKING_CONFIG
    assert conf["filtering_config"] == DEFAULT_FILTERING_CONFIG
    assert conf["retrieval_types_config"] == DEFAULT_RETRIEVAL_TYPES_CONFIG


def test_none_options_fall_back_to_defaults():
    """run_game passes each unset option as None; RunConfig's before-validator drops None so the
    field default applies (rather than storing a null)."""
    conf = _config(memory_config=None, session_id=None)["configurable"]
    assert conf["memory_config"] == DEFAULT_MEMORY_CONFIG
    assert conf["session_id"] is None


def test_supplied_overrides_win():
    mem = {"custom": True}
    conf = _config(memory_config=mem, session_id="sess-1")["configurable"]
    assert conf["memory_config"] == mem
    assert conf["session_id"] == "sess-1"


def test_sp_flags_explicit_false_preserved():
    """False is a real off-arm choice: a bool field keeps an explicit False rather than dropping it
    to the True default (the before-validator drops only None)."""
    conf = _config(sp_proven_tiering=False, sp_exploration_slot=False)["configurable"]
    assert conf["sp_proven_tiering"] is False
    assert conf["sp_exploration_slot"] is False


def test_game_id_supplied_is_used():
    conf = _config(game_id="game-abc")["configurable"]
    assert conf["game_id"] == "game-abc"


def test_game_id_generated_when_omitted_is_unique_nonempty():
    a = _config()["configurable"]["game_id"]
    b = _config()["configurable"]["game_id"]
    assert a and b and len(a) == 36  # uuid4
    assert a != b  # the replay seed anchor is freshly minted per RunConfig


def test_empty_game_id_backfills_a_fresh_id():
    """An empty `game_id` is treated like an omitted one and backfilled with a fresh uuid — `""` and
    `None` both mean "mint me a seed anchor". A plain default_factory would only fire on an omitted
    field, so RunConfig does this in a before-validator."""
    conf = _config(game_id="")["configurable"]
    assert conf["game_id"] and len(conf["game_id"]) == 36
