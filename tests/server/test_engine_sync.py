"""The server's hand-written copies of engine facts must match the engine.

The translator lists, per graph node, the state fields it may write; the pacing tracker
lists the night roles and their wrapper nodes; the events schema lists the roles and the
human-turn kinds. None of those lists can be imported from the engine, because they record
what the server has decided about each thing, so they drift when the engine grows. These
tests compare them with the engine's own declarations, so that adding a state field or a
role fails here, at test time, instead of in the first live game to stream it.
"""

import typing

from Agents.nodes.orchestrator import night_phase_name
from Agents.schemas.roles import ROLE_SPECS, roles
from Agents.state.day import DayGraphState
from Agents.state.night import PackNightGraph
from Agents.state.orchestrator import OrchestratorGraph
from server.game import pacing, translate
from server.schemas import events as ev

# Every state a graph runs on. Per-player payload states (DayActorState, NightTurnState) are
# left out: they are inputs to one agent's turn, never a graph's channels.
GRAPH_STATES = (OrchestratorGraph, DayGraphState, PackNightGraph)

# Fields a graph state carries only to seed its nodes. No node writes them back, so no
# chunk ever carries them, and the translator has no reason to list them.
INPUT_ONLY = {
    "cast_role_counts", "player_id", "player_role", "previous_strategy",
    "strategy_points", "surviving_players", "carrier",
}


def _engine_fields() -> set[str]:
    return {f for state in GRAPH_STATES for f in state.__annotations__}


def _translator_writes() -> set[str]:
    return {
        f for _handler, writes in translate._NODES.values()
        if writes is not None for f in writes
    }


def _solo_night_roles() -> list[str]:
    """Roles of the pool with their own night node: every night actor but the pack."""
    return [r for r in roles if ROLE_SPECS[r].night_action and not ROLE_SPECS[r].pack]


def test_every_field_the_translator_lists_exists_in_some_graph_state():
    # A retired key is tolerated for recorded games (translate._RETIRED_KEYS), never live.
    stale = _translator_writes() - _engine_fields() - translate._RETIRED_KEYS
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


def test_every_solo_night_role_has_its_translator_entries():
    for role in _solo_night_roles():
        assert night_phase_name(role).lower() in translate._NODES, f"no night node registered for {role}"
        field = ROLE_SPECS[role].target_field
        assert field in translate._ACTION_KINDS, f"no action kind for {role}"


def test_every_solo_night_role_has_its_pacing_entries():
    solo = _solo_night_roles()
    assert set(pacing._SOLO_NIGHT_ROLES) == set(solo)
    assert pacing.BRANCH_UNITS == {night_phase_name(role) for role in solo} | {"PACK_NIGHT_PHASE"}


def test_the_wire_role_vocabulary_is_the_engine_role_set():
    # events.py may not import Agents/, so it repeats the role names; this pins the copies.
    assert set(typing.get_args(ev.Role)) == set(ROLE_SPECS)
    assert set(typing.get_args(ev.PoolRole)) == set(roles)
    assert set(ev.PACK_ROLES) == {r for r, spec in ROLE_SPECS.items() if spec.pack}


def test_every_night_turn_has_its_human_turn_kind():
    kinds = set(typing.get_args(ev.InputRequest.model_fields["action_kind"].annotation))
    for role in _solo_night_roles() + [r for r in roles if ROLE_SPECS[r].pack]:
        assert ROLE_SPECS[role].target_field in kinds, f"input_request cannot name a {role} turn"
    assert "carrier_kill" in kinds
