"""The server's hand-written copies of engine facts must match the engine.

The translator lists, per graph node, the state fields it may write; the pacing tracker
lists the night roles and their wrapper nodes; the events schema lists the human-turn
kinds. None of those lists can be imported from the engine, because they record what the
server has decided about each thing, so they drift when the engine grows. These tests
compare them with the engine's own declarations, so that adding a state field or a role
fails here, at test time, instead of in the first live game to stream it.
"""

import typing

from Agents.schemas.roles import ROLE_SPECS
from Agents.state.day import DayGraphState
from Agents.state.night.healer import HealerNightGraph
from Agents.state.night.investigator import InvestigatorNightGraph
from Agents.state.night.serial_killer import SerialKillerNightGraph
from Agents.state.night.vigilante import VigilanteNightGraph
from Agents.state.night.wolf import WolfNightGraph
from Agents.state.orchestrator import OrchestratorGraph
from server.game import pacing, translate
from server.schemas import events as ev

# Every state a graph runs on. Per-player payload states (VillagerDayState, WolfNightState,
# ...) are left out: they are inputs to one agent's turn, never a graph's channels.
GRAPH_STATES = (
    OrchestratorGraph, DayGraphState, WolfNightGraph, HealerNightGraph,
    InvestigatorNightGraph, SerialKillerNightGraph, VigilanteNightGraph,
)

# Fields a graph state carries only to seed its nodes. No node writes them back, so no
# chunk ever carries them, and the translator has no reason to list them.
INPUT_ONLY = {
    "cast_role_counts", "player_id", "player_role", "previous_strategy",
    "strategy_points", "surviving_players",
}


def _engine_fields() -> set[str]:
    return {f for state in GRAPH_STATES for f in state.__annotations__}


def _translator_writes() -> set[str]:
    return {
        f for _handler, writes in translate._NODES.values()
        if writes is not None for f in writes
    }


def _night_roles() -> list[str]:
    """Roles with their own night subgraph: every night actor but the wolves, who act as a pack."""
    return [r for r, spec in ROLE_SPECS.items() if spec.night_action and r != "wolf"]


def test_every_field_the_translator_lists_exists_in_some_graph_state():
    stale = _translator_writes() - _engine_fields()
    assert not stale, f"translate.py lists fields the engine no longer has: {sorted(stale)}"


def test_every_graph_state_field_is_listed_by_some_node_or_declared_input_only():
    missing = _engine_fields() - _translator_writes() - INPUT_ONLY
    assert not missing, (
        f"engine state has fields no node in translate.py lists: {sorted(missing)}. "
        "Add each to the writes set of the node that commits it (with a handler if the "
        "browser needs it), or to INPUT_ONLY here if no node ever writes it.")


def test_input_only_fields_really_are_never_written():
    listed = INPUT_ONLY & _translator_writes()
    assert not listed, f"declared input-only but some node lists them as writes: {sorted(listed)}"


def test_every_night_role_has_its_translator_entries():
    for role in _night_roles():
        assert f"{role}_act" in translate._NODES, f"no act node registered for {role}"
        assert f"{role}_night_phase" in translate._NODES, f"no wrapper registered for {role}"
        assert f"{role}_target" in translate._ACTION_KINDS, f"no action kind for {role}"


def test_every_night_role_has_its_pacing_entries():
    roles = _night_roles()
    assert set(pacing._SPECIAL_UNITS) == set(roles)
    wrappers = {f"{role.upper()}_NIGHT_PHASE": role for role in roles}
    wrappers["WOLF_NIGHT_PHASE"] = "wolves"
    assert pacing.BRANCH_UNITS == wrappers


def test_the_wire_role_vocabulary_is_the_engine_role_set():
    # events.py may not import Agents/, so it repeats the role names; this pins the copy.
    assert set(typing.get_args(ev.Role)) == set(ROLE_SPECS)


def test_every_night_role_has_its_human_turn_kind():
    kinds = set(typing.get_args(ev.InputRequest.model_fields["action_kind"].annotation))
    for role in _night_roles():
        assert f"{role}_target" in kinds, f"input_request cannot name a {role} turn"
