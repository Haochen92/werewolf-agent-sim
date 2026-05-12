import random
from collections import Counter
from typing import Literal
from datetime import datetime

from langchain_core.runnables import RunnableConfig
from langgraph.graph import END
from langgraph.runtime import Runtime
from langgraph.types import Send

from Agents.state import (
    DayChannel,
    DayGraphState,
    DaySummary,
    InvestigatorResult,
    OrchestratorGraph,
    WolfNightGraph,
)

from Agents.prompts import DAY_SUMMARY_PROMPT
from Agents.schemas import DaySummaryOutput
from Agents.extraction import extract_postgame
from Agents.memory import store_observation, store_strategy, store_strategy_points
from Agents.memory_persistence import dump_memory_to_json_files
from Agents.tracing import (
    DayResolutionMetric,
    GraphContext,
    NightResolutionMetric,
    langfuse,
)

from logging import getLogger

logger = getLogger(__name__)

def initialize_game(state: OrchestratorGraph):
    # Initialize roles and players
    roles = [
        "villager",
        "villager",
        "villager",
        "villager",
        "wolf",
        "wolf",
        "healer",
        "investigator",
    ]
    characters = [f"player_{i}" for i in range(1, 9)]
    human_player = random.choice(characters)

    random.shuffle(roles)
    assigned_roles = dict(zip(characters, roles, strict=True))
    healer_player = [
        player for player, role in assigned_roles.items() if role == "healer"
    ][0]
    investigator_player = [
        player for player, role in assigned_roles.items() if role == "investigator"
    ][0]
    return {
        "day_channel": [],
        "day_summaries": [],
        "wolf_channel": [],
        "roles": assigned_roles,
        "surviving_wolves": [
            player for player, role in assigned_roles.items() if role == "wolf"
        ],
        "surviving_villagers": [
            player for player, role in assigned_roles.items() if role != "wolf"
        ],
        "current_day": 1,
        "human_player": human_player,
        "healer_player": healer_player,
        "investigator_player": investigator_player,
        "investigator_results": [],
        "day_votes": [],
        "winner": None,
    }


def prepare_round(state: DayGraphState):
    return {"current_round": state.get("current_round", 0) + 1}

def fan_out_day(state: DayGraphState, phase: Literal["discuss", "vote"]):
    concurrent_nodes = []
    surviving_players = state["surviving_villagers"] + state["surviving_wolves"]
    strategies = state.get("agent_strategies", {})

    for player in surviving_players:
        role = state["roles"][player]
        is_human = player == state["human_player"]

        if role == "villager":
            concurrent_nodes.append(
                Send(
                    f"villager_{phase}",
                    {
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
                    },
                )
            )
        elif role == "healer":
            concurrent_nodes.append(
                Send(
                    f"healer_{phase}",
                    {
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
                    },
                )
            )
        elif role == "wolf":
            concurrent_nodes.append(
                Send(
                    f"wolf_{phase}",
                    {
                        "human_player": is_human,
                        "day_channel": state["day_channel"],
                        "day_summaries": state.get("day_summaries", []),
                        "surviving_players": surviving_players,
                        "surviving_wolves": state["surviving_wolves"],
                        "surviving_villagers": state["surviving_villagers"],
                        "player_id": player,
                        "player_role": role,
                        "current_round": state["current_round"],
                        "current_day": state["current_day"],
                        "previous_strategy": strategies.get(player, ""),
                        "strategy_points": "",
                    },
                )
            )
        elif role == "investigator":
            concurrent_nodes.append(
                Send(
                    f"investigator_{phase}",
                    {
                        "human_player": is_human,
                        "day_channel": state["day_channel"],
                        "day_summaries": state.get("day_summaries", []),
                        "surviving_players": surviving_players,
                        "investigator_results": state["investigator_results"],
                        "player_id": player,
                        "player_role": role,
                        "current_round": state["current_round"],
                        "current_day": state["current_day"],
                        "previous_strategy": strategies.get(player, ""),
                        "strategy_points": "",
                    },
                )
            )

    return concurrent_nodes

def fan_out_discuss(state: DayGraphState):
    return fan_out_day(state, "discuss")


