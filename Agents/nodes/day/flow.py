"""Day-phase control flow: scheduling speakers, fanning out votes, summarizing the day.

Discussion is sequential — route_speaker is the scheduler hop that picks the next
speaker (or ends discussion) and the graph self-loops back through day_scheduler.
Voting is concurrent — fan_out_vote dispatches every survivor's vote node at once.
The per-role actor nodes these dispatch to (via Send) live in day/actors.py.
"""

from logging import getLogger as _getLogger
logger = _getLogger(__name__)

from typing import Literal

from langchain_core.runnables import RunnableConfig
from langgraph.graph import END
from langgraph.types import Send

from Agents.game_config import game_config_from_runnable
from Agents.schemas import DaySummary, FiringReason
from Agents.state import (
    DayGraphState,
)

from Agents.schemas import DaySummaryCase

from Agents.nodes.day.summary_agent import run_day_summary_agent
from Agents.observability import day_summary_span_name
from Agents.turn.scheduler import cycle_seed, select_next_speaker

from Agents.tracing import (
    langfuse,
)

def day_scheduler(state: DayGraphState):
    """No-op hub node: the fixed return point every speaker self-loops back to, so
    route_speaker can re-run from one place until discussion terminates."""
    return {}


def route_speaker(state: DayGraphState, config: RunnableConfig) -> Send | Literal["SUMMARIZE_DAY_DISCUSSION"]:
    """The scheduler hop: pick the next speaker from the day so far, or end discussion.

    Recomputes from day_channel (the scheduler is stateless), applies a lighter
    one-round cap on pre-voting days, seeds the speaker choice deterministically
    (game_id, day, utterances-so-far) and delegates ranking to select_next_speaker.
    Returns SUMMARIZE_DAY_DISCUSSION on terminate, else a Send to the chosen
    speaker's role node.
    """
    game_config = game_config_from_runnable(config)
    current_day = state.get("current_day", 1)
    surviving_players = state["surviving_villagers"] + state["surviving_wolves"]
    current_day_discussion = [
        m for m in state.get("day_channel", [])
        if m.day == current_day and m.player != "game_master"
    ]

    # Pre-voting days get a lighter cap (~one round = N); regular days use the config cap.
    num_survivors = len(surviving_players)
    cap = num_survivors if current_day < game_config.first_voting_day else game_config.utterance_cap(num_survivors)
    game_id = (config.get("configurable", {}) if config else {}).get("game_id", "")
    seed = cycle_seed(game_id, current_day, len(current_day_discussion))

    route_decision = select_next_speaker(
        day_channel=current_day_discussion,
        surviving_players=surviving_players,
        game_config=game_config,
        seed=seed,
        utterance_cap=cap,
    )

    seq = len(current_day_discussion)
    if route_decision.terminate:
        logger.info(
            "[schedule] day=%d seq=%d terminate=%s", current_day, seq, route_decision.terminate_reason,
        )
        return "SUMMARIZE_DAY_DISCUSSION"

    fr = route_decision.firing_reason
    logger.info(
        "[schedule] day=%d seq=%d tier=%s speaker=%s owes=%s",
        current_day, seq, fr.tier, route_decision.speaker, fr.owes,
    )
    role = state["roles"][route_decision.speaker]
    return build_speaker_send(state, route_decision.speaker, role, fr, game_config.opener_floor)
    
    
    
def build_speaker_send(
    state: DayGraphState,
    speaker_id: str,
    role: str,
    firing_reason: FiringReason,
    opener_floor: int = 0,
) -> Send:
    """Dispatch one speaker's role node with a common payload + role-gated private fields.

    Private fields (wolf roster, investigator results, vigilante results) are only
    attached to the role they belong to, mirroring fan_out_day. They must NOT ride
    along in a universal superset: _run_agent builds the prompt-input dict straight
    from this payload, so extra private keys reach every role's prompt input and are
    one template edit away from leaking (tests/leak_test.py guards this invariant).
    This replaces the old per-role fan-out branching.
    """
    surviving_players = state["surviving_villagers"] + state["surviving_wolves"]
    payload = {
        "human_player": speaker_id == state["human_player"],
        "day_channel": state["day_channel"],
        "day_summaries": state.get("day_summaries", []),
        "surviving_players": surviving_players,
        "player_id": speaker_id,
        "player_role": role,
        "current_day": state["current_day"],
        "current_round": 0,  # vestigial until Stage 5 removes round-based prompts
        "opener_floor": opener_floor,  # day's first N real utterances bypass the novelty gate
        "previous_strategy": state.get("agent_strategies", {}).get(speaker_id, ""),
        "strategy_points": "",
        "firing_reason": firing_reason,
    }
    if role == "wolf":
        payload["surviving_wolves"] = state["surviving_wolves"]
        payload["surviving_villagers"] = state["surviving_villagers"]
    elif role == "investigator":
        payload["investigator_results"] = state.get("investigator_results", [])
    elif role == "vigilante":
        payload["vigilante_results"] = state.get("vigilante_results", [])
    return Send(f"{role}_discuss", payload)


