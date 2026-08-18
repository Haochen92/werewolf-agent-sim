"""Sampler action-phase selection: night decisions are sampleable only when the
caller opts in via action_phases (Phase B labels night actions on v5), while the
default stays day-only so existing frozen day sets stay reproducible."""

import pytest

from Agents.schemas.evaluation import EvalCase
from evaluation.src.core.config_schema import DatasetBuildConfig
from evaluation.src.data.sampling import (
    DEFAULT_ACTION_PHASES,
    KNOWN_ACTION_PHASES,
    sample_cases,
)


def _case(action_phase: str, *, role: str = "wolf", memory_enabled: bool = True) -> EvalCase:
    return EvalCase(
        trace_id="g1",
        player_id="p1",
        player_role=role,
        day=1,
        round=1,
        action_phase=action_phase,
        memory_enabled=memory_enabled,
    )


_GAME_LENGTHS = {"g1": 3}


def _phases(cases: list[EvalCase]) -> set[str]:
    return {case.action_phase for case in cases}


def _mixed_cases() -> list[EvalCase]:
    return [
        _case("night_action", role="wolf"),
        _case("night_action", role="healer"),
        _case("day_discussion", role="villager"),
        _case("day_vote", role="villager"),
    ]


def test_default_is_day_only():
    sampled = sample_cases(_mixed_cases(), _GAME_LENGTHS, per_role_per_phase=5)
    assert _phases(sampled) == {"day_discussion", "day_vote"}


def test_night_opt_in_includes_night_action():
    sampled = sample_cases(
        _mixed_cases(),
        _GAME_LENGTHS,
        per_role_per_phase=5,
        action_phases=["day_discussion", "day_vote", "night_action"],
    )
    assert "night_action" in _phases(sampled)


def test_night_only_excludes_day():
    sampled = sample_cases(
        _mixed_cases(),
        _GAME_LENGTHS,
        per_role_per_phase=5,
        action_phases=["night_action"],
    )
    assert _phases(sampled) == {"night_action"}


def test_unknown_phase_rejected():
    with pytest.raises(ValueError, match="Unknown action_phases"):
        sample_cases(_mixed_cases(), _GAME_LENGTHS, action_phases=["night"])


def test_default_phases_subset_of_known():
    assert DEFAULT_ACTION_PHASES <= KNOWN_ACTION_PHASES
    assert "night_action" in KNOWN_ACTION_PHASES


def test_config_knob_roundtrips():
    config = DatasetBuildConfig.model_validate(
        {
            "eval_set_id": "x",
            "trace_ids": ["g1"],
            "action_phases": ["day_vote", "night_action"],
        }
    )
    assert config.action_phases == ["day_vote", "night_action"]
