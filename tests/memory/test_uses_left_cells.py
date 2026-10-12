"""Every limited-use role records its uses left in every cell, day and night, so retrieval can leave
out a lesson learned with uses left when the seat has none, and the reverse (decisions §11). The
speculator's pick is its one use; the vigilante's are its bullets."""

import pytest

from Agents.schemas.memory import (
    cell_observation_schema_for,
    cell_situation_schema_for,
    cell_strategy_schema_for,
)
from Agents.schemas.roles import ROLE_SPECS

_PHASES = ("day_discussion", "day_vote", "night_action")
_SCHEMAS = (cell_observation_schema_for, cell_strategy_schema_for, cell_situation_schema_for)


def _cells(role):
    return [(fn.__name__, phase, fn(role, phase)) for fn in _SCHEMAS for phase in _PHASES]


@pytest.mark.parametrize("role", sorted(r for r, s in ROLE_SPECS.items() if s.uses is not None))
def test_a_limited_use_role_records_its_uses_left_in_every_cell(role):
    field = "bullets_left" if role == "vigilante" else "uses_left"
    for kind, phase, cls in _cells(role):
        assert cls is not None and field in cls.model_fields, (kind, phase)


@pytest.mark.parametrize("role", sorted(r for r, s in ROLE_SPECS.items() if s.uses is None))
def test_a_role_without_limited_uses_records_none(role):
    for kind, phase, cls in _cells(role):
        if cls is not None:
            assert not {"uses_left", "bullets_left"} & set(cls.model_fields), (kind, phase)


def test_uses_left_is_counted_before_the_decision():
    # 15% of the seeding games' observations gave the count after the night's action (experiment log).
    cls = cell_observation_schema_for("sentinel", "night_action")
    assert "before acting on it" in cls.model_fields["uses_left"].description
