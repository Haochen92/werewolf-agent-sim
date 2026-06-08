from logging import getLogger as _getLogger
logger = _getLogger(__name__)

import random
from collections import Counter
from typing import Literal
from datetime import datetime

from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime

from Agents.game_config import game_config_from_runnable
from Agents.schemas import DayChannel, DaySummary
from Agents.state import (
    OrchestratorGraph,
)

from Agents.extraction import (
    build_extraction_prompt,
    extract_postgame,
    format_extraction_inputs,
)


from Agents.schemas.evaluation import ExtractionCase
from Agents.memory.deduplication import (
    run_downstream_dedup,
    run_observation_downstream_dedup,
)
from Agents.memory.persistence import (
    dump_memory_to_json_files_from_config,
    memory_persistence_config_from_runnable,
    run_batch_dedup_from_config,
)
from Agents.tracing import (
    DayResolutionMetric,
    GraphContext,
    langfuse,
)


def initialize_game(state: OrchestratorGraph, config: RunnableConfig):
    game_config = game_config_from_runnable(config)
    # Initialize roles and players
    roles = game_config.initial_roles.copy()
    characters = [
        f"{game_config.player_id_prefix}_{i}" for i in range(1, len(roles) + 1)
    ]
    human_player = random.choice(characters)

    random.shuffle(roles)
    assigned_roles = dict(zip(characters, roles, strict=True))

    def _first_with_role(role: str) -> str | None:
        players = [p for p, r in assigned_roles.items() if r == role]
        return players[0] if players else None

    healer_player = _first_with_role("healer")
    investigator_player = _first_with_role("investigator")
    serial_killer_player = _first_with_role("serial_killer")
    vigilante_player = _first_with_role("vigilante")
    return {
        "day_channel": [],
        "day_summaries": [],
        "wolf_channel": [],
        "roles": assigned_roles,
        "surviving_wolves": [
            player for player, role in assigned_roles.items() if role == "wolf"
        ],
        # Non-wolf bucket: town (villager/healer/investigator/vigilante) AND the solo
        # serial killer. Factional standing is read off the *_player markers, not this list.
        "surviving_villagers": [
            player for player, role in assigned_roles.items() if role != "wolf"
        ],
        "current_day": game_config.starting_day,
        "human_player": human_player,
        "healer_player": healer_player,
        "investigator_player": investigator_player,
        "serial_killer_player": serial_killer_player,
        "vigilante_player": vigilante_player,
        "vigilante_bullets": game_config.vigilante_bullets,
        "no_lynch_streak": 0,
        "investigator_results": [],
        "day_votes": [],
        "winner": None,
    }



def _nullify_special_roles(
    state_update: dict,
    player: str,
    state: OrchestratorGraph,
) -> None:
    if player == state.get("healer_player"):
        state_update["healer_player"] = None
    if player == state.get("investigator_player"):
        state_update["investigator_player"] = None
    if player == state.get("serial_killer_player"):
        state_update["serial_killer_player"] = None
    if player == state.get("vigilante_player"):
        state_update["vigilante_player"] = None