def fan_out_vote(state: DayGraphState):
    return fan_out_day(state, "vote")


def collect_discussion(state: DayGraphState):
    return {}


def check_round(state: DayGraphState) -> Literal["PREPARE_ROUND", "SUMMARIZE_DAY_DISCUSSION"]:
    if state["current_day"] == 1:
        return "SUMMARIZE_DAY_DISCUSSION"

    # Check if anyone spoke this round
    current_round_messages = [
        m for m in state["day_channel"]
        if m.day == state["current_day"] and m.round == state["current_round"]
    ]
    if not current_round_messages:
        return "SUMMARIZE_DAY_DISCUSSION"

    if state["current_round"] > 5:
        return "SUMMARIZE_DAY_DISCUSSION"

    return "PREPARE_ROUND"


def summarize_day_discussion(state: DayGraphState):
    current_day = state.get("current_day", 1)
    current_day_messages = [
        message for message in state.get("day_channel", [])
        if message.day == current_day and message.player != "game_master"
    ]
    if not current_day_messages:
        return {}

    from Agents.agents import get_llm
    from Agents.formatters import format_day_channel

    prompt = DAY_SUMMARY_PROMPT.format(
        current_day=current_day,
        day_channel=format_day_channel(current_day_messages),
    )
    try:
        result = get_llm().with_structured_output(DaySummaryOutput).invoke(prompt)
        summary = result.summary.strip()
    except Exception as exc:
        logger.warning(f"Day discussion summary failed for day {current_day}: {exc}")
        summary = format_day_channel(current_day_messages)

    return {"day_summaries": [DaySummary(day=current_day, summary=summary)]}


def route_after_day_summary(state: DayGraphState) -> Literal["START_VOTING", "__end__"]:
    if state["current_day"] == 1:
        return END
    return "START_VOTING"


def start_voting(state: DayGraphState):
    return {}


def collect_votes(state: DayGraphState):
    return {}


def prepare_wolf_night(state: WolfNightGraph):
    current_round = state.get("current_round", 1)
    if len(state["surviving_wolves"]) == 1:
        current_round = 2
    return {"current_round": current_round}


def wolf_fan_out(state: WolfNightGraph):
    concurrent_nodes = []
    strategies = state.get("agent_strategies", {})

    for wolf in state["surviving_wolves"]:
        is_human = wolf == state["human_player"]
        concurrent_nodes.append(
            Send(
                "WOLF_NIGHT_DISCUSS",
                {
                    "day_channel": state["day_channel"],
                    "day_summaries": state.get("day_summaries", []),
                    "wolf_channel": state["wolf_channel"],
                    "surviving_villagers": state["surviving_villagers"],
                    "surviving_wolves": state["surviving_wolves"],
                    "player_id": wolf,
                    "player_role": "wolf",
                    "human_player": is_human,
                    "current_day": state["current_day"],
                    "current_round": state["current_round"],
                    "previous_strategy": strategies.get(wolf, ""),
                    "strategy_points": "",
                },
            )
        )
    return concurrent_nodes


def collect_wolf_night_discussion(state: WolfNightGraph):
    if state["current_round"] >= 2:
        final_votes = [
            msg.vote
            for msg in state["wolf_channel"]
            if msg.round == 2 and msg.day == state["current_day"]
        ]
        msg_count = Counter(final_votes)
        max_votes = max(msg_count.values(), default=0)
        candidates = [player for player, votes in msg_count.items() if votes == max_votes]
        return {"wolves_kill_target": random.choice(candidates)} if candidates else {}
    return {"current_round": state["current_round"] + 1}


def check_night_end(state: WolfNightGraph) -> Literal["PREPARE_WOLF_NIGHT", "__end__"]:
    if state.get("wolves_kill_target") is not None:
        return END
    return "PREPARE_WOLF_NIGHT"


def _nullify_special_roles(
    state_update: dict,
    player: str,
    state: OrchestratorGraph,
) -> None:
    if player == state["healer_player"]:
        state_update["healer_player"] = None
    if player == state["investigator_player"]:
        state_update["investigator_player"] = None


