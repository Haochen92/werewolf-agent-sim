"""Full v6 mixin-DAG cells (step 4A). Guards the invariants across all 11 concrete cells: the
registry covers exactly the valid (role, action_phase) combinations, every cell is all-required
(flash-lite), the criticality numbers + direction enums stay OUT of the embedding string, and the
`_Embed` marker never reaches a model. See evidence/phase_b/dimension_schema_build_spec.md §2."""

import json
import typing

import pytest

from Agents.schemas import memory as M
from Agents.schemas.roles import VALID_ACTION_PHASES_BY_ROLE, roles

_SAMPLE = dict(
    situation="Aardvark accused Badger and demanded a vote.",
    information_landscape="one unverified claim, otherwise speculative",
    players_alive=61, distance_to_parity=37, is_swing=True,
    criticality_stakes="few alive, the next result is decisive",
    consensus_text="a fragile, splintered room", my_position="standing apart from the push",
    consensus_direction="opposes_my_read", heat_now="no pressure on me",
    target_landscape="two candidates remain, cases purely behavioral",
    forward_exposure="acting now would expose my hand", public_private_text="my finding clashes with the public read",
    divergence_sign="contradicts", bullets_left=4, ally_revealed=False,
    approach="voted the accused", impact_on_final_game_outcome="NET POSITIVE removed a threat",
    immediate_response="the room followed", net_verdict="positive",
)
# distinctive tokens belonging to non-embed (reranker-only) fields — must never be in the embed
_FORBIDDEN = ["61", "37", "opposes_my_read", "contradicts", "bullets", "ally_revealed"]


def _cells():
    seen = {}
    for r in roles:
        for ph in ("day_discussion", "day_vote", "night_action"):
            c = M.cell_observation_schema_for(r, ph)
            if c is not None:
                seen[c.__name__] = c
    return sorted(seen.values(), key=lambda c: c.__name__)


def _instantiate(cell):
    fields = set(cell.model_fields)
    kw = {k: v for k, v in _SAMPLE.items() if k in fields}
    kw["perspective"] = typing.get_args(cell.model_fields["perspective"].annotation)[0]
    kw["action_phase"] = typing.get_args(cell.model_fields["action_phase"].annotation)[0]
    return cell(**kw)


def test_registry_covers_exactly_valid_role_phase_combos():
    for r in roles:
        for ph in ("day_discussion", "day_vote", "night_action"):
            cell = M.cell_observation_schema_for(r, ph)
            valid = ph in VALID_ACTION_PHASES_BY_ROLE[r]
            assert (cell is not None) == valid, f"{r}/{ph} valid={valid} cell={cell}"


def test_eleven_distinct_cells():
    assert len(_cells()) == 11


@pytest.mark.parametrize("cell", _cells(), ids=lambda c: c.__name__)
def test_cell_is_all_required_and_marker_free(cell):
    sch = cell.model_json_schema()
    assert set(sch["required"]) == set(sch["properties"]), f"{cell.__name__} has optional fields"
    assert "outcome" not in sch["properties"]  # computed, not asked of the model
    assert "_Embed" not in json.dumps(sch)


@pytest.mark.parametrize("cell", _cells(), ids=lambda c: c.__name__)
def test_numbers_and_enums_excluded_from_embed(cell):
    emb = _instantiate(cell).composed_situation
    assert emb.startswith("Aardvark"), cell.__name__
    leaked = [t for t in _FORBIDDEN if t in emb]
    assert not leaked, f"{cell.__name__} leaked reranker-only tokens into embed: {leaked}"


def test_day_cells_carry_consensus_and_heat_night_cells_do_not():
    healer_day = M.cell_observation_schema_for("healer", "day_vote")
    healer_night = M.cell_observation_schema_for("healer", "night_action")
    assert "consensus_text" in healer_day.model_fields and "heat_now" in healer_day.model_fields
    assert "consensus_text" not in healer_night.model_fields
    assert "heat_now" not in healer_night.model_fields


def test_situation_cell_registry_parity_with_observation_cells():
    for r in roles:
        for ph in ("day_discussion", "day_vote", "night_action"):
            sit = M.cell_situation_schema_for(r, ph)
            obs = M.cell_observation_schema_for(r, ph)
            assert (sit is None) == (obs is None), f"{r}/{ph} registry parity"


@pytest.mark.parametrize("role,phase", [
    ("villager", "day_vote"), ("wolf", "day_vote"), ("wolf", "night_action"),
    ("healer", "day_vote"), ("healer", "night_action"), ("vigilante", "day_vote"),
    ("investigator", "night_action"), ("serial_killer", "day_vote"),
])
def test_situation_embed_matches_observation_embed(role, phase):
    """The live-query situation cell must compose the IDENTICAL embed string as the stored observation
    cell for the same field values — the symmetry that lets a query match the store."""
    sit_cls = M.cell_situation_schema_for(role, phase)
    obs_cls = M.cell_observation_schema_for(role, phase)
    sit = sit_cls(**{k: v for k, v in _SAMPLE.items() if k in sit_cls.model_fields})
    okw = {k: v for k, v in _SAMPLE.items() if k in obs_cls.model_fields}
    okw["perspective"] = typing.get_args(obs_cls.model_fields["perspective"].annotation)[0]
    okw["action_phase"] = typing.get_args(obs_cls.model_fields["action_phase"].annotation)[0]
    okw.update(approach="a", impact_on_final_game_outcome="b", immediate_response="c", net_verdict="positive")
    assert sit.composed_situation == obs_cls(**okw).composed_situation


def test_conditioners_on_the_right_roles():
    assert "bullets_left" in M.cell_observation_schema_for("vigilante", "day_vote").model_fields
    assert "ally_revealed" in M.cell_observation_schema_for("wolf", "day_vote").model_fields
    assert "ally_revealed" not in M.cell_observation_schema_for("serial_killer", "day_vote").model_fields
    assert "bullets_left" not in M.cell_observation_schema_for("villager", "day_vote").model_fields
