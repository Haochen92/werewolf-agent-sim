"""Guard the eval-only query-situation-dimensions carrier: EvalCase carries the structured query dims
parallel to the composed `situations` strings, and the v6 cell situation schema actually exposes the
gate enums we capture (so the model_dump is gate-screenable). No LLM."""

from Agents.schemas.evaluation import EvalCase
from Agents.schemas.memory import cell_situation_schema_for


def _evalcase(**kw):
    base = dict(player_id="player_1", player_role="villager", day=1, round=0,
                action_phase="day_vote", memory_enabled=True)
    base.update(kw)
    return EvalCase(**base)


def test_situation_dimensions_defaults_empty():
    assert _evalcase().situation_dimensions == []


def test_situation_dimensions_accepts_dim_dicts():
    dims = [{"exposure_class": "exposed", "info_landscape_class": "info_starved", "players_alive": 5}]
    ec = _evalcase(situations=["s"], situation_dimensions=dims)
    assert ec.situation_dimensions[0]["exposure_class"] == "exposed"
    # parallel to the strings
    assert len(ec.situations) == len(ec.situation_dimensions)


def test_v6_situation_cell_exposes_gate_enums():
    # the captured model_dump must carry the gate enums the screens gate on
    cell = cell_situation_schema_for("villager", "day_vote")
    assert cell is not None
    fields = cell.model_fields
    assert "exposure_class" in fields
    assert "info_landscape_class" in fields
