from __future__ import annotations

from contextlib import contextmanager
from types import SimpleNamespace

import pytest

from Agents.config import RunConfig
from Agents import main


class _RootSpan:
    trace_id = "trace-test"

    def update(self, **kwargs):
        return None

    def update_trace(self, **kwargs):
        return None


def _stub_run_dependencies(monkeypatch):
    captured = {}

    def seed(config, *, target_store):
        captured["seed_config"] = config
        captured["seed_store"] = target_store

    def invoke(initial_state, *, config, context, version):
        captured["initial_state"] = initial_state
        captured["runnable_config"] = config
        captured["context"] = context
        captured["invoke_version"] = version
        # run_game invokes with version="v2": GraphOutput(value, interrupts), no
        # __interrupt__ key in the state dict.
        return SimpleNamespace(
            value={"winner": "town", "current_day": 1}, interrupts=()
        )

    @contextmanager
    def observation(**kwargs):
        captured["observation"] = kwargs
        yield _RootSpan()

    monkeypatch.setattr(main, "seed_memory_from_config", seed)
    monkeypatch.setattr(main, "create_langfuse_handler", lambda: "handler")
    monkeypatch.setattr(main, "runtime_fingerprint", lambda: {"fingerprint": "test"})
    monkeypatch.setattr(
        main,
        "parent_graph_compiled",
        SimpleNamespace(invoke=invoke),
    )
    monkeypatch.setattr(
        main,
        "langfuse",
        SimpleNamespace(start_as_current_observation=observation),
    )
    monkeypatch.setattr(main, "compute_game_metrics", lambda result, metrics: "computed")
    monkeypatch.setattr(main, "push_scores_to_langfuse", lambda *args: None)
    monkeypatch.setattr(main, "flush", lambda: None)
    return captured


def test_run_game_accepts_one_canonical_run_config(monkeypatch):
    captured = _stub_run_dependencies(monkeypatch)
    run = RunConfig(
        game_id="game-canonical",
        session_id="session-canonical",
        memory_persistence={"seed_enabled": False, "dump_enabled": False},
        sp_proven_tiering=False,
        sp_exploration_slot=False,
    )

    outcome = main.run_game(run)

    configurable = captured["runnable_config"]["configurable"]
    assert outcome.game_id == "game-canonical"
    assert captured["seed_config"] is run.memory_persistence
    assert configurable["thread_id"] == "game-canonical"
    assert configurable["sp_proven_tiering"] is False
    assert configurable["sp_exploration_slot"] is False


def test_run_game_accepts_canonical_dict(monkeypatch):
    captured = _stub_run_dependencies(monkeypatch)

    outcome = main.run_game(
        {
            "game_id": "game-dict",
            "memory_persistence": {"seed_enabled": False, "dump_enabled": False},
        }
    )

    assert outcome.game_id == "game-dict"
    assert captured["runnable_config"]["configurable"]["thread_id"] == "game-dict"


def test_legacy_keywords_still_work_with_deprecation_warning(monkeypatch):
    captured = _stub_run_dependencies(monkeypatch)

    with pytest.warns(DeprecationWarning, match="pass RunConfig"):
        outcome = main.run_game(
            game_id="game-legacy",
            game_config={"max_days": 4},
            memory_persistence_config={
                "seed_enabled": False,
                "dump_enabled": False,
            },
        )

    configurable = captured["runnable_config"]["configurable"]
    assert outcome.game_id == "game-legacy"
    assert configurable["game_config"]["max_days"] == 4


def test_legacy_positional_memory_config_still_works(monkeypatch):
    captured = _stub_run_dependencies(monkeypatch)

    with pytest.warns(DeprecationWarning, match="pass RunConfig"):
        main.run_game(
            {"wolf": True, "villager": False},
            session_id="legacy-positional",
        )

    configurable = captured["runnable_config"]["configurable"]
    assert configurable["memory_config"] == {"wolf": True, "villager": False}
    assert configurable["session_id"] == "legacy-positional"


def test_run_game_rejects_mixed_or_unknown_inputs():
    with pytest.raises(TypeError, match="cannot be combined"):
        main.run_game(RunConfig(), game_id="legacy")

    with pytest.raises(TypeError, match="unexpected keyword"):
        main.run_game(typo_config=True)
