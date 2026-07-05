"""Query-time override of the agent-knowable situation dims (players_alive / bullets_left /
ally_revealed). These are computed from game state, never trusted from the LLM's structured output —
the structural corollary of the 2026-07 dimension-accuracy audit
(evidence/phase_b/dimension_accuracy_audit/). No LLM: we hand the override a synthetic parsed cell
+ payload and assert the corrected dims. See Agents/memory/retrieval/situation_agent.py."""

from typing import Literal, get_args, get_origin

from Agents.memory.retrieval.situation_agent import (
    _computed_players_alive,
    _known_board_facts,
    _override_deterministic_dims,
)
from Agents.schemas.memory import cell_situation_schema_for


def _dummy(annotation):
    """A schema-valid placeholder for a situation-cell field (all fields are str/int/bool/Literal)."""
    if get_origin(annotation) is Literal:
        return get_args(annotation)[0]
    if annotation is bool:
        return False
    if annotation is int:
        return 0
    return "x"


def _make_cell(role: str, phase: str, **overrides):
    """A fully-populated (schema-valid) situation cell for (role, phase), with the fields under test
    set to deliberately-WRONG LLM values so a successful override is observable."""
    schema = cell_situation_schema_for(role, phase)
    assert schema is not None, f"no cell for {role}/{phase}"
    values = {name: _dummy(f.annotation) for name, f in schema.model_fields.items()}
    values.update(overrides)
    return schema(**values)


# ── players_alive ────────────────────────────────────────────────────────────────────────────
def test_players_alive_day_roster_overrides_llm():
    # LLM claims 9 alive; the role-blind day roster (self included) has 6 -> dims report 6.
    payload = {"surviving_players": ["p1", "p2", "p3", "p4", "p5", "p6"], "player_id": "p1"}
    cell = _make_cell("villager", "day_discussion", players_alive=9)
    _override_deterministic_dims(cell, payload)
    assert cell.players_alive == 6


def test_players_alive_single_actor_night_adds_self():
    # Single-actor night payloads list every living player EXCEPT the actor -> +1 for self.
    payload = {"surviving_players": ["p2", "p3", "p4", "p5"], "player_id": "p1"}
    cell = _make_cell("healer", "night_action", players_alive=9)
    _override_deterministic_dims(cell, payload)
    assert cell.players_alive == 5


def test_players_alive_wolf_uses_faction_rosters():
    payload = {"surviving_wolves": ["w1", "w2"], "surviving_villagers": ["v1", "v2", "v3", "v4"],
               "player_id": "w1"}
    cell = _make_cell("wolf", "day_discussion", players_alive=9)
    _override_deterministic_dims(cell, payload)
    assert cell.players_alive == 6


def test_players_alive_uncomputable_keeps_llm_fill():
    # No roster reachable (legacy fallback) -> leave the LLM's value untouched.
    assert _computed_players_alive({"player_id": "p1"}) is None
    cell = _make_cell("villager", "day_discussion", players_alive=7)
    _override_deterministic_dims(cell, {"player_id": "p1"})
    assert cell.players_alive == 7


# ── bullets_left ─────────────────────────────────────────────────────────────────────────────
def test_bullets_left_from_vigilante_counter():
    # Vigilante with 1 shot fired of a 2-bullet loadout -> counter reads 1; LLM under-counted to 0.
    payload = {"surviving_players": ["p2", "p3", "p4"], "player_id": "p1", "vigilante_bullets": 1}
    cell = _make_cell("vigilante", "night_action", bullets_left=0)
    _override_deterministic_dims(cell, payload)
    assert cell.bullets_left == 1


def test_bullets_left_day_cell_threaded_counter():
    payload = {"surviving_players": ["p1", "p2", "p3", "p4"], "player_id": "p1",
               "vigilante_bullets": 2}
    cell = _make_cell("vigilante", "day_discussion", bullets_left=1)
    _override_deterministic_dims(cell, payload)
    assert cell.bullets_left == 2


