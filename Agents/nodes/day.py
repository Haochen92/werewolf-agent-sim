from logging import getLogger as _getLogger
logger = _getLogger(__name__)

from typing import Literal

from langchain_core.runnables import RunnableConfig
from langgraph.graph import END
from langgraph.runtime import Runtime
from langgraph.types import Send

from Agents.game_config import game_config_from_runnable
from Agents.schemas import DaySummary, FiringReason
from Agents.state import (
    DayGraphState,
)

from Agents.prompts import DAY_SUMMARY_PROMPT, SITUATION_STANDARDS
from Agents.schemas import DaySummaryCase, DaySummaryOutput

from Agents.nodes.scheduler import cycle_seed, select_next_speaker

from Agents.tracing import (
    GraphContext,
    langfuse,
)

# Day actor nodes (thin wrappers over the shared runtime engine).
from Agents.nodes.runtime import _run_memory_informed_action
from Agents.prompts import (
    HEALER_DAY_DISCUSS,
    HEALER_DAY_VOTE,
    INVESTIGATOR_DAY_DISCUSS,
    INVESTIGATOR_DAY_VOTE,
    SERIAL_KILLER_DAY_DISCUSS,
    SERIAL_KILLER_DAY_VOTE,
    VIGILANTE_DAY_DISCUSS,
    VIGILANTE_DAY_VOTE,
    VILLAGER_DAY_DISCUSS,
    VILLAGER_DAY_VOTE,
    WOLF_DAY_DISCUSS,
    WOLF_DAY_VOTE,
)
from Agents.schemas import DayDiscussOutput, DayVoteOutput
from Agents.state import HealerDayState, InvestigatorDayState, VillagerDayState, WolfDayState


def day_scheduler(state: DayGraphState):
    """An no-op node that serves as a central return point for route_speaker nodes to return to if not termination"""
    return {}
    
    
def route_speaker(state: DayGraphState, config: RunnableConfig) -> Send | Literal["SUMMARIZE_DAY_DISCUSSION"]:
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
    game_config = game_config_from_runnable(config)
    allow_abstain = (
        game_config.abstain_enabled
        and state.get("no_lynch_streak", 0) < game_config.no_lynch_force_after
    )
    return fan_out_day(state, "vote", allow_abstain)


def _serialize_day_summary(result: DaySummaryOutput) -> str:
    parts = []

    if result.accusations:
        acc_parts = []
        for a in result.accusations:
            accusers = ", ".join(a.accusers)
            entry = (
                f"{accusers} accused {a.target} of {a.reasoning} "
                f"(evidence type: {a.evidence_type})"
            )
            if a.defense:
                entry += f"; {a.target} defended by {a.defense}"
            acc_parts.append(entry)
        parts.append("Key accusations and defenses: " + " | ".join(acc_parts))
    else:
        parts.append("Key accusations and defenses: None.")

    if result.role_claims:
        claims = [
            f"{c.player} claimed {c.claimed_role} ({c.evidence})"
            for c in result.role_claims
        ]
        parts.append("Role claims: " + "; ".join(claims))
    else:
        parts.append("Role claims: None.")

    if result.alliances:
        blocs = [
            f"{', '.join(a.players)} aligned based on {a.basis}"
            for a in result.alliances
        ]
        parts.append("Alliances and blocs: " + "; ".join(blocs))
    else:
        parts.append("Alliances and blocs: None.")

    vd = result.village_dynamics
    parts.append(
        f"Village dynamics: {vd.information_landscape} "
        f"{vd.consensus} {vd.drivers}"
    )

    return "\n".join(parts)


def summarize_day_discussion(state: DayGraphState, max_retries: int = 1):
    current_day = state.get("current_day", 1)
    current_day_messages = [
        message for message in state.get("day_channel", [])
        if message.day == current_day and message.player != "game_master"
    ]
    if not current_day_messages:
        return {}

    from Agents.llm_factory import get_llm_summary
    from Agents.formatters import format_day_channel

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
    span_name = f"day_summary_eval_{game_id}_day_{current_day}"

    prompt = DAY_SUMMARY_PROMPT.format(
        current_day=current_day,
        day_channel=format_day_channel(current_day_messages),
        situation_standards=SITUATION_STANDARDS,
    )
    with langfuse.start_as_current_observation(
        as_type="span",
        name=span_name,
        input={"day": current_day, "raw_discussion": raw_discussion},
        metadata={"eval_schema": "day_summary_case_v1"},
    ) as summary_span:
        model_used = ""
        for attempt in range(max_retries + 1):
            try:
                llm = get_llm_summary()
                result = llm.with_structured_output(DaySummaryOutput).invoke(prompt)
                summary = _serialize_day_summary(result)
                model_used = getattr(llm, "model", "") or ""
                break
            except Exception as exc:
                logger.warning(f"Day discussion summary failed for day {current_day}: {exc}")
                if attempt < max_retries:
                    continue
                logger.error(
                    f"Day discussion summary failed all retries for day {current_day}, "
                    "using fallback"
                )
                summary = format_day_channel(current_day_messages)

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
    game_config = game_config_from_runnable(config)
    if state["current_day"] < game_config.first_voting_day:
        return END
    return "START_VOTING"


