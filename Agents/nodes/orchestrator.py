"""Orchestrator graph nodes: the game's spine outside the day/night sub-graphs.

Owns the nodes that bracket each cycle: the deal, day-vote resolution, the day/night advance,
the terminal/winner logic, and the post-game memory pipeline. The day and night phases
themselves live in their own sub-graphs (nodes/day/, nodes/night/); this module wires the
transitions between them and decides when the game ends.
"""

from logging import getLogger as _getLogger
logger = _getLogger(__name__)

import random
import zlib
from typing import Literal
from datetime import datetime

from langchain_core.runnables import RunnableConfig
from langgraph.config import get_stream_writer
from langgraph.runtime import Runtime

from Agents.game_config import game_config_from_runnable
from Agents.rules.night import usable_bodies
from Agents.rules.night_record import disclosure
from Agents.rules.resolution import tally_day_vote
from Agents.rules.seats import alive_holder, seat_order, survivors
from Agents.schemas import DayChannel, DaySummary, DeathRecord
from Agents.schemas.roles import (
    ACTS_WHEN_SPENT,
    FIXED_SEATS,
    LONE_KILLER,
    LONE_KILLER_ROLES,
    NEUTRAL,
    NEUTRAL_ROLES,
    ROLE_SPECS,
    TOWN,
    WINNER_OF_SIDE,
    WOLVES,
    lineup as lineup_of,
    side_of,
)
from Agents.turn.action_space import valid_targets_for_action
from Agents.turn.human_turn import announce_human_turn
from Agents.state import (
    OrchestratorGraph,
)

from Agents.memory.extraction import (
    EXTRACTION_ROLES,
    extract_postgame_per_cell,
    format_extraction_inputs,
)


from Agents.observability import extraction_span_name, freeze_case
from Agents.schemas.evaluation import ExtractionCase
from Agents.schemas.memory import BaseSituation
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

def _draw_seat(rng: random.Random, chosen: str | None, pool: list[str], human_role: str | None) -> str:
    """One drawn seat: the config's choice, else the human's requested role if it is in this
    pool, else the game's seed decides. The draw is made even when the choice is fixed, so the
    rng sequence, and so the role shuffle after it, is the same whatever was chosen."""
    drawn = rng.choice(pool)
    if chosen is not None:
        return chosen
    if human_role in pool:
        return human_role
    return drawn