def test_bullets_left_missing_counter_keeps_llm_fill():
    payload = {"surviving_players": ["p2", "p3"], "player_id": "p1"}  # no vigilante_bullets
    cell = _make_cell("vigilante", "night_action", bullets_left=1)
    _override_deterministic_dims(cell, payload)
    assert cell.bullets_left == 1


# ── ally_revealed ────────────────────────────────────────────────────────────────────────────
def test_ally_revealed_true_when_partner_gone():
    # 2 wolves cast, only the actor survives -> a partner is gone -> True (LLM said False).
    payload = {"surviving_wolves": ["w1"], "surviving_villagers": ["v1", "v2", "v3"],
               "player_id": "w1", "initial_wolf_count": 2}
    cell = _make_cell("wolf", "day_discussion", ally_revealed=False)
    _override_deterministic_dims(cell, payload)
    assert cell.ally_revealed is True


def test_ally_revealed_false_when_partner_alive():
    payload = {"surviving_wolves": ["w1", "w2"], "surviving_villagers": ["v1", "v2"],
               "player_id": "w1", "initial_wolf_count": 2}
    cell = _make_cell("wolf", "day_discussion", ally_revealed=True)
    _override_deterministic_dims(cell, payload)
    assert cell.ally_revealed is False


def test_ally_revealed_missing_count_keeps_llm_fill():
    payload = {"surviving_wolves": ["w1"], "surviving_villagers": ["v1"], "player_id": "w1"}
    cell = _make_cell("wolf", "day_discussion", ally_revealed=False)
    _override_deterministic_dims(cell, payload)
    assert cell.ally_revealed is False


# ── _known_board_facts (the prompt-injection half) ─────────────────────────────────────────────
def test_known_facts_states_players_alive():
    payload = {"surviving_players": ["p1", "p2", "p3", "p4", "p5", "p6"], "player_id": "p1"}
    facts = _known_board_facts(payload, cell_situation_schema_for("villager", "day_discussion"))
    assert "Players alive right now: 6" in facts


def test_known_facts_states_bullets_and_villager_note_at_zero():
    schema = cell_situation_schema_for("vigilante", "night_action")
    with_shot = _known_board_facts(
        {"surviving_players": ["p2", "p3"], "player_id": "p1", "vigilante_bullets": 1}, schema)
    assert "Vigilante shots you have left: 1" in with_shot and "regular villager" not in with_shot
    spent = _known_board_facts(
        {"surviving_players": ["p2", "p3"], "player_id": "p1", "vigilante_bullets": 0}, schema)
    assert "Vigilante shots you have left: 0" in spent and "regular villager" in spent


def test_known_facts_states_ally_revealed():
    payload = {"surviving_wolves": ["w1"], "surviving_villagers": ["v1", "v2"],
               "player_id": "w1", "initial_wolf_count": 2}
    facts = _known_board_facts(payload, cell_situation_schema_for("wolf", "day_discussion"))
    assert "revealed or eliminated: yes" in facts


def test_known_facts_empty_when_uncomputable():
    # No roster (uncomputable players_alive) and no conditioner inputs -> nothing to inject.
    facts = _known_board_facts({"player_id": "p1"}, cell_situation_schema_for("villager", "day_discussion"))
    assert facts == ""


def test_known_facts_number_matches_the_override_value():
    # Single-source invariant: the number the prompt STATES must equal the one the override SETS,
    # so the model can never be told N and then overridden to M.
    payload = {"surviving_players": ["p2", "p3", "p4", "p5"], "player_id": "p1"}  # night: +1 for self
    schema = cell_situation_schema_for("healer", "night_action")
    facts = _known_board_facts(payload, schema)
    cell = _make_cell("healer", "night_action", players_alive=9)
    _override_deterministic_dims(cell, payload)
    assert f"Players alive right now: {cell.players_alive}" in facts
