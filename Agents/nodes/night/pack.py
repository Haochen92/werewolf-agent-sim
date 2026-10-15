"""The pack's night: a miniature of the day phase, as the wolf night was.

PREPARE_PACK_NIGHT is the scheduler hub (it commits the chat round); route_pack_speaker is the
scheduler hop (ONE wolf at a time through PACK_CHAT, the carrier first, each reading everything
said before its turn, for up to WOLF_CHAT_ROUNDS rounds, ending early once every wolf has passed
in a row); then CARRIER_KILL, the carrier's choice; then pack_fan_out_skills dispatches every
wolf's skill turn in parallel (the chanteuse's block, the illusionist's conceal); COLLECT_PACK
is the barrier. A lone wolf skips the chat. Each turn runs through the shared night engine, so
it does flag-gated retrieval and emits an EvalCase.
"""

from typing import TypedDict

from langchain_core.runnables import RunnableConfig
from langgraph.graph import END
from langgraph.runtime import Runtime
from langgraph.types import Send

from Agents.prompts.night import carrier_template, night_template, wolf_chat_template
from Agents.rules.night_record import own_night_actions
from Agents.schemas import carrier_output, night_output, wolf_chat_output
from Agents.schemas.game_events import WolfChannel
from Agents.schemas.night import NightChoice
from Agents.schemas.roles import ROLE_SPECS, roles_on, WOLVES
from Agents.schemas.turn import ResolvedNightChoice, ResolvedWolfDiscussion
from Agents.state import NightTurnState, PackNightGraph
from Agents.tracing import GraphContext
from Agents.turn import run_memory_informed_night_action
from Agents.turn.action_space import KILL_TARGET

# The chat's hard cap (owner, 2026-10-08): three rounds, a pass, ends on a full round of passes.
WOLF_CHAT_ROUNDS = 3
CARRIER_ROUND = WOLF_CHAT_ROUNDS + 1
"""The round the carrier's kill is recorded under."""
SKILL_ROUND = CARRIER_ROUND + 1
"""The round a wolf's skill turn is stamped with: its reads are sent per player, day and
round, so the carrier's skill must not share the kill's round."""

PACK_ROLES = roles_on(WOLVES)
_CHAT_TEMPLATES = {role: wolf_chat_template(role) for role in PACK_ROLES}
_CARRIER_TEMPLATES = {role: carrier_template(role) for role in PACK_ROLES}
_SKILL_TEMPLATES = {role: night_template(role) for role in PACK_ROLES}


class PackDelta(TypedDict, total=False):
    wolf_channel: list[WolfChannel]
    """One entry: a chat line, a pass, or the carrier's kill (vote=target)."""
    night_choices: list[NightChoice]
    """The carrier's kill, or a wolf's skill."""
    wolves_target: str | None
    agent_strategies: dict[str, str]
    """{player_id: updated strategy note} — present only when the strategy changed."""


def _entries(state: PackNightGraph, round_: int) -> list[WolfChannel]:
    return [m for m in state["wolf_channel"] if m.day == state["current_day"] and m.round == round_]


def _speaking_order(state: PackNightGraph) -> list[str]:
    """The carrier first, then the rest in roster order."""
    carrier = state.get("carrier")
    return [carrier, *[w for w in state["surviving_wolves"] if w != carrier]] if carrier else list(state["surviving_wolves"])


def prepare_pack_night(state: PackNightGraph):
    """The scheduler hub: every chat turn loops back here. Advances the round when every wolf
    has spoken in it; jumps to the carrier's turn when the rounds are spent, when every wolf
    passed in the same round, or when one wolf is left (nothing to discuss)."""
    if len(state["surviving_wolves"]) <= 1:
        return {"current_round": CARRIER_ROUND}
    current_round = state.get("current_round", 1)
    if current_round >= CARRIER_ROUND:
        return {"current_round": current_round}
    spoken = _entries(state, current_round)
    if {m.wolf for m in spoken} >= set(state["surviving_wolves"]):
        if all(m.passed for m in spoken):
            return {"current_round": CARRIER_ROUND}
        current_round += 1
    return {"current_round": current_round}


def _pack_payload(state: PackNightGraph, wolf: str) -> NightTurnState:
    """One wolf's turn payload: the public board, the pack's rosters and chat, its own record."""
    role = state["roles"][wolf]
    strategies = state.get("agent_strategies", {})
    payload: NightTurnState = {
        "day_channel": state["day_channel"],
        "day_summaries": state.get("day_summaries", []),
        "dead_roster": state.get("dead_roster", []),
        "cast_role_counts": state.get("cast_role_counts", {}),
        "lineup": state.get("lineup", []),
        "night_actions": own_night_actions(state.get("night_actions", []), wolf, role),
        "wolf_channel": state["wolf_channel"],
        "surviving_villagers": state["surviving_villagers"],
        "surviving_wolves": state["surviving_wolves"],
        "surviving_players": [p for p in [*state["surviving_wolves"], *state["surviving_villagers"]] if p != wolf],
        "carrier": state.get("carrier", ""),
        "wolves_target": state.get("wolves_target") or "",
        # The chat and the carrier's turn are the pack's turns (one lot for the kill); a skill
        # turn is the wolf's own.
        "pack_turn": state.get("wolves_target") is None,
        "player_id": wolf,
        "player_role": role,
        "human_player": wolf in state["human_players"],
        "current_day": state["current_day"],
        "current_round": state.get("current_round", 1),
        "previous_strategy": strategies.get(wolf, ""),
        "strategy_points": "",
    }
    spec = ROLE_SPECS[role]
    if spec.uses is not None:
        payload["uses_left"] = state.get("uses_left", {}).get(role, 0)
    return payload


