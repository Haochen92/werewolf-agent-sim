import random
from collections import Counter
from typing import Literal
from datetime import datetime

from langchain_core.runnables import RunnableConfig
from langgraph.graph import END
from langgraph.runtime import Runtime
from langgraph.types import Send

from Agents.game_config import game_config_from_runnable
from Agents.schemas import DayChannel, DaySummary, InvestigatorResult, FiringReason
from Agents.state import (
    DayGraphState,
    OrchestratorGraph,
    WolfNightGraph,
)

from Agents.prompts import DAY_SUMMARY_PROMPT, SITUATION_STANDARDS
from Agents.schemas import DaySummaryOutput
from Agents.extraction import (
    build_extraction_prompt,
    extract_postgame,
    format_extraction_inputs,
)

from Agents.scheduler import cycle_seed, select_next_speaker

from Agents.schemas.evaluation import ExtractionCase
from Agents.memory_deduplication import (
    run_downstream_dedup,
    run_observation_downstream_dedup,
)
from Agents.memory_persistence import (
    dump_memory_to_json_files_from_config,
    memory_persistence_config_from_runnable,
    run_batch_dedup_from_config,
)
from Agents.tracing import (
    DayResolutionMetric,
    GraphContext,
    NightResolutionMetric,
    langfuse,
)

from logging import getLogger

logger = getLogger(__name__)

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
    """Dispatch one speaker's role node with a universal payload.

    Every role gets the same superset of fields; each role node reads only the
    subset it needs (LangGraph ignores extra keys on a Send payload). This replaces
    the old per-role fan-out branching.
    """
    surviving_players = state["surviving_villagers"] + state["surviving_wolves"]
    return Send(
        f"{role}_discuss",
        {
            "human_player": speaker_id == state["human_player"],
            "day_channel": state["day_channel"],
            "day_summaries": state.get("day_summaries", []),
            "surviving_players": surviving_players,
            "surviving_wolves": state["surviving_wolves"],
            "surviving_villagers": state["surviving_villagers"],
            "investigator_results": state.get("investigator_results", []),
            "vigilante_results": state.get("vigilante_results", []),
            "player_id": speaker_id,
            "player_role": role,
            "current_day": state["current_day"],
            "current_round": 0,  # vestigial until Stage 5 removes round-based prompts
            "opener_floor": opener_floor,  # day's first N real utterances bypass the novelty gate
            "previous_strategy": state.get("agent_strategies", {}).get(speaker_id, ""),
            "strategy_points": "",
            "firing_reason": firing_reason,
        },
    )


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
            "vigilante_results": state.get("vigilante_results", []),
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

    from Agents.agents import get_llm_summary
    from Agents.formatters import format_day_channel

    prompt = DAY_SUMMARY_PROMPT.format(
        current_day=current_day,
        day_channel=format_day_channel(current_day_messages),
        situation_standards=SITUATION_STANDARDS,
    )
    for attempt in range(max_retries + 1):
        try:
            result = get_llm_summary().with_structured_output(DaySummaryOutput).invoke(prompt)
            summary = _serialize_day_summary(result)
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


# Public death-announcement flavor per attacker: (verb, subject phrase). Reveals the
# attacker TYPE (so the town learns an SK/vigilante exists once they act) but never the
# attacker's identity.
_ATTACK_FLAVOR = {
    "wolves": ("killed", "the wolves"),
    "serial_killer": ("stabbed", "the serial killer"),
    "vigilante": ("shot", "the vigilante"),
}


def _join(items: list[str]) -> str:
    if len(items) <= 1:
        return items[0] if items else ""
    return ", ".join(items[:-1]) + " and " + items[-1]