# Roles with day discuss/vote nodes registered in the day graph.
_DAY_ACTING_ROLES = {
    "villager",
    "wolf",
    "healer",
    "investigator",
    "serial_killer",
    "vigilante",
}


def fan_out_day(
    state: DayGraphState,
    phase: Literal["discuss", "vote"],
    allow_abstain: bool = False,
):
    """Build a concurrent Send to every surviving acting player's {role}_{phase} node.

    The shared fan-out used for voting (discussion now goes one speaker at a time
    via route_speaker). Same role-gated private-field rule as build_speaker_send:
    wolf roster / investigator / vigilante results attach only to their own role.
    """
    concurrent_nodes = []
    surviving_players = state["surviving_villagers"] + state["surviving_wolves"]
    strategies = state.get("agent_strategies", {})

    def base_payload(player: str, role: str, is_human: bool) -> dict:
        return {
            "human_player": is_human,
            "day_channel": state["day_channel"],
            "day_summaries": state.get("day_summaries", []),
            "surviving_players": surviving_players,
            "player_id": player,
            "player_role": role,
            "current_round": state["current_round"],
            "current_day": state["current_day"],
            "previous_strategy": strategies.get(player, ""),
            "strategy_points": "",
            "allow_abstain": allow_abstain,
        }

    for player in surviving_players:
        role = state["roles"][player]
        is_human = player == state["human_player"]
        if role not in _DAY_ACTING_ROLES:
            continue

        payload = base_payload(player, role, is_human)
        if role == "wolf":
            payload["surviving_wolves"] = state["surviving_wolves"]
            payload["surviving_villagers"] = state["surviving_villagers"]
        elif role == "investigator":
            payload["investigator_results"] = state["investigator_results"]
        elif role == "vigilante":
            payload["vigilante_results"] = state.get("vigilante_results", [])

        concurrent_nodes.append(Send(f"{role}_{phase}", payload))

    return concurrent_nodes


def fan_out_vote(state: DayGraphState, config: RunnableConfig):
    """Router from START_VOTING: fan every survivor out to their vote node. Abstain is
    offered only while abstain is enabled and the no-lynch streak is under the force cap."""
    game_config = game_config_from_runnable(config)
    allow_abstain = (
        game_config.abstain_enabled
        and state.get("no_lynch_streak", 0) < game_config.no_lynch_force_after
    )
    return fan_out_day(state, "vote", allow_abstain)


def summarize_day_discussion(state: DayGraphState, max_retries: int = 1):
    """Summarize the day's discussion into a DaySummary, and freeze it as a judgeable case.

    Reads this day's non-game_master messages (no-op if none); calls the summary LLM
    with a retry, falling back to the raw formatted channel on repeated failure. Runs
    in BOTH memory arms (it's pre-memory), so it emits a DaySummaryCase span for the
    day-summary judge. Writes day_summaries.
    """
    current_day = state.get("current_day", 1)
    current_day_messages = [
        message for message in state.get("day_channel", [])
        if message.day == current_day and message.player != "game_master"
    ]
    if not current_day_messages:
        return {}

    # The day summary runs in BOTH memory arms (it's pre-memory), so freeze it
    # as a judgeable case (#3). ``raw_discussion`` matches what the day-summary
    # judge consumes; ``round`` carries the message seq (sequential discussion
    # has no per-round notion). The span nests under the game trace, so
    # ``trace_id`` alone lets the builder reattach it (``game_id`` is convenience).
    raw_discussion = [
        {"player": m.player, "round": m.seq, "message": m.message}
        for m in current_day_messages
    ]
    game_id = state.get("game_id", "") or ""
    span_name = day_summary_span_name(game_id, current_day)

    with langfuse.start_as_current_observation(
        as_type="span",
        name=span_name,
        input={"day": current_day, "raw_discussion": raw_discussion},
        metadata={"eval_schema": "day_summary_case_v1"},
    ) as summary_span:
        summary, model_used = run_day_summary_agent(
            current_day, current_day_messages, max_retries,
        )

        day_summary_case = DaySummaryCase(
            span_name=span_name,
            game_id=game_id,
            day=current_day,
            raw_discussion=raw_discussion,
            summary=summary,
            model_used=model_used,
        )
        summary_span.update(
            output={"day_summary_case": day_summary_case.model_dump(mode="json")},
            metadata={
                "eval_schema": day_summary_case.schema_version,
                "day": current_day,
                "message_count": len(raw_discussion),
                "model_used": model_used,
            },
        )

    return {"day_summaries": [DaySummary(day=current_day, summary=summary)]}


def route_after_day_summary(
    state: DayGraphState,
    config: RunnableConfig,
) -> Literal["START_VOTING", "__end__"]:
    """Router after the summary: end the day with no vote on pre-voting days, else
    proceed to START_VOTING."""
    game_config = game_config_from_runnable(config)
    if state["current_day"] < game_config.first_voting_day:
        return END
    return "START_VOTING"


def start_voting(state: DayGraphState):
    """No-op entry node for the voting phase (the fan-out happens on its out-edge)."""
    return {}


def collect_votes(state: DayGraphState):
    """No-op barrier node where the fanned-out vote nodes rejoin before day resolution."""
    return {}