def initialize_game(state: OrchestratorGraph, config: RunnableConfig):
    """Set up a fresh game and return the initial OrchestratorGraph state.

    Deals the ten seats: the eight fixed roles, then the lone killer's seat and the neutral seat
    drawn by the game's seed unless the config or a solo human's request fixed them; shuffles
    the lineup over the seats; seeds the two survivor buckets by side, the limited abilities and
    the accumulators. Human seats are dealt only when the run opts in (RunConfig.human_player =
    the seat count); default 0 leaves the list empty so eval/batch runs stay fully automated.
    """
    game_config = game_config_from_runnable(config)
    # Everything random is seeded off game_id — the single master seed. A unique uuid4 game_id
    # per game keeps draws varied; pinning the same game_id across two runs reproduces the
    # deal. No game_id (a bare unit test) -> unseeded.
    configurable = config.get("configurable", {}) if config else {}
    game_id = configurable.get("game_id") or ""
    rng = random.Random(zlib.crc32(game_id.encode())) if game_id else random.Random()
    human_role = configurable.get("human_role")
    # The request is honoured for a solo human only (the swap below is solo-only too).
    requested = human_role if int(configurable.get("human_player") or 0) == 1 else None

    lone_killer = _draw_seat(rng, game_config.lone_killer, LONE_KILLER_ROLES, requested)
    neutral = _draw_seat(rng, game_config.neutral, NEUTRAL_ROLES, requested)
    lineup = lineup_of(lone_killer, neutral)
    roles = list(lineup)
    characters = [f"{game_config.player_id_prefix}_{i}" for i in range(1, len(roles) + 1)]
    # Draw a candidate seat UNCONDITIONALLY so the role shuffle's rng sequence stays the same
    # with or without a human — then only SEAT the human when the run opted in.
    human_candidate = rng.choice(characters)
    human_seats = min(int(configurable.get("human_player") or 0), len(characters))
    human_players = [human_candidate] if human_seats else []

    rng.shuffle(roles)
    assigned_roles = dict(zip(characters, roles, strict=True))

    # Extra human seats (multi-human rooms) draw AFTER the shuffle: post-shuffle draws can't
    # perturb the role assignment, so 0-vs-1-vs-N humans on one game_id share the same cast.
    if human_seats > 1:
        remaining = [c for c in characters if c != human_candidate]
        human_players += rng.sample(remaining, human_seats - 1)

    # Optional role preference: seat is random, but the human may opt to play a specific role.
    # Swap that role onto the human's seat (a drawn role was forced into the lineup above). A
    # swap preserves the cast. SOLO-ONLY: honored only with exactly one human seat and a
    # requested role — in a shared room role choice leaks/races, so multi-human games keep the
    # untouched shuffle.
    if len(human_players) == 1 and human_role:
        human_player = human_players[0]
        if human_role not in roles:
            raise ValueError(f"Unknown human role: {human_role} (not in the pool)")
        if assigned_roles[human_player] != human_role:
            donor = next(p for p, r in assigned_roles.items() if r == human_role)
            assigned_roles[human_player], assigned_roles[donor] = (
                assigned_roles[donor],
                assigned_roles[human_player],
            )

    return {
        "day_channel": [],
        "day_summaries": [],
        "wolf_channel": [],
        "roles": assigned_roles,
        "lineup": lineup,
        "surviving_wolves": [p for p, r in assigned_roles.items() if side_of(r) == WOLVES],
        "surviving_villagers": [p for p, r in assigned_roles.items() if side_of(r) != WOLVES],
        "current_day": game_config.starting_day,
        "human_players": human_players,
        "uses_left": {role: n for role, n in game_config.starting_uses().items() if role in lineup},
        "speculator_pick": None,
        "fortune_points": 0,
        "last_body": None,
        "night_choices": [],
        "night_report": None,
        "no_lynch_streak": 0,
        "night_actions": [],
        "day_votes": [],
        "winner": None,
        "neutral_result": None,
    }


# --- Death bookkeeping (shared by day + night resolution) --------------------

def remove_from_buckets(state_update: dict, state: OrchestratorGraph, dead: list[str]) -> None:
    """Take the dead out of both survivor buckets (a role's aliveness is read off the buckets, so
    this is the whole of a death's bookkeeping). Mutates state_update in place."""
    state_update["surviving_wolves"] = [p for p in state.get("surviving_wolves", []) if p not in dead]
    state_update["surviving_villagers"] = [p for p in state.get("surviving_villagers", []) if p not in dead]


# --- Day resolution ----------------------------------------------------------

def day_resolution(state: OrchestratorGraph, runtime: Runtime[GraphContext]):
    """Resolve the day's vote into a lynch (or a no-lynch) and announce it.

    A real lynch needs a unique, non-"abstain" plurality; a tie, an abstain
    plurality, or no votes is a no-lynch day (which bumps no_lynch_streak). On a
    lynch: removes the player from both survivor buckets and writes a game_master message +
    day summary. Records a DayResolutionMetric span on every path.
    """
    current_day = state.get("current_day", 1)
    day_votes = state.get("day_votes", [])
    # The shared kernel (Agents.rules.resolution) owns the plurality classification — the
    # wire translator tallies with the SAME function, so game and wire cannot drift.
    tally = tally_day_vote(vote.votee for vote in day_votes)
    vote_counts, candidates, lynched = tally.vote_counts, tally.candidates, tally.lynched

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

    # "voted for X" reads as support in everyday English; agents misread a ballot to eliminate a
    # player as defending them (evidence/game_play_enhancement/discussion_evidence.md §6.4).
    vote_summary = "\n".join(
        f"  {v.voter} voted to abstain" if v.votee == "abstain" else f"  {v.voter} voted to eliminate {v.votee}"
        for v in day_votes
    )

    if lynched:
        message = f"""
Here's the vote result for day {current_day}:
{vote_summary}
Player {lynched} has been voted out and was a {state['roles'][lynched].replace('_', ' ')}.
"""
        # A revealed town role's night record is published with the reveal (no wills: the
        # engine's own record, which cannot be forged).
        record_line = disclosure(lynched, state["roles"][lynched], list(state.get("night_actions", [])))
        if record_line:
            message = message + record_line + "\n"
        state_update = {
            "voted_player": lynched,
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
                DaySummary(day=current_day, summary=message, source="game_master")
            ],
            # The announcement above publicly reveals the lynched player's role — record it on
            # the deterministic dead roster (phase="day").
            "dead_roster": [
                DeathRecord(
                    player=lynched,
                    role=state["roles"][lynched],
                    day=current_day,
                    phase="day",
                )
            ],
        }
        remove_from_buckets(state_update, state, [lynched])
        return state_update

    # No lynch: no votes, an abstain plurality, or a tie.
    if tally.outcome == "no_vote":
        # No ballots means no vote was held (day 1): a voting day's failed turns still cast one.
        # Not worded as a vote result, which agents read as a day-1 abstention (2026-10-04).
        message = f"\nThere is no vote on day {current_day}, so no one voted and no one is eliminated."
    else:
        if tally.outcome == "abstain":
            outcome = "The town chose to abstain. No one is eliminated today."
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
            DaySummary(day=current_day, summary=message, source="game_master")
        ],
    }