def route_pack_speaker(state: PackNightGraph):
    """The scheduler hop: ONE Send to the next unspoken wolf of the round, the carrier first;
    once the chat is spent, the carrier's turn."""
    # Wolves extinct (a shot and a lynch can wipe the pack while the game continues): end the
    # subgraph with no kill.
    if not state["surviving_wolves"]:
        return END
    if state["current_round"] >= CARRIER_ROUND:
        return "START_CARRIER"
    spoken = {m.wolf for m in _entries(state, state["current_round"])}
    next_speaker = next((w for w in _speaking_order(state) if w not in spoken), None)
    if next_speaker is None:
        return []
    return [Send("PACK_CHAT", _pack_payload(state, next_speaker))]


def start_carrier(state: PackNightGraph):
    """Phase-marker no-op: the chat is over, the carrier names the kill."""
    return {}


def route_carrier(state: PackNightGraph):
    """One Send to the carrier's kill turn (the uncached twin for a human)."""
    carrier = state.get("carrier")
    if not carrier or carrier not in state["surviving_wolves"]:
        return END
    node = "CARRIER_KILL_HUMAN" if carrier in state["human_players"] else "CARRIER_KILL"
    return [Send(node, _pack_payload(state, carrier))]


def pack_fan_out_skills(state: PackNightGraph):
    """Every wolf's skill turn in parallel, after the kill is known (the illusionist decides on
    the victim; the chanteuse's block is its own). Humans go to the uncached twin."""
    sends = []
    for wolf in state["surviving_wolves"]:
        role = state["roles"][wolf]
        spec = ROLE_SPECS[role]
        if spec.uses is not None and state.get("uses_left", {}).get(role, 0) <= 0:
            continue
        node = "PACK_SKILL_HUMAN" if wolf in state["human_players"] else "PACK_SKILL"
        sends.append(Send(node, {**_pack_payload(state, wolf), "current_round": SKILL_ROUND}))
    return sends or "COLLECT_PACK"


def collect_pack(state: PackNightGraph):
    """Barrier after the skill turns."""
    return {}


def pack_chat(payload: NightTurnState, config: RunnableConfig, runtime: Runtime[GraphContext]) -> PackDelta | None:
    """One wolf's chat turn: a message to the pack, or a pass."""
    role = payload["player_role"]
    turn = run_memory_informed_night_action(
        payload, config, runtime, _CHAT_TEMPLATES[role], wolf_chat_output(payload["lineup"]), "wolf_channel",
    )
    if turn is None:
        return None
    if not isinstance(turn, ResolvedWolfDiscussion):
        raise TypeError(f"pack chat resolved to unexpected turn: {turn.kind}")
    updates: PackDelta = {"wolf_channel": [turn.entry]}
    if turn.effects.strategy:
        updates["agent_strategies"] = {payload["player_id"]: turn.effects.strategy}
    return updates


def carrier_kill(payload: NightTurnState, config: RunnableConfig, runtime: Runtime[GraphContext]) -> PackDelta | None:
    """The carrier names the pack's target: the kill the carrier makes, recorded on the channel
    so every wolf reads it."""
    role = payload["player_role"]
    turn = run_memory_informed_night_action(
        payload, config, runtime, _CARRIER_TEMPLATES[role], carrier_output(payload["lineup"]), KILL_TARGET,
    )
    if turn is None:
        return None
    if not isinstance(turn, ResolvedNightChoice) or turn.entry is None:
        raise TypeError("the carrier's turn resolved to no kill")
    updates: PackDelta = {
        "night_choices": [turn.entry],
        "wolves_target": turn.entry.target,
        "wolf_channel": [WolfChannel(
            day=payload["current_day"], round=CARRIER_ROUND, wolf=payload["player_id"],
            message="", vote=turn.entry.target or "",
        )],
    }
    if turn.effects.strategy:
        updates["agent_strategies"] = {payload["player_id"]: turn.effects.strategy}
    return updates


def pack_skill(payload: NightTurnState, config: RunnableConfig, runtime: Runtime[GraphContext]) -> PackDelta | None:
    """One wolf's skill turn: the chanteuse's block, the illusionist's conceal."""
    role = payload["player_role"]
    turn = run_memory_informed_night_action(
        payload, config, runtime, _SKILL_TEMPLATES[role], night_output(role, payload["lineup"]),
        ROLE_SPECS[role].target_field,
    )
    if turn is None:
        return None
    if not isinstance(turn, ResolvedNightChoice):
        raise TypeError(f"pack skill resolved to unexpected turn: {turn.kind}")
    updates: PackDelta = {}
    if turn.entry is not None:
        updates["night_choices"] = [turn.entry]
    if turn.effects.strategy:
        updates["agent_strategies"] = {payload["player_id"]: turn.effects.strategy}
    return updates or None