def night_kill_resolution(state: OrchestratorGraph, runtime: Runtime[GraphContext]):
    """Resolve the night's kills (wolves / SK / vigilante) jointly.

    Runs BEFORE the investigator phase so a player killed this night does not act
    (the investigator is gated on surviving this resolution — its result would be
    moot). The healer is exempt: it acts in the pre-resolution group, so its
    protection still applies even if the healer itself dies tonight.

    Builds this night's NightResolutionMetric (investigator fields filled later in
    night_finalize) and appends it without emitting the langfuse span yet, so the
    night gets a single span carrying both kill and investigation data.
    """
    current_day = state.get("current_day", 1)
    wolves_target = state.get("wolves_kill_target")
    healer_target = state.get("healer_target")
    serial_killer_target = state.get("serial_killer_target")
    vigilante_target = state.get("vigilante_target")
    sk_player = state.get("serial_killer_player")

    roles = state["roles"]
    wolves_before, town_before, sk_before = _faction_counts(state)

    # Who attacked whom this night (a target may be hit by more than one killer).
    attacks_on: dict[str, list[str]] = {}
    for target, attacker in (
        (wolves_target, "wolves"),
        (serial_killer_target, "serial_killer"),
        (vigilante_target, "vigilante"),
    ):
        if target:
            attacks_on.setdefault(target, []).append(attacker)

    # Resolve protection + SK night-immunity once over the whole set. A player attacked
    # by multiple killers still dies at most once; the immune SK never dies at night and
    # such whiffs are SILENT (announcing them would out the SK).
    def _resolved(target: str) -> str:
        if target == sk_player:
            return "immune"  # silent whiff
        if target == healer_target:
            return "saved"
        return "killed"

    outcomes = {t: _resolved(t) for t in attacks_on}
    deaths = sorted(t for t, o in outcomes.items() if o == "killed")

    kill_successful = bool(wolves_target and wolves_target in deaths)
    healer_saved = bool(wolves_target and wolves_target == healer_target)
    serial_killer_kill_landed = bool(serial_killer_target and serial_killer_target in deaths)
    vigilante_kill_landed = bool(vigilante_target and vigilante_target in deaths)

    # Investigator fields are filled in night_finalize (it acts after this resolution).
    metric = NightResolutionMetric(
        day=current_day,
        wolves_target=wolves_target,
        wolf_target_role=roles.get(wolves_target) if wolves_target else None,
        healer_target=healer_target,
        investigator_target=None,
        investigator_target_role=None,
        kill_successful=kill_successful,
        healer_saved=healer_saved,
        serial_killer_target=serial_killer_target,
        serial_killer_target_role=roles.get(serial_killer_target) if serial_killer_target else None,
        vigilante_target=vigilante_target,
        vigilante_target_role=roles.get(vigilante_target) if vigilante_target else None,
        serial_killer_kill_landed=serial_killer_kill_landed,
        vigilante_kill_landed=vigilante_kill_landed,
        deaths=deaths,
        wolves_before=wolves_before,
        town_before=town_before,
        sk_before=sk_before,
    )
    runtime.context["metrics"].night_resolutions.append(metric)

    state_update: dict = {}

    # The vigilante spends a bullet whenever it takes a shot, even if healed or whiffed.
    if vigilante_target:
        state_update["vigilante_bullets"] = max(0, state.get("vigilante_bullets", 0) - 1)

    # A shot at the night-immune target (the SK) doesn't kill, but the vigilante learns
    # the target was immune — a private, reliable confirmation of the serial killer.
    # (A shot stopped by a heal does NOT trigger this, so there is no false positive.)
    if vigilante_target and outcomes.get(vigilante_target) == "immune":
        state_update["vigilante_results"] = [
            f"Night of day {current_day}: you shot {vigilante_target}, but they were unharmed "
            f"— immune to night kills, which confirms {vigilante_target} is the serial killer."
        ]

    lines: list[str] = []
    announced_save = False
    for target in sorted(attacks_on):
        outcome = outcomes[target]
        if outcome == "immune":
            continue  # silent
        attackers = attacks_on[target]
        phrase = _join([_ATTACK_FLAVOR[a][1] for a in attackers])
        if outcome == "saved":
            # Use a neutral verb so it doesn't read as "killed ... but saved".
            lines.append(f"{target} was attacked by {phrase} but was saved by the healer!")
            announced_save = True
        else:  # killed
            verb = _ATTACK_FLAVOR[attackers[0]][0] if len(attackers) == 1 else "attacked"
            lines.append(
                f"{target} was {verb} by {phrase} last night. They were a {roles[target]}."
            )
            _nullify_special_roles(state_update, target, state)

    if not deaths and not announced_save:
        lines.append("No one died last night.")

    if deaths:
        state_update["surviving_wolves"] = [
            p for p in state["surviving_wolves"] if p not in deaths
        ]
        state_update["surviving_villagers"] = [
            p for p in state["surviving_villagers"] if p not in deaths
        ]

    message = f"Night of day {current_day}: " + " ".join(lines)
    state_update["day_channel"] = [
        DayChannel(
            day=current_day,
            seq=sum(1 for m in state["day_channel"] if m.day == current_day),
            player="game_master",
            message=message,
        )
    ]
    state_update["day_summaries"] = [DaySummary(day=current_day, summary=message)]
    return state_update


