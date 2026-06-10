"""Orchestrator graph nodes: the game's spine outside the day/night sub-graphs.

Owns the OrchestratorGraph state shape and the nodes that bracket each cycle —
game setup, day-vote resolution, the day/night advance, the terminal/winner
logic, and the post-game memory pipeline. The day and night phases themselves
live in their own sub-graphs (nodes/day/, nodes/night/); this module wires the
transitions between them and decides when the game ends.
"""

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

from Agents.memory.extraction import (
    build_extraction_prompt,
    build_role_extraction_prefix,
    extract_postgame,
    extract_postgame_per_role,
    format_extraction_inputs,
)


from Agents.schemas.evaluation import ExtractionCase
from Agents.memory.deduplication import (
    run_downstream_strategy_dedup,
    run_downstream_observation_dedup,
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


# --- Game setup --------------------------------------------------------------

def initialize_game(state: OrchestratorGraph, config: RunnableConfig):
    """Set up a fresh game and return the initial OrchestratorGraph state.

    Assigns and shuffles roles, then seeds the two-layer survivor model: the
    survivor *buckets* (surviving_wolves, surviving_villagers = the non-wolf
    bucket of town + the solo SK) and the per-role *markers* (healer_player, …,
    serial_killer_player) that the rest of the game reads role-aliveness off.
    human_player is chosen but vestigial — eval runs have no human player.
    """
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



# --- Death bookkeeping (shared by day + night resolution) --------------------

def _nullify_special_roles(
    state_update: dict,
    player: str,
    state: OrchestratorGraph,
) -> None:
    """Clear the special-role marker(s) held by a player who just died.

    The *_player markers are the source of truth for a special role's aliveness:
    _faction_counts reads serial_killer_player to count the SK, and night routing
    skips a role whose marker is None. Removing a dead player from the survivor
    buckets does NOT touch the markers, so both death paths — day_resolution
    (lynch) and night_kill_resolution — call this to keep the two layers in sync.
    Mutates state_update in place.
    """
    if player == state.get("healer_player"):
        state_update["healer_player"] = None
    if player == state.get("investigator_player"):
        state_update["investigator_player"] = None
    if player == state.get("serial_killer_player"):
        state_update["serial_killer_player"] = None
    if player == state.get("vigilante_player"):
        state_update["vigilante_player"] = None


# --- Day resolution ----------------------------------------------------------

def day_resolution(state: OrchestratorGraph, runtime: Runtime[GraphContext]):
    """Resolve the day's vote into a lynch (or a no-lynch) and announce it.

    A real lynch needs a unique, non-"abstain" plurality; a tie, an abstain
    plurality, or no votes is a no-lynch day (which bumps no_lynch_streak). On a
    lynch: removes the player from both survivor buckets, nullifies any
    special-role marker they held, and writes a game_master message + day
    summary. Records a DayResolutionMetric span on every path.
    """
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




# --- Day/night advance -------------------------------------------------------

def one_more_day(state: OrchestratorGraph):
    """Advance to the next day: bump current_day and clear the day's votes and all
    night-action targets so the new cycle starts from a clean slate."""
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


# --- Terminal conditions & winner --------------------------------------------

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
    """Terminal node: compute the winner and announce it.

    Uses determine_winner; if still undecided when the day limit is hit, falls
    back to _max_days_winner (largest surviving faction, draw on a tie). Writes
    winner + a game_master announcement.
    """
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
    """Router after the day phase: END_GAME if a faction has won or the day limit
    is reached, otherwise proceed into the wolf night phase."""
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
    """Router after the night phase: END_GAME if a faction has won or the day
    limit is reached, otherwise ONE_MORE_DAY."""
    game_config = game_config_from_runnable(config)
    if determine_winner(state) is not None:
        return "END_GAME"
    if state.get("current_day", 1) >= game_config.max_days:
        return "END_GAME"
    return "ONE_MORE_DAY"



# --- Post-game memory pipeline -----------------------------------------------

def post_game_analysis(
    state: OrchestratorGraph,
    config: RunnableConfig,
    runtime: Runtime[GraphContext],
):
    """Extract observations/strategy points from the finished game and persist them.

    No-op when memory dumping is disabled: the extracted memories would be deduped
    into the ephemeral runtime store and discarded with it, so the (expensive)
    extraction LLM call would be pure waste. Otherwise: extract → trace an
    ExtractionCase span → downstream-dedup into the store → dump to JSON →
    batch-dedup. This is what seeds the next memory-store version.
    """
    store = runtime.store
    if store is None:
        raise RuntimeError("Post-game analysis requires a LangGraph runtime store.")

    # Skip the whole pipeline in no-dump runs (see docstring: extraction would be wasted).
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
    extraction_config = memory_persistence_config.extraction

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
        if extraction_config.per_role:
            prefix = build_role_extraction_prefix(extraction_inputs)
            result = extract_postgame_per_role(
                prefix,
                max_workers=extraction_config.max_workers,
                cache_prefix=extraction_config.cache_prefix,
            )
        else:
            result = extract_postgame(build_extraction_prompt(extraction_inputs))

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
    observation_dedup_stats = run_downstream_observation_dedup(
        store,
        extracted_observations.observations,
        game_id,
    )
    strategy_dedup_stats = run_downstream_strategy_dedup(
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


