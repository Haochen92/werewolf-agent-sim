"""What the live situation query is given (feedback 2026-10-12): the seat's own exact state that its
turn prompt states, never a field its role lacks, and a query form without the four labels that fed
only the switched-off dimension gating, while its embedded fields stay those of the stored lessons."""

from Agents.memory.retrieval.situation_agent import _UNUSED_QUERY_LABELS, _private_state, _query_cell
from Agents.schemas.memory import _Embed, cell_situation_schema_for


def test_the_private_state_names_each_roles_own_values():
    necro = _private_state({"player_id": "player_3", "player_role": "necromancer",
                            "bodies": ["player_6"], "body_conceals": 0})
    assert "You are player_3, the necromancer." in necro and "player_6" in necro and "body: 0" in necro
    teller = _private_state({"player_id": "p", "player_role": "fortune_teller", "uses_left": 1, "fortune_points": 1})
    assert "Self-bets left: 1." in teller and "Your points: 1 of 2." in teller
    wolf = _private_state({"player_id": "p", "player_role": "chanteuse", "carrier": "player_1",
                           "wolves_target": "player_4"})
    assert "carrier for the pack: player_1; the pack's target: player_4" in wolf


def test_a_field_the_role_lacks_is_not_shown():
    town = _private_state({"player_id": "p", "player_role": "healer"})
    assert town == "You are p, the healer."


def test_the_query_form_drops_the_unused_labels_and_keeps_every_embedded_field():
    cell = cell_situation_schema_for("chanteuse", "day_discussion")
    query = _query_cell(cell)
    assert not set(_UNUSED_QUERY_LABELS) & set(query.model_fields)
    embedded = lambda m: [n for n, f in m.model_fields.items() if any(isinstance(x, _Embed) for x in f.metadata)]
    assert embedded(query) == embedded(cell)
