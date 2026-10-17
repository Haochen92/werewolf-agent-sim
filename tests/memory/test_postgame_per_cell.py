"""Guard the v6 LIVE post-game per-cell extractor (extract_postgame_per_cell): it fans out over every
(role, phase) cell in ROLE_UNITS, merges all cells' observations + strategy points into one
CellExtractionOutput, drops failed/None cells (reporting them as missing), and surfaces backup use.
No LLM calls — the per-cell worker (_extract_one_cell) is stubbed."""

from unittest.mock import patch

from Agents.memory.extraction import EXTRACTION_ROLES
from Agents.memory.extraction import extraction_agent as ea
from Agents.memory.extraction.cell_units import ROLE_UNITS
from Agents.schemas.roles import lineup

_INPUTS = {
    "formatted_roles": "player_1: villager",
    "formatted_discussions": "d",
    "formatted_strategy_notes": "s",
    "formatted_previous_strategies": "none",
    "game_outcome": "villagers",
    "lineup": lineup("serial_killer", "speculator"),
}

# The fan-out runs over the pool, and every pool role has a day and a night cell (plan 2026-10-11 §9).
_N_CELLS = sum(len(ROLE_UNITS.get(role, [])) for role in EXTRACTION_ROLES)


def test_every_pool_role_has_a_discussion_a_vote_and_a_night_cell():
    assert all([u[2] for u in ROLE_UNITS[role]] == ["day_discussion", "day_vote", "night_action"]
               for role in EXTRACTION_ROLES)
    assert _N_CELLS == 36  # 12 roles x 3; a game extracts its 10 dealt roles


def test_the_discussion_and_vote_calls_each_keep_to_their_own_phase():
    from Agents.memory.extraction.inputs import build_cell_observation_tail
    from Agents.schemas.memory import cell_observation_schema_for

    for phase, own, other in (("day_discussion", "DISCUSSION only", "separate vote cell"),
                              ("day_vote", "VOTE only", "separate discussion cell")):
        tail = build_cell_observation_tail("chanteuse", phase, phase,
                                           cell_observation_schema_for("chanteuse", phase))
        assert own in tail and other in tail and f"Tag every observation {phase}" in tail
    night = build_cell_observation_tail("chanteuse", "night", "night_action",
                                        cell_observation_schema_for("chanteuse", "night_action"))
    assert "DISCUSSION only" not in night and "VOTE only" not in night


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
        if role == "investigator" and rep_phase == "night_action":
            return None  # cell failed / no schema
        return ([f"obs:{role}"], [], "primary")

    with patch.object(ea, "_extract_one_cell", side_effect=fake):
        result = ea.extract_postgame_per_cell(_INPUTS)

    assert len(result.output.observations) == _N_CELLS - 1
    assert "missing" in result.model_used
    assert "investigator/night" in result.model_used


def test_all_cells_fail_returns_none():
    with patch.object(ea, "_extract_one_cell", return_value=None):
        assert ea.extract_postgame_per_cell(_INPUTS) is None


def test_backup_use_surfaces_in_model_used():
    def fake(prefix, role, wording, rep_phase, cache, mr, bmr, wsp):
        return ([f"obs:{role}"], [], "backup" if role == "serial_killer" else "primary")

    with patch.object(ea, "_extract_one_cell", side_effect=fake):
        result = ea.extract_postgame_per_cell(_INPUTS)

    assert "backup" in result.model_used
    assert "serial_killer" in result.model_used


def test_the_extractor_sees_a_dying_actors_last_night_marked_as_never_told():
    from Agents.memory.extraction.inputs import format_extraction_inputs
    from Agents.schemas.game_events import DeathRecord, NightActionRecord

    record = NightActionRecord(day=1, actor="player_4", action="investigate", target="player_9",
                               outcome="player_9 is Not suspicious.", result="not_suspicious")
    state = {"roles": {"player_4": "investigator", "player_9": "trailseer"}, "night_actions": [record],
             "dead_roster": [DeathRecord(player="player_4", role="investigator", day=1, phase="night")],
             "day_channel": [], "wolf_channel": [], "agent_strategies": {}, "lineup": []}
    text = format_extraction_inputs(state)["formatted_discussions"]
    assert "Night 1: player_4 (investigator) investigate player_9." in text
    assert "(They died that night and were never told this.)" in text


def test_a_draw_is_the_outcome_when_end_game_names_no_winner():
    """2026-10-17: a draw left winner None, the post-game ExtractionCase refused it, and the
    finished game was dropped."""
    from Agents.memory.extraction.inputs import format_extraction_inputs
    from Agents.schemas.evaluation import ExtractionCase

    state = {"roles": {}, "night_actions": [], "dead_roster": [], "day_channel": [],
             "wolf_channel": [], "agent_strategies": {}, "lineup": [], "winner": None}
    outcome = format_extraction_inputs(state)["game_outcome"]
    assert outcome == "draw"
    ExtractionCase(game_outcome=outcome)  # the case the post-game step builds accepts it