# --- Day/night advance -------------------------------------------------------

def one_more_day(state: OrchestratorGraph):
    """Advance to the next day: bump current_day and clear the day's votes and the night's
    choices so the new cycle starts from a clean slate."""
    return {
        "current_day": state.get("current_day", 1) + 1,
        "day_votes": [],
        "night_choices": None,
        "night_report": None,
        "voted_player": None,
    }


# --- Terminal conditions & winner --------------------------------------------

def side_counts(state: OrchestratorGraph) -> dict[str, int]:
    """How many living players each side has: town, wolves, lone_killer, neutral."""
    roles = state.get("roles", {})
    counts = {TOWN: 0, WOLVES: 0, LONE_KILLER: 0, NEUTRAL: 0}
    for player in survivors(state):
        role = roles.get(player)
        if role in ROLE_SPECS:
            counts[side_of(role)] += 1
    return counts


def _lone_killer_role(state: OrchestratorGraph) -> str:
    """The lone killer this game dealt, by role name (the wire's winner for that side)."""
    for role in state.get("lineup", []):
        if role in LONE_KILLER_ROLES:
            return role
    return "serial_killer"


def determine_winner(state: OrchestratorGraph) -> str | None:
    """The terminal rule (role_sheet.md, "Win logic"); None means the game continues.

    The neutral is never a member of a side but is a living voter, so it counts in the numbers
    that decide whether a side can still be out-voted. A side wins only with a member alive.
    - TOWN:        no wolf and no lone killer remain, and a town player is alive.
    - LONE KILLER: at most one other living player remains, neutral included.
    - WOLVES:      the lone killer is gone and the wolves equal or outnumber town + neutral.
    """
    counts = side_counts(state)
    wolves, town, killer, neutral = counts[WOLVES], counts[TOWN], counts[LONE_KILLER], counts[NEUTRAL]
    if wolves == 0 and killer == 0 and town > 0:
        return WINNER_OF_SIDE[TOWN]
    if killer == 1 and (town + wolves + neutral) <= 1:
        return _lone_killer_role(state)
    if killer == 0 and wolves > 0 and wolves >= town + neutral:
        return WINNER_OF_SIDE[WOLVES]
    return None


def _max_days_winner(state: OrchestratorGraph) -> str | None:
    """Cost-backstop tiebreak: the largest surviving side wins; a tie is a draw."""
    counts = side_counts(state)
    tally = {
        WINNER_OF_SIDE[TOWN]: counts[TOWN],
        WINNER_OF_SIDE[WOLVES]: counts[WOLVES],
        _lone_killer_role(state): counts[LONE_KILLER],
    }
    top = max(tally.values())
    leaders = [side for side, count in tally.items() if count == top]
    return leaders[0] if len(leaders) == 1 else None


def is_draw(state: OrchestratorGraph) -> bool:
    """A board with no side alive: the last wolf and the last town player killing each other.
    Nobody wins, and only a speculator's self-pick wins it."""
    counts = side_counts(state)
    return counts[TOWN] == 0 and counts[WOLVES] == 0 and counts[LONE_KILLER] == 0


