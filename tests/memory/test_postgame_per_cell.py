"""Guard the v6 LIVE post-game per-cell extractor (extract_postgame_per_cell): it fans out over every
(role, phase) cell in ROLE_UNITS, merges all cells' observations + strategy points into one
CellExtractionOutput, drops failed/None cells (reporting them as missing), and surfaces backup use.
No LLM calls — the per-cell worker (_extract_one_cell) is stubbed."""

from unittest.mock import patch

from Agents.memory.extraction import extraction_agent as ea
from Agents.memory.extraction.cell_units import ROLE_UNITS

_INPUTS = {
    "formatted_roles": "player_1: villager",
    "formatted_discussions": "d",
    "formatted_strategy_notes": "s",
    "formatted_previous_strategies": "none",
    "game_outcome": "villagers",
}

_N_CELLS = sum(len(units) for units in ROLE_UNITS.values())  # villager day + 5 roles × (day+night)


def test_n_cells_is_eleven():
    assert _N_CELLS == 11


def test_fans_out_obs_only_by_default():
    # v7 default = OBSERVATIONS ONLY; the worker respects the with_strategy_points flag (here: False).
    def fake(prefix, role, wording, rep_phase, cache, mr, bmr, wsp):
        return ([f"obs:{role}:{rep_phase}"], [f"sp:{role}"] if wsp else [], "primary")

    with patch.object(ea, "_extract_one_cell", side_effect=fake) as m:
        result = ea.extract_postgame_per_cell(_INPUTS)

    assert m.call_count == _N_CELLS
    assert result is not None
    assert isinstance(result.output, ea.CellExtractionOutput)
    assert len(result.output.observations) == _N_CELLS
    assert len(result.output.strategy_points) == 0  # per-run SPs dropped (synthesis owns SPs)
    assert result.model_used == "per_cell"


def test_dual_when_strategy_points_requested():
    # legacy dual path (offline store-builders): with_strategy_points=True is threaded to the worker.
    def fake(prefix, role, wording, rep_phase, cache, mr, bmr, wsp):
        return ([f"obs:{role}"], [f"sp:{role}"] if wsp else [], "primary")

    with patch.object(ea, "_extract_one_cell", side_effect=fake):
        result = ea.extract_postgame_per_cell(_INPUTS, with_strategy_points=True)

    assert len(result.output.observations) == _N_CELLS
    assert len(result.output.strategy_points) == _N_CELLS


def test_none_cell_is_dropped_and_reported_missing():
    def fake(prefix, role, wording, rep_phase, cache, mr, bmr, wsp):
        if role == "villager":
            return None  # cell failed / no schema
        return ([f"obs:{role}"], [], "primary")

    with patch.object(ea, "_extract_one_cell", side_effect=fake):
        result = ea.extract_postgame_per_cell(_INPUTS)

    assert len(result.output.observations) == _N_CELLS - 1
    assert "missing" in result.model_used
    assert "villager/day" in result.model_used


def test_all_cells_fail_returns_none():
    with patch.object(ea, "_extract_one_cell", return_value=None):
        assert ea.extract_postgame_per_cell(_INPUTS) is None


def test_backup_use_surfaces_in_model_used():
    def fake(prefix, role, wording, rep_phase, cache, mr, bmr, wsp):
        return ([f"obs:{role}"], [], "backup" if role == "wolf" else "primary")

    with patch.object(ea, "_extract_one_cell", side_effect=fake):
        result = ea.extract_postgame_per_cell(_INPUTS)

    assert "backup" in result.model_used
    assert "wolf" in result.model_used