def day_resolution(state: OrchestratorGraph, runtime: Runtime[GraphContext]):
    current_day = state.get("current_day", 1)
    day_votes = state.get("day_votes", [])
    vote_counts = Counter(vote.votee for vote in day_votes)
    max_votes = max(vote_counts.values(), default=0)
    candidates = [player for player, votes in vote_counts.items() if votes == max_votes]
    voted_player = candidates[0] if len(candidates) == 1 else None

    metric = DayResolutionMetric(
        day=current_day,
        votes=[vote.model_dump() for vote in day_votes],
        voted_player=voted_player,
        voted_player_role=state["roles"].get(voted_player) if voted_player else None,
        vote_counts=dict(vote_counts),
        tied_players=candidates if len(candidates) > 1 else [],
        no_vote=not bool(day_votes),
    )
    runtime.context["metrics"].day_resolutions.append(metric)
    with langfuse.start_as_current_observation(
        as_type="span",
        name=f"day_resolution_day_{current_day}",
    ) as span:
        span.update(metadata=metric.model_dump())

    if not day_votes:
        message = f"Day {current_day}: No vote was held today."
        return {
            "day_channel": [
                DayChannel(
                    day=current_day,
                    round=0,
                    player="game_master",
                    message=message,
                )
            ],
            "day_summaries": [
                DaySummary(day=current_day, summary=message)
            ],
        }

    vote_summary = "\n".join(f"  {v.voter} voted for {v.votee}" for v in day_votes)

    if voted_player:
        message = f"""
Here's the vote result for day {current_day}:
{vote_summary}
Player {voted_player} has been voted out and was a {state['roles'][voted_player]}.
"""
        state_update = {
            "voted_player": voted_player,
            "surviving_wolves": [
                p for p in state["surviving_wolves"] if p != voted_player
            ],
            "surviving_villagers": [
                p for p in state["surviving_villagers"] if p != voted_player
            ],
            "day_channel": [
                DayChannel(
                    day=current_day,
                    round=state.get("current_round", 1),
                    player="game_master",
                    message=message,
                )
            ],
            "day_summaries": [
                DaySummary(day=current_day, summary=message)
            ],
        }

        _nullify_special_roles(state_update, voted_player, state)
        return state_update

    message = f"""
Here's the vote result for day {current_day}:
{vote_summary}
It's a tie between players {candidates}. No one is voted out this day."""
    return {
        "day_channel": [
            DayChannel(
                day=current_day,
                round=state.get("current_round", 0),
                player="game_master",
                message=message,
            )
        ],
        "day_summaries": [
            DaySummary(day=current_day, summary=message)
        ],
    }


def night_resolution(state: OrchestratorGraph, runtime: Runtime[GraphContext]):
    wolves_target = state.get("wolves_kill_target")
    healer_target = state.get("healer_target")
    current_day = state.get("current_day", 1)
    investigator_target = state.get("investigator_target")
    kill_successful = bool(wolves_target and wolves_target != healer_target)
    healer_saved = bool(wolves_target and wolves_target == healer_target)

    metric = NightResolutionMetric(
        day=current_day,
        wolves_target=wolves_target,
        wolf_target_role=state["roles"].get(wolves_target) if wolves_target else None,
        healer_target=healer_target,
        investigator_target=investigator_target,
        investigator_target_role=(
            state["roles"].get(investigator_target) if investigator_target else None
        ),
        kill_successful=kill_successful,
        healer_saved=healer_saved,
    )
    runtime.context["metrics"].night_resolutions.append(metric)
    with langfuse.start_as_current_observation(
        as_type="span",
        name=f"night_resolution_day_{current_day}",
    ) as span:
        span.update(metadata=metric.model_dump())

    investigated_role = state["roles"].get(investigator_target, "unknown")
    investigator_update = (
        [
            InvestigatorResult(
                day=current_day,
                player_investigated=investigator_target,
                role_revealed=investigated_role,
            )
        ]
        if investigator_target
        else []
    )

    if kill_successful:
        surviving_villagers = [
            player for player in state["surviving_villagers"] if player != wolves_target
        ]
        message = (
            f"{wolves_target} was killed by the wolves last night. "
            f"They were a {state['roles'][wolves_target]}."
        )

        state_update = {
            "surviving_villagers": surviving_villagers,
            "investigator_results": investigator_update,
            "day_channel": [
                DayChannel(
                    day=current_day,
                    round=state.get("current_round", 0),
                    player="game_master",
                    message=message,
                )
            ],
            "day_summaries": [
                DaySummary(day=current_day, summary=message)
            ],
        }

        _nullify_special_roles(state_update, wolves_target, state)

        return state_update

    if healer_saved:
        message = (
            f"{wolves_target} was targeted by the wolves last night, "
            "but was saved by the healer!"
        )
        return {
            "investigator_results": investigator_update,
            "day_channel": [
                DayChannel(
                    day=current_day,
                    round=state.get("current_round", 0),
                    player="game_master",
                    message=message,
                )
            ],
            "day_summaries": [
                DaySummary(day=current_day, summary=message)
            ],
        }

    return {"investigator_results": investigator_update} if investigator_update else {}