def neutral_result(state: OrchestratorGraph, winner: str | None, points_to_win: int) -> str | None:
    """How the neutral fared, beside the winner. The speculator wins when the side it picked
    wins, alive or dead; a self-pick wins only as the last one standing; unpicked is a loss. The
    fortune teller wins on its points, whoever else won."""
    roles = state.get("roles", {})
    lineup = state.get("lineup", [])
    if "speculator" in lineup:
        pick = state.get("speculator_pick")
        if pick is None:
            return "lost"
        if pick == "self":
            standing = survivors(state)
            won = len(standing) == 1 and roles.get(standing[0]) == "speculator"
        elif pick == TOWN:
            won = winner == WINNER_OF_SIDE[TOWN]
        elif pick == WOLVES:
            won = winner == WINNER_OF_SIDE[WOLVES]
        else:
            won = winner in LONE_KILLER_ROLES
        return "won" if won else "lost"
    if "fortune_teller" in lineup:
        points = state.get("fortune_points", 0)
        return f"{'won' if points >= points_to_win else 'lost'} ({points} points)"
    return None


_WINNER_MESSAGE = {
    "villagers": "Game over! The town has won!",
    "wolves": "Game over! The wolves have won!",
    "serial_killer": "Game over! The serial killer has won!",
    "necromancer": "Game over! The necromancer has won!",
    None: "Game over! No side is left standing: the game ends in a draw.",
}
_DAY_LIMIT_MESSAGE = "Game over! The day limit was reached — the game ends in a draw."


def end_game(state: OrchestratorGraph, config: RunnableConfig):
    """Terminal node: compute the winner and announce it, with the neutral's result.

    Uses determine_winner; if still undecided when the day limit is hit, falls back to
    _max_days_winner (largest surviving side, draw on a tie). Writes winner, neutral_result and
    a game_master announcement.
    """
    game_config = game_config_from_runnable(config)
    winner = determine_winner(state)
    at_limit = winner is None and not is_draw(state) and state.get("current_day", 1) >= game_config.max_days
    if at_limit:
        winner = _max_days_winner(state)
    result = neutral_result(state, winner, game_config.fortune_points_to_win)

    message = _WINNER_MESSAGE.get(winner, _WINNER_MESSAGE[None]) if not (at_limit and winner is None) else _DAY_LIMIT_MESSAGE
    neutral_role = next((r for r in state.get("lineup", []) if r in NEUTRAL_ROLES), None)
    if neutral_role and result:
        message += f" The {neutral_role.replace('_', ' ')} {result}."

    return {
        "winner": winner,
        "neutral_result": result,
        "day_channel": [
            DayChannel(
                day=state.get("current_day", 1),
                seq=sum(1 for m in state["day_channel"] if m.day == state.get("current_day", 1)),
                player="game_master",
                message=message,
            )
        ],
    }


def check_game_end_day(
    state: OrchestratorGraph,
    config: RunnableConfig,
) -> Literal["END_GAME", "NIGHT_START"]:
    """Router after the day phase: END_GAME if a side has won, the board is a draw or the day
    limit is reached, otherwise NIGHT_START (which fans out the night actors)."""
    game_config = game_config_from_runnable(config)
    if determine_winner(state) is not None or is_draw(state):
        return "END_GAME"
    if state.get("current_day", 1) >= game_config.max_days:
        return "END_GAME"
    return "NIGHT_START"


def night_start(state: OrchestratorGraph):
    """Phase-marker no-op (START_VOTING analog): day is settled and the game continues, so
    night begins. Runs only when check_game_end_day routes past END_GAME — the single anchor
    for the night phase, which the graph otherwise encodes only positionally."""
    return {}


def night_phase_name(role: str) -> str:
    """The parent graph's node for a role's night turn: HEALER_NIGHT_PHASE; the pack's is
    PACK_NIGHT_PHASE."""
    return f"{role.upper()}_NIGHT_PHASE"


def acts_tonight(state: OrchestratorGraph, role: str) -> bool:
    """Whether a solo role takes a night turn tonight: alive, from its first night, with a use
    left when its ability is limited, the speculator only until it has picked."""
    spec = ROLE_SPECS[role]
    if spec.pack or spec.night_action is None or alive_holder(state, role) is None:
        return False
    if state.get("current_day", 1) < spec.acts_from_night:
        return False
    if (spec.uses is not None and role not in ACTS_WHEN_SPENT
            and state.get("uses_left", {}).get(role, 0) <= 0):
        return False
    if role == "necromancer" and not usable_bodies(state.get("dead_roster", []), state.get("last_body")):
        return False
    return True