def night_finalize(state: OrchestratorGraph, runtime: Runtime[GraphContext]):
    """Record the investigator's result (if it acted) and emit the night's metric span.

    The investigator runs only when it survived night_kill_resolution and the game is
    not already decided, so reaching here with an investigator_target means a live
    investigation. One langfuse span per night carries both kill and investigation data.
    """
    current_day = state.get("current_day", 1)
    investigator_target = state.get("investigator_target")
    roles = state["roles"]

    investigator_update = (
        [
            InvestigatorResult(
                day=current_day,
                player_investigated=investigator_target,
                role_revealed=roles.get(investigator_target, "unknown"),
            )
        ]
        if investigator_target
        else []
    )

    night_metrics = runtime.context["metrics"].night_resolutions
    if night_metrics:
        nr = night_metrics[-1]
        nr.investigator_target = investigator_target
        nr.investigator_target_role = (
            roles.get(investigator_target) if investigator_target else None
        )
        with langfuse.start_as_current_observation(
            as_type="span",
            name=f"night_resolution_day_{current_day}",
        ) as span:
            span.update(metadata=nr.model_dump())

    return {"investigator_results": investigator_update} if investigator_update else {}


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
def _vigilante_can_act(state: OrchestratorGraph) -> bool:
    return bool(state.get("vigilante_player")) and state.get("vigilante_bullets", 0) > 0


def _next_night_phase(state: OrchestratorGraph, after: str) -> str:
    order = [
        ("wolves", "WOLF_NIGHT_PHASE"),
        ("healer", "HEALER_NIGHT_PHASE"),
        ("serial_killer", "SERIAL_KILLER_NIGHT_PHASE"),
        ("vigilante", "VIGILANTE_NIGHT_PHASE"),
    ]
    present = {
        "healer": bool(state.get("healer_player")),
        "serial_killer": bool(state.get("serial_killer_player")),
        "vigilante": _vigilante_can_act(state),
    }
    start = next(i for i, (key, _) in enumerate(order) if key == after) + 1
    for key, node in order[start:]:
        if present.get(key):
            return node
    return "KILL_RESOLUTION"


def route_after_wolf_night(
    state: OrchestratorGraph,
) -> Literal[
    "HEALER_NIGHT_PHASE",
    "SERIAL_KILLER_NIGHT_PHASE",
    "VIGILANTE_NIGHT_PHASE",
    "KILL_RESOLUTION",
]:
    return _next_night_phase(state, "wolves")


def route_after_healer_night(
    state: OrchestratorGraph,
) -> Literal[
    "SERIAL_KILLER_NIGHT_PHASE",
    "VIGILANTE_NIGHT_PHASE",
    "KILL_RESOLUTION",
]:
    return _next_night_phase(state, "healer")


def route_after_serial_killer_night(
    state: OrchestratorGraph,
) -> Literal["VIGILANTE_NIGHT_PHASE", "KILL_RESOLUTION"]:
    return _next_night_phase(state, "serial_killer")


def route_after_kill_resolution(
    state: OrchestratorGraph,
) -> Literal["INVESTIGATOR_NIGHT_PHASE", "NIGHT_FINALIZE"]:
    # Skip the investigator if the game is already decided by the night's kills, or if the
    # investigator did not survive the night (its result would be moot either way).
    if determine_winner(state) is not None:
        return "NIGHT_FINALIZE"
    if state.get("investigator_player"):
        return "INVESTIGATOR_NIGHT_PHASE"
    return "NIGHT_FINALIZE"


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
