"""Tests for the batch_results experiment layout (evaluation.src.data.batch_layout).

Covers the file-writing behaviour that matters for multi-invocation loop campaigns:
config.json is write-if-absent (first writer wins) and summary.json merges by
session_prefix instead of clobbering.
"""

from __future__ import annotations

import json

import pytest

from evaluation.src.data import batch_layout


@pytest.fixture
def batch_root(tmp_path, monkeypatch):
    root = tmp_path / "batch_results"
    monkeypatch.setattr(batch_layout, "BATCH_ROOT", root)
    return root


def test_path_builders_nest_under_experiment(batch_root):
    assert batch_layout.experiment_dir("exp1") == batch_root / "exp1"
    assert (
        batch_layout.game_records_path("exp1", "gen1_on")
        == batch_root / "exp1" / "games" / "gen1_on.jsonl"
    )
    assert (
        batch_layout.eval_cases_path("exp1", "gen1_on_all_enabled", "g0")
        == batch_root / "exp1" / "eval_cases" / "gen1_on_all_enabled" / "g0.jsonl"
    )
    assert batch_layout.config_path("exp1") == batch_root / "exp1" / "config.json"
    assert batch_layout.summary_path("exp1") == batch_root / "exp1" / "summary.json"


def test_write_run_config_is_write_if_absent(batch_root):
    p1 = batch_layout.write_run_config(
        "exp1", {"resolved_config": {"configs": ["town_only"]}}
    )
    assert p1.exists()
    assert json.loads(p1.read_text())["resolved_config"]["configs"] == ["town_only"]

    # Second call must NOT overwrite — the first writer wins (so a loop's per-(gen,arm)
    # run_batch calls don't trample the campaign config stamped first).
    p2 = batch_layout.write_run_config(
        "exp1", {"resolved_config": {"configs": ["all_enabled"]}}
    )
    assert p2 == p1
    assert json.loads(p1.read_text())["resolved_config"]["configs"] == ["town_only"]


def test_config_overview_summarizes_arms_store_and_scale(batch_root):
    resolved = {
        "configs": ["all_disabled", "town_only"],
        "memory_configs": {
            "all_disabled": {r: False for r in
                             ("wolf", "villager", "healer", "investigator", "serial_killer", "vigilante")},
            "town_only": {"wolf": False, "villager": True, "healer": True,
                          "investigator": True, "serial_killer": False, "vigilante": True},
        },
        "runs_per_config": 5,
        "game_ids_pinned": ["g0", "g1", "g2"],
        "memory_persistence_config": {"seed_store_dir": "memory_stores/v6_1"},
    }
    fp = {"game_model": "gemini-2.5-pro", "llm_backend": "vertex", "git_commit": "abc123"}
    ov = batch_layout.config_overview(resolved, fp)
    assert ov["store"] == "memory_stores/v6_1"
    assert ov["arms"]["all_disabled"] == []
    # arms summarised as enabled factions (sorted) — an arms-race slip would show here
    assert ov["arms"]["town_only"] == ["healer", "investigator", "vigilante", "villager"]
    assert ov["n_games_per_arm"] == 3  # pinned set overrides runs_per_config
    assert ov["paired"] is True
    assert (ov["model"], ov["backend"], ov["git"]) == ("gemini-2.5-pro", "vertex", "abc123")


def test_config_overview_accepts_pydantic_like_fingerprint(batch_root):
    class FP:
        def model_dump(self):
            return {"game_model": "m", "llm_backend": "b", "git_commit": "g"}

    ov = batch_layout.config_overview({"memory_configs": {}}, FP())
    assert (ov["model"], ov["backend"], ov["git"]) == ("m", "b", "g")
    assert ov["paired"] is False  # no pinned ids


def test_build_loop_descriptor_mirrors_config_with_overview(batch_root):
    loop_config = {
        "arm": "ob_sp_loop", "model": "gemini-3.1-flash-lite",
        "expect_factions": "town_only", "generations": 10,
        "games_per_generation": 5, "off_baseline": True, "discussion_mode": "tagger",
    }
    d = batch_layout.build_loop_descriptor(
        "town_only_run3", loop_config, base_store="memory_stores/v6_1", configs="town_only",
        created_at="2026-06-29T00:00:00+00:00", argv=["--run-dir", "batch_results/town_only_run3"],
        run_dir="batch_results/town_only_run3",
    )
    assert d["kind"] == "loop"
    assert d["overview"]["store"] == "memory_stores/v6_1"
    assert d["overview"]["expect_factions"] == "town_only"   # DECLARED intent
    assert d["overview"]["arm_config"] == "town_only"
    assert d["overview"]["model"] == "gemini-3.1-flash-lite"
    assert d["loop_config"] is loop_config                    # full config carried verbatim
    assert d["source"]["run_dir"] == "batch_results/town_only_run3"


def test_merge_run_summary_accumulates_by_session_prefix(batch_root):
    batch_layout.merge_run_summary("exp1", "gen1_on", {"status": "complete", "successes": 4})
    batch_layout.merge_run_summary("exp1", "gen1_off", {"status": "complete", "successes": 4})
    data = json.loads(batch_layout.summary_path("exp1").read_text())
    assert set(data["runs"]) == {"gen1_on", "gen1_off"}

    # Re-reporting the same prefix overwrites just that entry, not its siblings.
    batch_layout.merge_run_summary("exp1", "gen1_on", {"status": "errors", "successes": 2})
    data = json.loads(batch_layout.summary_path("exp1").read_text())
    assert data["runs"]["gen1_on"]["status"] == "errors"
    assert data["runs"]["gen1_off"]["status"] == "complete"