def route_night_actors(state: OrchestratorGraph) -> list[str]:
    """Fan out every present night actor in one parallel superstep (NIGHT_RESOLUTION is the
    barrier): the pack if a wolf is alive, and each solo role that acts tonight. The real actor
    list computed here must never reach the wire — routers don't commit, which is what keeps a
    silent whiff silent.

    A human solo actor's turn is announced here (announce_human_turn), so their room opens as
    the night starts instead of after the slowest branch, the pack's whole talk, has ended
    (2026-10-06). A human wolf is not announced: the pack's talk is sequential and prompts at
    the turn."""
    alive_phases = []
    if state.get("surviving_wolves"):
        alive_phases.append("PACK_NIGHT_PHASE")
    for role in state.get("lineup", []):
        if acts_tonight(state, role):
            alive_phases.append(night_phase_name(role))
    # An undecided game always has a live killer side (wolves or the lone killer); the lone
    # killer may sit out night 1 (the necromancer), so the fan-out can still be the pack alone.
    assert alive_phases, "night fan-out is empty but no winner was determined"
    _announce_human_night_turns(state, alive_phases)
    return alive_phases


def _announce_human_night_turns(state: OrchestratorGraph, alive_phases: list[str]) -> None:
    """Announce each human solo actor's night turn with the targets its node will offer: every
    other survivor in seat order plus the role's no-action word (the same
    valid_targets_for_action the node uses, on the same uses), and a necromancer's bodies."""
    humans = set(state.get("human_players", []))
    standing = survivors(state)
    for role in state.get("lineup", []):
        if night_phase_name(role) not in alive_phases:
            continue
        actor = alive_holder(state, role)
        if not actor or actor not in humans:
            continue
        field = ROLE_SPECS[role].target_field
        targets = valid_targets_for_action(
            {"player_id": actor, "surviving_players": standing,
             "uses_left": state.get("uses_left", {}).get(role)}, field)
        bodies = usable_bodies(state.get("dead_roster", []), state.get("last_body")) if role == "necromancer" else []
        announce_human_turn(actor, role, field, state.get("current_day", 1), targets, bodies=bodies)


def check_game_end_night(
    state: OrchestratorGraph,
    config: RunnableConfig,
) -> Literal["END_GAME", "ONE_MORE_DAY"]:
    """Router after the night phase: END_GAME if a side has won, the board is a draw or the day
    limit is reached, otherwise ONE_MORE_DAY."""
    game_config = game_config_from_runnable(config)
    if determine_winner(state) is not None or is_draw(state):
        return "END_GAME"
    if state.get("current_day", 1) >= game_config.max_days:
        return "END_GAME"
    return "ONE_MORE_DAY"



# --- Post-game memory pipeline -----------------------------------------------

def _extracted_dimensions(item) -> dict | None:
    """The structured fields of one extracted v6 cell record, dumped the way the store write keeps
    them (store_ops: ``dimensions=model_dump``). None for a legacy Observation / StrategyPoint,
    which has no structured situation."""
    return item.model_dump(mode="json") if isinstance(item, BaseSituation) else None