def day_resolution(state: OrchestratorGraph, runtime: Runtime[GraphContext]):
    current_day = state.get("current_day", 1)
    day_votes = state.get("day_votes", [])
    vote_counts = Counter(vote.votee for vote in day_votes)
    max_votes = max(vote_counts.values(), default=0)
    candidates = [player for player, votes in vote_counts.items() if votes == max_votes]
    plurality = candidates[0] if len(candidates) == 1 else None
    # A real lynch only when the unique plurality is a player; an "abstain" plurality (or
    # a tie, or no votes) is a no-lynch day.
    lynched = plurality if (plurality and plurality != "abstain") else None

    prev_streak = state.get("no_lynch_streak", 0)
    no_lynch_streak = 0 if lynched else prev_streak + 1

    metric = DayResolutionMetric(
        day=current_day,
        votes=[vote.model_dump() for vote in day_votes],
        voted_player=lynched,
        voted_player_role=state["roles"].get(lynched) if lynched else None,
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

    vote_summary = "\n".join(f"  {v.voter} voted for {v.votee}" for v in day_votes)

    if lynched:
        message = f"""
Here's the vote result for day {current_day}:
{vote_summary}
Player {lynched} has been voted out and was a {state['roles'][lynched]}.
"""
        state_update = {
            "voted_player": lynched,
            "no_lynch_streak": no_lynch_streak,
            "surviving_wolves": [
                p for p in state["surviving_wolves"] if p != lynched
            ],
            "surviving_villagers": [
                p for p in state["surviving_villagers"] if p != lynched
            ],
            "day_channel": [
                DayChannel(
                    day=current_day,
                    seq=sum(1 for m in state["day_channel"] if m.day == current_day),
                    player="game_master",
                    message=message,
                )
            ],
            "day_summaries": [
                DaySummary(day=current_day, summary=message)
            ],
        }
        _nullify_special_roles(state_update, lynched, state)
        return state_update

    # No lynch: no votes, an abstain plurality, or a tie.
    if not day_votes:
        outcome = "No vote was held today; no one is eliminated."
    elif plurality == "abstain":
        outcome = "The village chose to abstain. No one is eliminated today."
    else:
        outcome = f"It's a tie between {candidates}. No one is voted out this day."
    message = f"""
Here's the vote result for day {current_day}:
{vote_summary}
{outcome}"""
    return {
        "voted_player": None,
        "no_lynch_streak": no_lynch_streak,
        "day_channel": [
            DayChannel(
                day=current_day,
                seq=sum(1 for m in state["day_channel"] if m.day == current_day),
                player="game_master",
                message=message,
            )
        ],
        "day_summaries": [
            DaySummary(day=current_day, summary=message)
        ],
    }




def one_more_day(state: OrchestratorGraph):
    return {
        "current_day": state.get("current_day", 1) + 1,
        "day_votes": [],
        "wolves_kill_target": None,
        "healer_target": None,
        "investigator_target": None,
        "serial_killer_target": None,
        "vigilante_target": None,
        "voted_player": None,
    }


# The night runs in two groups (see the two-group model). GROUP 1 — all the killers plus
# the healer — acts first, because their choices determine who dies; phases are skipped
# only when their actor is absent, and the group ends at KILL_RESOLUTION:
#   wolves -> healer -> serial killer -> vigilante -> KILL_RESOLUTION
# GROUP 2 — the pure-information investigator — runs AFTER kills resolve, and only if it
# survived the night (and the game is not already decided): a dead investigator's result
# is moot, so its phase is skipped to save the call. NIGHT_FINALIZE then records the
# investigation and emits the night's single metric span.


def _faction_counts(state: OrchestratorGraph) -> tuple[int, int, int]:
    """Return (wolves, town, serial_killer) survivor counts.

    surviving_villagers is the non-wolf bucket (town + the solo SK). Town excludes the
    SK, whose aliveness is tracked by the serial_killer_player marker.
    """
    wolves = len(state.get("surviving_wolves", []))
    non_wolf = len(state.get("surviving_villagers", []))
    sk = 1 if state.get("serial_killer_player") else 0
    town = non_wolf - sk
    return wolves, town, sk


def determine_winner(state: OrchestratorGraph) -> str | None:
    """The locked 3-faction terminal rule; None means the game continues.

    Order matters. W=wolves, T=town, S=serial killer (0/1).
    - TOWN  : W==0 and S==0
    - SK    : S==1 and (T+W) <= 1  (night-immune + a guaranteed kill ⇒ can't lose; a
              1v1 day vote ties ⇒ no lynch, so declaring here is correct)
    - WOLVES: S==0 and W >= T      (classic parity, only once the SK wildcard is gone)
    """
    wolves, town, sk = _faction_counts(state)
    if wolves == 0 and sk == 0:
        return "villagers"
    if sk == 1 and (town + wolves) <= 1:
        return "serial_killer"
    if sk == 0 and wolves >= town:
        return "wolves"
    return None


def _max_days_winner(state: OrchestratorGraph) -> str | None:
    """Cost-backstop tiebreak: the largest surviving faction wins; a tie is a draw."""
    wolves, town, sk = _faction_counts(state)
    tally = {"villagers": town, "wolves": wolves, "serial_killer": sk}
    top = max(tally.values())
    leaders = [faction for faction, count in tally.items() if count == top]
    return leaders[0] if len(leaders) == 1 else None


_WINNER_MESSAGE = {
    "villagers": "Game over! The villagers have won!",
    "wolves": "Game over! The wolves have won!",
    "serial_killer": "Game over! The serial killer has won!",
    None: "Game over! The day limit was reached — the game ends in a draw.",
}


def end_game(state: OrchestratorGraph, config: RunnableConfig):
    game_config = game_config_from_runnable(config)
    winner = determine_winner(state)
    if winner is None and state.get("current_day", 1) >= game_config.max_days:
        winner = _max_days_winner(state)

    return {
        "winner": winner,
        "day_channel": [
            DayChannel(
                day=state.get("current_day", 1),
                seq=sum(1 for m in state["day_channel"] if m.day == state.get("current_day", 1)),
                player="game_master",
                message=_WINNER_MESSAGE.get(winner, _WINNER_MESSAGE[None]),
            )
        ],
    }


def check_game_end_day(
    state: OrchestratorGraph,
    config: RunnableConfig,
) -> Literal["END_GAME", "WOLF_NIGHT_PHASE"]:
    game_config = game_config_from_runnable(config)
    if determine_winner(state) is not None:
        return "END_GAME"
    if state.get("current_day", 1) >= game_config.max_days:
        return "END_GAME"
    return "WOLF_NIGHT_PHASE"


def check_game_end_night(
    state: OrchestratorGraph,
    config: RunnableConfig,
) -> Literal["END_GAME", "ONE_MORE_DAY"]:
    game_config = game_config_from_runnable(config)
    if determine_winner(state) is not None:
        return "END_GAME"
    if state.get("current_day", 1) >= game_config.max_days:
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

    # Extraction exists to write memory. When dumping is off, the extracted
    # observations/strategies are deduped into the ephemeral runtime store and then
    # discarded with it — so the (expensive) extraction LLM call is pure waste.
    # Skip the whole post-game pipeline in no-dump runs.
    memory_persistence_config = memory_persistence_config_from_runnable(config)
    if not memory_persistence_config.dump_enabled:
        logger.info("Memory dump disabled; skipping post-game extraction.")
        return {}

    configurable = config.get("configurable", {}) if config else {}
    game_id = str(
        configurable.get("game_id")
        or f"game_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    )

    # Format once, use for both the LLM prompt and the trace span.
    extraction_inputs = format_extraction_inputs(state)
    prompt = build_extraction_prompt(extraction_inputs)

    span_name = f"postgame_extraction_{game_id}"
    with langfuse.start_as_current_observation(
        as_type="span",
        name=span_name,
        input={
            "roles": state.get("roles", {}),
            "game_outcome": extraction_inputs["game_outcome"],
            "formatted_discussions": extraction_inputs["formatted_discussions"],
            "formatted_strategy_notes": extraction_inputs["formatted_strategy_notes"],
        },
        metadata={"eval_schema": "extraction_case_v1"},
    ) as extraction_span:
        result = extract_postgame(prompt)

        if result:
            extracted_observations_output = result.output
            extraction_case = ExtractionCase(
                span_name=span_name,
                game_id=game_id,
                game_outcome=extraction_inputs["game_outcome"],
                roles=state.get("roles", {}),
                formatted_discussions=extraction_inputs["formatted_discussions"],
                formatted_strategy_notes=extraction_inputs["formatted_strategy_notes"],
                observations=[
                    o.model_dump(mode="json")
                    for o in extracted_observations_output.observations
                ],
                strategy_points=[
                    s.model_dump(mode="json")
                    for s in extracted_observations_output.strategy_points
                ],
                model_used=result.model_used,
            )
            extraction_span.update(
                output={
                    "extraction_case": extraction_case.model_dump(mode="json"),
                },
                metadata={
                    "eval_schema": extraction_case.schema_version,
                    "model_used": result.model_used,
                    "observation_count": len(
                        extracted_observations_output.observations
                    ),
                    "strategy_point_count": len(
                        extracted_observations_output.strategy_points
                    ),
                },
            )

    if not result:
        logger.warning("No observations extracted from post-game analysis.")
        return {}

    extracted_observations = result.output

    # Store observations and strategies in memory with downstream dedup.
    observation_dedup_stats = run_observation_downstream_dedup(
        store,
        extracted_observations.observations,
        game_id,
    )
    strategy_dedup_stats = run_downstream_dedup(
        store,
        extracted_observations.strategy_points,
        game_id,
    )
    logger.info(
        f"Observation dedup stats: {observation_dedup_stats.kept} kept, "
        f"{observation_dedup_stats.discarded} discarded, "
        f"{observation_dedup_stats.replaced} replaced, "
        f"{observation_dedup_stats.differentiated} differentiated, "
        f"{observation_dedup_stats.failed} failed, "
        f"{observation_dedup_stats.auto_kept} auto-kept, "
        f"{observation_dedup_stats.auto_discarded} auto-discarded"
    )
    logger.info(
        f"Strategy dedup stats: {strategy_dedup_stats.kept} kept, "
        f"{strategy_dedup_stats.discarded} discarded, "
        f"{strategy_dedup_stats.replaced} replaced, "
        f"{strategy_dedup_stats.differentiated} differentiated, "
        f"{strategy_dedup_stats.failed} failed, "
        f"{strategy_dedup_stats.auto_kept} auto-kept, "
        f"{strategy_dedup_stats.auto_discarded} auto-discarded"
    )

    dump_memory_to_json_files_from_config(
        memory_persistence_config,
        target_store=store,
    )

    batch_dedup_report = run_batch_dedup_from_config(
        memory_persistence_config,
        target_store=store,
    )
    if batch_dedup_report:
        total_merged = sum(s.get("merged", 0) for s in batch_dedup_report.get("stats", []))
        total_discarded = sum(s.get("discarded", 0) for s in batch_dedup_report.get("stats", []))
        logger.info(
            "Batch dedup: %d merged, %d discarded",
            total_merged, total_discarded,
        )

    logger.info(f"Post-game analysis completed and stored for game_id: {game_id}")


