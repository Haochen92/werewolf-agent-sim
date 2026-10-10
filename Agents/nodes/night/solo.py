"""A solo role's night turn: the one body behind every ``<ROLE>_NIGHT_PHASE`` node of the parent
graph, and the payload every night turn (the pack's included) is built from.

The parent graph registers one named node per dealt role, so the graph, the traces and the
translator still read role by role; each node is ``solo_night_phase(role)``. What differs per
role comes from the registry (Agents/schemas/roles.py: the field, the no-action word, the uses)
and the card (the words); what is the same is here once: the payload, the turn, the choice.
"""

from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime

from Agents.prompts.night import night_template
from Agents.rules.night import usable_bodies
from Agents.rules.night_record import own_night_actions
from Agents.rules.seats import alive_holder, survivors
from Agents.schemas import night_output
from Agents.schemas.roles import ROLE_SPECS, cast_role_counts
from Agents.schemas.turn import ResolvedNightChoice
from Agents.state import NightTurnState, OrchestratorGraph
from Agents.tracing import GraphContext
from Agents.turn import run_memory_informed_night_action


def night_turn_payload(state: OrchestratorGraph, actor: str, role: str) -> NightTurnState:
    """The payload of one player's night turn: the public board, the actor's own record and
    what its role keeps count of. Private fields go only to the role they belong to."""
    spec = ROLE_SPECS[role]
    payload: NightTurnState = {
        "previous_strategy": state.get("agent_strategies", {}).get(actor, ""),
        "strategy_points": "",
        "current_day": state["current_day"],
        "current_round": 0,
        "day_channel": state.get("day_channel", []),
        "day_summaries": state.get("day_summaries", []),
        # Both public: the dead roster is announced, the cast census is counts-only.
        "dead_roster": state.get("dead_roster", []),
        "cast_role_counts": cast_role_counts(state.get("roles", {})),
        "lineup": state.get("lineup", []),
        "surviving_players": [p for p in survivors(state) if p != actor],
        "player_id": actor,
        "player_role": role,
        "human_player": actor in state.get("human_players", []),
        # Private: only this actor's own night record (and the pack's kills, for a wolf).
        "night_actions": own_night_actions(state.get("night_actions", []), actor, role),
    }
    if spec.uses is not None:
        payload["uses_left"] = state.get("uses_left", {}).get(role, 0)
    if role == "necromancer":
        payload["bodies"] = usable_bodies(state.get("dead_roster", []))
    if role == "speculator":
        payload["speculator_pick"] = state.get("speculator_pick") or "not yet"
    if role == "fortune_teller":
        payload["fortune_points"] = state.get("fortune_points", 0)
    return payload


def solo_night_phase(role: str):
    """The parent-graph node of one solo role's night: build the payload, run the turn, write
    the choice (and the strategy note) back."""
    template = night_template(role)
    field = ROLE_SPECS[role].target_field

    def phase(state: OrchestratorGraph, config: RunnableConfig, runtime: Runtime[GraphContext]):
        actor = alive_holder(state, role)
        assert actor is not None  # routing only enters this phase while the role is alive
        payload = night_turn_payload(state, actor, role)
        turn = run_memory_informed_night_action(
            payload, config, runtime, template, night_output(role, state.get("lineup", [])), field,
        )
        if turn is None:
            return {}
        if not isinstance(turn, ResolvedNightChoice):
            raise TypeError(f"{role} night turn resolved to unexpected turn: {turn.kind}")
        updates: dict = {}
        if turn.entry is not None:
            updates["night_choices"] = [turn.entry]
        if turn.effects.strategy:
            updates["agent_strategies"] = {actor: turn.effects.strategy}
        return updates

    phase.__name__ = f"{role}_night_phase"
    return phase