def _announce_memory_extracted(output, *, day: int) -> None:
    """Stream what the finished game taught, for the replay's X-ray: the raw extraction,
    before any dedup against the store (a served game never writes the store, so there is
    no post-dedup form of it). A custom chunk, never graph state."""
    observations = [
        {"perspective": o.perspective, "action_phase": o.action_phase, "situation": o.situation,
         "approach": getattr(o, "approach", ""), "outcome": getattr(o, "outcome", ""),
         "net_verdict": getattr(o, "net_verdict", ""), "dimensions": _extracted_dimensions(o)}
        for o in output.observations
    ]
    strategy_points = [
        {"perspective": s.perspective, "action_phase": s.action_phase, "situation": s.situation,
         "action": s.action, "dimensions": _extracted_dimensions(s)}
        for s in output.strategy_points
    ]
    try:
        get_stream_writer()({"event": "memory_extracted", "day": day,
                             "observations": observations, "strategy_points": strategy_points})
    except RuntimeError:  # direct call outside a graph run (tests)
        pass


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

    memory_persistence_config = memory_persistence_config_from_runnable(config)
    extraction_config = memory_persistence_config.extraction
    persist = memory_persistence_config.dump_enabled
    # POISONING GUARD: a human-involved game is never PERSISTED — human play is out-of-distribution
    # for the store (and the memory-config role filter below can't be trusted to exclude it: roles
    # absent from the config dict default to True). Extracting for display only (no dump) is fine:
    # nothing reaches the store. Replayable, never mined.
    if state.get("human_players") and persist:
        logger.info("Human seat in game; skipping post-game extraction (poisoning guard).")
        return {}
    # A no-dump run normally skips extraction entirely (the memories would be deduped
    # into the ephemeral runtime store and discarded — the LLM cost is pure waste).
    # extract_without_dump overrides that: run + trace extraction, and stream what the game
    # taught (served games show it in the replay), but skip persistence below.
    if not persist and not extraction_config.extract_without_dump:
        logger.info("Memory dump disabled; skipping post-game extraction.")
        return {}

    configurable = config.get("configurable", {}) if config else {}
    game_id = str(
        configurable.get("game_id")
        or f"game_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    )
    # Only mine cells for roles whose memory is ENABLED this arm (e.g. town_only -> town cells only),
    # so a single-role arm builds a true single-role store instead of extracting content no one reads.
    # Absent memory_config (default runs) -> all roles (backward compatible).
    mem_cfg = configurable.get("memory_config") or {}
    extraction_roles = tuple(r for r in EXTRACTION_ROLES if mem_cfg.get(r, True))

    # Format once, use for both the LLM prompt and the trace span.
    extraction_inputs = format_extraction_inputs(state)

    span_name = extraction_span_name(game_id)
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
        # v6 post-game extraction: fan out over (role, phase) cells producing the v6 cell schema.
        # (Superseded the v5 per-role GameStrategyOutput fan-out; the v5 extractors stay in the
        # package for the offline store-builders / experiments that aren't on v6 yet.)
        result = extract_postgame_per_cell(
            extraction_inputs,
            roles=extraction_roles or EXTRACTION_ROLES,
            max_workers=extraction_config.max_workers,
            cache_prefix=extraction_config.cache_prefix,
        )

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
                    "extraction_case": freeze_case(
                        extraction_span,
                        extraction_case,
                        kind="postgame_extraction",
                        case_key="extraction_case",
                        sink=runtime.context.get("eval_sink"),
                    ),
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

    _announce_memory_extracted(result.output, day=state.get("current_day", 1))

    if not persist:
        logger.info(
            "Extraction ran (traced for measurement); skipping persistence "
            "because memory dump is disabled."
        )
        return {}

    extracted_observations = result.output

    # Store observations and strategies in memory with downstream dedup.
    observation_dedup_stats = run_downstream_observation_dedup(
        store,
        extracted_observations.observations,
        game_id,
        sink=runtime.context.get("eval_sink"),
    )
    strategy_dedup_stats = run_downstream_strategy_dedup(
        store,
        extracted_observations.strategy_points,
        game_id,
        sink=runtime.context.get("eval_sink"),
    )
    # Record the dedup outcomes on the live Metrics accumulator so they ride
    # raw_metrics into the batch record (not just the ephemeral log) — per-game
    # absorption is the store-saturation signal during seeding.
    runtime.context["metrics"].dedup_stats = {
        "observations": observation_dedup_stats.model_dump(mode="json"),
        "strategy_points": strategy_dedup_stats.model_dump(mode="json"),
    }
    logger.info(
        "Observation dedup: %s kept, %s discarded, %s failed, %s auto-kept, "
        "%s auto-discarded | Strategy dedup: %s kept, %s discarded, %s failed, "
        "%s auto-kept, %s auto-discarded",
        observation_dedup_stats.kept, observation_dedup_stats.discarded,
        observation_dedup_stats.failed, observation_dedup_stats.auto_kept,
        observation_dedup_stats.auto_discarded,
        strategy_dedup_stats.kept, strategy_dedup_stats.discarded,
        strategy_dedup_stats.failed, strategy_dedup_stats.auto_kept,
        strategy_dedup_stats.auto_discarded,
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