def start_voting(state: DayGraphState):
    return {}


def collect_votes(state: DayGraphState):
    return {}




def villager_discuss(
    payload: VillagerDayState,
    config: RunnableConfig,
    runtime: Runtime[GraphContext],
):
    return _run_memory_informed_action(
        payload,
        config,
        runtime,
        "day_discussion",
        VILLAGER_DAY_DISCUSS,
        DayDiscussOutput,
        "day_channel",
    )


def healer_discuss(
    payload: HealerDayState,
    config: RunnableConfig,
    runtime: Runtime[GraphContext],
):
    return _run_memory_informed_action(
        payload,
        config,
        runtime,
        "day_discussion",
        HEALER_DAY_DISCUSS,
        DayDiscussOutput,
        "day_channel",
    )


def wolf_discuss(
    payload: WolfDayState,
    config: RunnableConfig,
    runtime: Runtime[GraphContext],
):
    return _run_memory_informed_action(
        payload,
        config,
        runtime,
        "day_discussion",
        WOLF_DAY_DISCUSS,
        DayDiscussOutput,
        "day_channel",
    )


def investigator_discuss(
    payload: InvestigatorDayState,
    config: RunnableConfig,
    runtime: Runtime[GraphContext],
):
    return _run_memory_informed_action(
        payload,
        config,
        runtime,
        "day_discussion",
        INVESTIGATOR_DAY_DISCUSS,
        DayDiscussOutput,
        "day_channel",
    )


def villager_vote(
    payload: VillagerDayState,
    config: RunnableConfig,
    runtime: Runtime[GraphContext],
):
    return _run_memory_informed_action(
        payload,
        config,
        runtime,
        "day_vote",
        VILLAGER_DAY_VOTE,
        DayVoteOutput,
        "day_votes",
    )


def healer_vote(
    payload: HealerDayState,
    config: RunnableConfig,
    runtime: Runtime[GraphContext],
):
    return _run_memory_informed_action(
        payload,
        config,
        runtime,
        "day_vote",
        HEALER_DAY_VOTE,
        DayVoteOutput,
        "day_votes",
    )


def wolf_vote(
    payload: WolfDayState,
    config: RunnableConfig,
    runtime: Runtime[GraphContext],
):
    return _run_memory_informed_action(
        payload,
        config,
        runtime,
        "day_vote",
        WOLF_DAY_VOTE,
        DayVoteOutput,
        "day_votes",
    )


def investigator_vote(
    payload: InvestigatorDayState,
    config: RunnableConfig,
    runtime: Runtime[GraphContext],
):
    return _run_memory_informed_action(
        payload,
        config,
        runtime,
        "day_vote",
        INVESTIGATOR_DAY_VOTE,
        DayVoteOutput,
        "day_votes",
    )


def serial_killer_discuss(
    payload: VillagerDayState,
    config: RunnableConfig,
    runtime: Runtime[GraphContext],
):
    return _run_memory_informed_action(
        payload,
        config,
        runtime,
        "day_discussion",
        SERIAL_KILLER_DAY_DISCUSS,
        DayDiscussOutput,
        "day_channel",
    )


def vigilante_discuss(
    payload: VillagerDayState,
    config: RunnableConfig,
    runtime: Runtime[GraphContext],
):
    return _run_memory_informed_action(
        payload,
        config,
        runtime,
        "day_discussion",
        VIGILANTE_DAY_DISCUSS,
        DayDiscussOutput,
        "day_channel",
    )


def serial_killer_vote(
    payload: VillagerDayState,
    config: RunnableConfig,
    runtime: Runtime[GraphContext],
):
    return _run_memory_informed_action(
        payload,
        config,
        runtime,
        "day_vote",
        SERIAL_KILLER_DAY_VOTE,
        DayVoteOutput,
        "day_votes",
    )


def vigilante_vote(
    payload: VillagerDayState,
    config: RunnableConfig,
    runtime: Runtime[GraphContext],
):
    return _run_memory_informed_action(
        payload,
        config,
        runtime,
        "day_vote",
        VIGILANTE_DAY_VOTE,
        DayVoteOutput,
        "day_votes",
    )


