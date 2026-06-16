"""Guard the v6 cell-extraction prefix/tail builder: the prefix must be cacheable (role/phase-neutral,
byte-identical across cells), the per-cell variation lives in the tail, and the SP stub composes."""

from Agents.memory.extraction.inputs import (
    build_cell_extraction_prefix,
    build_cell_extraction_prompt,
    build_cell_observation_tail,
)
from Agents.prompts.extraction.cell import CELL_EXTRACTION_PREFIX
from Agents.schemas.memory import cell_observation_schema_for

_INPUTS = {
    "formatted_roles": "player_1: villager",
    "formatted_discussions": "discussion text with literal {braces} in it",
    "formatted_strategy_notes": "notes",
    "formatted_previous_strategies": "none",
    "game_outcome": "villagers",
}


def test_prefix_has_no_per_cell_placeholders():
    # role/phase/menu/driver belong in the TAIL, so the prefix stays byte-identical across cells
    for tok in ("{role}", "{phase}", "{dimension_menu}", "{driver_horizon}"):
        assert tok not in CELL_EXTRACTION_PREFIX


def test_prefix_byte_identical_across_cells_for_caching():
    prefix = build_cell_extraction_prefix(_INPUTS)
    villager = build_cell_extraction_prompt(
        _INPUTS, "villager", "day", "day_vote", cell_observation_schema_for("villager", "day_vote")
    )
    wolf = build_cell_extraction_prompt(
        _INPUTS, "wolf", "night", "night_action", cell_observation_schema_for("wolf", "night_action")
    )
    # both cells start with the IDENTICAL prefix -> it caches once per game
    assert villager.startswith(prefix)
    assert wolf.startswith(prefix)


def test_tail_carries_the_per_cell_variation():
    schema = cell_observation_schema_for("villager", "day_vote")
    tail = build_cell_observation_tail("villager", "day", "day_vote", schema)
    assert "role = villager" in tail and "phase = day" in tail
    assert "DRIVER" in tail          # driver/horizon
    assert "\n- " in tail            # the dimension menu (bulleted fields)


def test_with_sp_appends_the_stub():
    schema = cell_observation_schema_for("villager", "day_vote")
    base = build_cell_extraction_prompt(_INPUTS, "villager", "day", "day_vote", schema)
    with_sp = build_cell_extraction_prompt(_INPUTS, "villager", "day", "day_vote", schema, with_sp=True)
    assert len(with_sp) > len(base)
    assert "STRATEGY POINTS" in with_sp and "STUB" in with_sp


def test_transcript_braces_survive_format():
    # .format() inserts values literally, so braces in the transcript don't break composition
    schema = cell_observation_schema_for("villager", "day_vote")
    prompt = build_cell_extraction_prompt(_INPUTS, "villager", "day", "day_vote", schema)
    assert "{braces}" in prompt
