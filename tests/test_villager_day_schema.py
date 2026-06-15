"""v6 dimension schema, cheap-first villager·day cell. Guards the load-bearing invariants of the
mixin DAG: the embedding composition includes only the marked free-text dims (in marker order),
the criticality numbers + direction enum stay OUT of the embed (reranker-only) and out of nothing
the model can't supply (all-required), and the `_Embed` marker never reaches a model. See
evidence/phase_b/dimension_schema_build_spec.md."""

import json

import pytest
from pydantic import ValidationError

from Agents.schemas.memory import (
    VillagerDayExtraction,
    VillagerDayObservation,
    cell_observation_schema_for,
    compose_situation_embed,
)


def _obs(**kw):
    base = dict(
        perspective="villager",
        action_phase="day_vote",
        situation="A claimed investigator accused player_3 and demanded an immediate vote.",
        information_landscape="One unverified high-stakes claim; otherwise speculative reads.",
        players_alive=7,
        distance_to_parity=2,
        is_swing=False,
        criticality_stakes="Seven alive, a mislynch is still recoverable but data is thin.",
        consensus_text="Fragile consensus forming around the accused on social momentum.",
        my_position="Holding out, unconvinced by the claim.",
        consensus_direction="opposes_my_read",
        heat_now="No suspicion on me; I have stayed quiet.",
        target_landscape="player_3 (accused, behavior-based) vs the claimant (claim only).",
        approach="Trusted the claim and voted the accused.",
        impact_on_final_game_outcome="NET POSITIVE: the accused was a wolf; the vote removed a threat.",
        immediate_response="The village swung behind the vote and the accused was eliminated.",
        net_verdict="positive",
    )
    base.update(kw)
    return VillagerDayObservation(**base)


def test_embed_leads_with_situation_and_labels_marked_dims_in_order():
    emb = compose_situation_embed(_obs())
    assert emb.startswith("A claimed investigator")
    # marker order: situation < information_landscape < stakes < consensus < my_position < heat < target
    order = [
        emb.index("A claimed investigator"),
        emb.index("Information landscape:"),
        emb.index("Stakes:"),
        emb.index("Consensus:"),
        emb.index("My position:"),
        emb.index("Heat:"),
        emb.index("Target landscape:"),
    ]
    assert order == sorted(order)


def test_criticality_numbers_and_enum_excluded_from_embed():
    # The bi-encoder mangles magnitudes/signs, so the numbers + direction enum are reranker-only.
    emb = compose_situation_embed(_obs(players_alive=7, distance_to_parity=2))
    assert "7" not in emb and "2" not in emb
    assert "opposes_my_read" not in emb


def test_empty_marked_field_drops_cleanly():
    emb = compose_situation_embed(_obs(heat_now=""))
    assert "Heat:" not in emb
    assert "Target landscape:" in emb  # later fields still present


def test_composed_situation_property_matches_helper():
    o = _obs()
    assert o.composed_situation == compose_situation_embed(o)


def test_outcome_composed_net_first():
    o = _obs()
    assert o.outcome.startswith("NET POSITIVE")
    assert o.outcome.endswith("the accused was eliminated.")


def test_extraction_schema_is_all_required_and_marker_does_not_leak():
    # flash-lite fails JSON parsing on optional/nullable fields -> the cell schema must be all-required;
    # and the _Embed marker must not appear in the model-visible JSON schema.
    sch = VillagerDayExtraction.model_json_schema()
    vobs = sch["$defs"]["VillagerDayObservation"]
    assert set(vobs["required"]) == set(vobs["properties"])
    assert "outcome" not in vobs["properties"]  # computed, not asked of the model
    assert "_Embed" not in json.dumps(sch)


def test_villager_day_registry():
    # villager·day maps to VillagerDayObservation; villager has no night cell (full-DAG coverage of
    # the other roles is asserted in test_v6_cells.py).
    assert cell_observation_schema_for("villager", "day_vote") is VillagerDayObservation
    assert cell_observation_schema_for("villager", "day_discussion") is VillagerDayObservation
    assert cell_observation_schema_for("villager", "night_action") is None


def test_invalid_enums_rejected():
    with pytest.raises(ValidationError):
        _obs(net_verdict="great")
    with pytest.raises(ValidationError):
        _obs(consensus_direction="sideways")