def one_more_day(state: OrchestratorGraph):
    return {
        "current_day": state.get("current_day", 1) + 1,
        "day_votes": [],
        "wolves_kill_target": None,
        "healer_target": None,
        "investigator_target": None,
        "voted_player": None,
    }


def route_after_wolf_night(
    state: OrchestratorGraph,
) -> Literal["HEALER_NIGHT_PHASE", "INVESTIGATOR_NIGHT_PHASE", "NIGHT_RESOLUTION"]:
    if state.get("healer_player"):
        return "HEALER_NIGHT_PHASE"
    if state.get("investigator_player"):
        return "INVESTIGATOR_NIGHT_PHASE"
    return "NIGHT_RESOLUTION"


def route_after_healer_night(
    state: OrchestratorGraph,
) -> Literal["INVESTIGATOR_NIGHT_PHASE", "NIGHT_RESOLUTION"]:
    if state.get("investigator_player"):
        return "INVESTIGATOR_NIGHT_PHASE"
    return "NIGHT_RESOLUTION"


def end_game(state: OrchestratorGraph):
    winner = "villagers" if not state["surviving_wolves"] else "wolves"

    return {
        "winner": winner,
        "day_channel": [
            DayChannel(
                day=state.get("current_day", 1),
                round=0,
                player="game_master",
                message=f"Game over! The {winner} have won!",
            )
        ],
    }


def check_game_end_day(
    state: OrchestratorGraph,
) -> Literal["END_GAME", "WOLF_NIGHT_PHASE"]:
    if not state["surviving_wolves"]:
        return "END_GAME"
    if len(state["surviving_wolves"]) >= len(state["surviving_villagers"]):
        return "END_GAME"
    return "WOLF_NIGHT_PHASE"


def check_game_end_night(
    state: OrchestratorGraph,
) -> Literal["END_GAME", "ONE_MORE_DAY"]:
    if not state["surviving_wolves"]:
        return "END_GAME"
    if len(state["surviving_wolves"]) >= len(state["surviving_villagers"]):
        return "END_GAME"
    return "ONE_MORE_DAY"

def post_game_analysis(
    state: OrchestratorGraph,
    config: RunnableConfig,
    runtime: Runtime[GraphContext],
):
    store = runtime.store
    if store is None:
        raise RuntimeError("Post-game analysis requires a LangGraph runtime store.")

    configurable = config.get("configurable", {}) if config else {}
    game_id = str(
        configurable.get("game_id")
        or f"game_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    )

    # Analyse game and extract observations
    extracted_observations = extract_postgame(state)
    if not extracted_observations:
        logger.warning("No observations extracted from post-game analysis.")
        return {}

    # Store observations and strategies in memory
    store_observation(store, extracted_observations.observations, game_id)
    store_strategy_points(store, extracted_observations.strategy_points, game_id)

    strategies_dict = {
        'wolf': extracted_observations.wolf_strategy,
        'villager': extracted_observations.villager_strategy,
        'healer': extracted_observations.healer_strategy,
        'investigator': extracted_observations.investigator_strategy,
    }
    store_strategy(store, strategies_dict, game_id)
    # Temporary dev-phase persistence until memory storage is refactored for production.
    dump_memory_to_json_files(target_store=store)

    logger.info(f"Post-game analysis completed and stored for game_id: {game_id}")
