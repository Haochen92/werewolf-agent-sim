"""Day-phase control flow: the rounds, scheduling speakers, fanning out votes, summarizing.

A day opens with a round (every survivor's opening at once: start_opening / fan_out_round /
collect_round), then on voting days the discussion — route_speaker is the scheduler hop that
fires the next speaker and the graph self-loops back through day_scheduler: whoever owes an
answer first, then the sweep gives the floor to the players who have not spoken, one at a time
(Agents/turn/scheduler.py) — then, when anyone has two accusers, the closing round
(start_closing), then the summary and the concurrent vote (fan_out_vote). Day 1 is the opening
and the summary only. route_after_discussion holds the day's branching after the discussion.
The per-role actor nodes these dispatch to (via Send) live in day/actors.py.
"""

from collections.abc import Iterable
from logging import getLogger as _getLogger
from typing import Literal

from langchain_core.runnables import RunnableConfig
from langgraph.config import get_stream_writer
from langgraph.graph import END
from langgraph.runtime import Runtime
from langgraph.types import Send

from Agents.game_config import GameConfig, game_config_from_runnable
from Agents.schemas import DayChannel, DayRound, DaySummary, FiringReason, RoundCandidate
from Agents.rules.closing import closing_announcement, closing_speakers
from Agents.rules.night_record import own_night_actions
from Agents.rules.seats import seat_order
from Agents.schemas.roles import ROLE_SPECS, WOLVES, cast_role_counts, side_of
from Agents.state import (
    DayGraphState,
)

from Agents.schemas import DaySummaryCase

from Agents.nodes.day.summary_agent import run_day_summary_agent
from Agents.observability import day_summary_span_name, freeze_case
from Agents.turn.action_space import valid_targets_for_action
from Agents.turn.human_turn import announce_human_turn
from Agents.turn.round_filter import filter_openings
from Agents.turn.scheduler import select_next_speaker

from Agents.tracing import (
    GraphContext,
    langfuse,
)

logger = _getLogger(__name__)


def day_scheduler(state: DayGraphState):
    """No-op hub node: the fixed return point every speaker self-loops back to, so
    route_speaker can re-run from one place until discussion terminates."""
    return {}


def route_speaker(
    state: DayGraphState, config: RunnableConfig
) -> Send | Literal["START_CLOSING", "SUMMARIZE_DAY_DISCUSSION"]:
    """The scheduler hop: the next speaker speaks, or the discussion is over.

    Recomputes from day_channel (the scheduler is stateless) and delegates to
    select_next_speaker: the player who owes an answer, else the sweep's next silent player.
    When neither is left (or the cap is reached) route_after_discussion decides what the day
    does next. Only voting days reach this hop: day 1 is the opening round alone
    (route_after_round).
    """
    game_config = game_config_from_runnable(config)
    current_day = state.get("current_day", 1)
    surviving_players = state["surviving_villagers"] + state["surviving_wolves"]
    current_day_discussion = [
        m for m in state.get("day_channel", [])
        if m.day == current_day and m.player != "game_master"
    ]

    route_decision = select_next_speaker(
        day_channel=current_day_discussion,
        surviving_players=surviving_players,
        game_config=game_config,
    )

    seq = len(current_day_discussion)
    if route_decision.terminate:
        logger.info(
            "[schedule] day=%d seq=%d terminate=%s", current_day, seq, route_decision.terminate_reason,
        )
        return route_after_discussion(state, config, route_decision.terminate_reason == "cap")

    fr = route_decision.firing_reason
    logger.info(
        "[schedule] day=%d seq=%d tier=%s sweep=%d speaker=%s owes=%s",
        current_day, seq, fr.tier, fr.sweep, route_decision.speaker, fr.owes,
    )
    role = state["roles"][route_decision.speaker]
    # turn_started for the "X is thinking" UI. Emitted from the edge, not the node: resume
    # after interrupt() re-runs the node but not this routing, so it can't double-fire.
    try:
        get_stream_writer()(
            {"event": "turn_started", "player": route_decision.speaker, "day": current_day}
        )
    except RuntimeError:  # direct call outside a graph run (tests)
        pass
    return build_speaker_send(state, route_decision.speaker, role, fr)


def route_after_discussion(
    state: DayGraphState, config: RunnableConfig, capped: bool
) -> Literal["START_CLOSING", "SUMMARIZE_DAY_DISCUSSION"]:
    """What the day does once the discussion is over (nobody owes an answer and the sweeps are
    done, or the cap was reached and drained): the closing defence when anyone has two
    accusers, else the summary. ``capped`` is kept for the trace; both ends lead here."""
    current_day = state["current_day"]
    surviving_players = state["surviving_villagers"] + state["surviving_wolves"]
    accused = closing_speakers(state.get("day_channel", []), current_day, surviving_players)
    if accused:
        return "START_CLOSING"
    return "SUMMARIZE_DAY_DISCUSSION"


def _initial_wolf_count(state: DayGraphState) -> int:
    """How many wolves the game was CAST with (from the true role map). Used only to fill the wolf
    day cell's deterministic `ally_revealed` — a scalar count, so no wolf identity rides the payload
    (the leak-boundary invariant is about names, not the count the wolf already knows)."""
    return sum(1 for r in state.get("roles", {}).values() if r in ROLE_SPECS and side_of(r) == WOLVES)


def _private_fields(state: DayGraphState, player: str, role: str) -> dict:
    """The private fields of one player's day payload, by role: the leak boundary. The pack's
    rosters and chat go to a wolf; every night actor gets its own record; a limited ability its
    uses left; the neutrals their pick or score."""
    spec = ROLE_SPECS[role]
    fields: dict = {}
    if spec.pack:
        fields["surviving_wolves"] = state["surviving_wolves"]
        fields["surviving_villagers"] = state["surviving_villagers"]
        # Wolves carry their own night coordination + GM notes into day discuss/vote (their own
        # information; gated to wolves only — see check_wolf_channel_isolation).
        fields["wolf_channel"] = state.get("wolf_channel", [])
        # Deterministic ally_revealed fill (situation_agent): how many wolves were cast, so a live
        # query can compute "a partner is gone" from surviving_wolves without trusting the LLM.
        fields["initial_wolf_count"] = _initial_wolf_count(state)
    if spec.night_action:
        # The speaker's own night record only (and the pack's kills, for a wolf).
        fields["night_actions"] = own_night_actions(state.get("night_actions", []), player, role)
    if spec.uses is not None:
        fields["uses_left"] = state.get("uses_left", {}).get(role, 0)
    if role == "vigilante":
        fields["vigilante_bullets"] = state.get("uses_left", {}).get(role, 0)
    if role == "speculator":
        fields["speculator_pick"] = state.get("speculator_pick") or "not yet"
    if role == "fortune_teller":
        fields["fortune_points"] = state.get("fortune_points", 0)
    return fields


def build_speaker_send(
    state: DayGraphState,
    speaker_id: str,
    role: str,
    firing_reason: FiringReason,
    *,
    voting_available: bool = True,
) -> Send:
    """Dispatch the discuss node for one speaker with a common payload + role-gated private fields.

    Private fields (wolf roster, investigator results, vigilante results) are only
    attached to the role they belong to, mirroring fan_out_day. They must NOT ride
    along in a universal superset: run_agent builds the prompt-input dict straight
    from this payload, so extra private keys reach every role's prompt input and are
    one template edit away from leaking (tests/leak_test.py guards this invariant).
    This replaces the old per-role fan-out branching.
    """
    surviving_players = seat_order(state["surviving_villagers"] + state["surviving_wolves"])
    payload = {
        "human_player": speaker_id in state["human_players"],
        "day_channel": state["day_channel"],
        "day_summaries": state.get("day_summaries", []),
        # Public dead roster — attached to EVERY role's payload (no leak gating; the dead
        # players' roles were announced publicly). Renders the who-died-and-as-what block.
        "dead_roster": state.get("dead_roster", []),
        # Public fixed-cast census (counts only, no identities) — feeds the alive-roles line
        # (cast minus revealed deaths). Same no-leak rationale as dead_roster.
        "cast_role_counts": cast_role_counts(state.get("roles", {})),
        "lineup": state.get("lineup", []),
        "surviving_players": surviving_players,
        "player_id": speaker_id,
        "player_role": role,
        "current_day": state["current_day"],
        "voting_available": voting_available,
        # A sweep turn is the open floor (the prompt's rules block and the human's ask follow
        # day_round); a reactive turn is the discussion. The opening and closing rounds are
        # fanned out by fan_out_day (Phase 2).
        "day_round": "proactive" if firing_reason.tier == "proactive" else "discussion",
        "previous_strategy": state.get("agent_strategies", {}).get(speaker_id, ""),
        "strategy_points": "",
        "firing_reason": firing_reason,
    }
    payload.update(_private_fields(state, speaker_id, role))
    return Send("discuss", payload)


def fan_out_day(
    state: DayGraphState,
    phase: Literal["discuss", "vote", "round_turn"],
    allow_abstain: bool = False,
    day_round: DayRound = "discussion",
    players: Iterable[str] | None = None,
):
    """Build a concurrent Send to the generic {phase} node for every surviving acting player.

    The shared fan-out used for voting and for the opening and closing rounds (discussion
    goes one speaker at a time via route_speaker). ``players`` narrows the fan-out to a
    subset of the survivors (the closing round's accused); None means everyone. Same
    role-gated private-field rule as build_speaker_send: wolf roster / investigator /
    vigilante results attach only to their own role.
    """
    concurrent_nodes = []
    surviving_players = seat_order(state["surviving_villagers"] + state["surviving_wolves"])
    chosen = None if players is None else set(players)
    strategies = state.get("agent_strategies", {})

    def base_payload(player: str, role: str, is_human: bool) -> dict:
        return {
            "human_player": is_human,
            "day_channel": state["day_channel"],
            "day_summaries": state.get("day_summaries", []),
            # Public dead roster on every role's payload (see build_speaker_send).
            "dead_roster": state.get("dead_roster", []),
            # Public fixed-cast census feeding the alive-roles line (see build_speaker_send).
            "cast_role_counts": cast_role_counts(state.get("roles", {})),
            "lineup": state.get("lineup", []),
            "surviving_players": surviving_players,
            "player_id": player,
            "player_role": role,
            "current_day": state["current_day"],
            "previous_strategy": strategies.get(player, ""),
            "strategy_points": "",
            "allow_abstain": allow_abstain,
            # Which round of the day this turn belongs to (opening / closing here); the prompt
            # picks its rules block by it. Votes carry it too, unused.
            "day_round": day_round,
        }

    for player in surviving_players:
        role = state["roles"][player]
        is_human = player in state["human_players"]
        if chosen is not None and player not in chosen:
            continue

        payload = base_payload(player, role, is_human)
        payload.update(_private_fields(state, player, role))

        # Humans go to the UNCACHED twin node: a human resume aborts and re-runs this
        # superstep, and the cached LLM nodes then replay their results instead of
        # re-billing; a cache wrapped around interrupt() crashes this langgraph version.
        concurrent_nodes.append(Send(f"{phase}_human" if is_human else phase, payload))

    return concurrent_nodes


def fan_out_vote(state: DayGraphState, config: RunnableConfig):
    """Router from START_VOTING: fan every survivor out to their vote node. Abstain is
    offered only while abstain is enabled and the no-lynch streak is under the force cap.
    A human's vote is announced here, so their ballot opens as the agents start voting
    rather than after the step ends (2026-10-06; see announce_human_turn)."""
    game_config = game_config_from_runnable(config)
    allow_abstain = (
        game_config.abstain_enabled
        and state.get("no_lynch_streak", 0) < game_config.no_lynch_force_after
    )
    sends = fan_out_day(state, "vote", allow_abstain)
    for send in sends:
        if send.node == "vote_human":
            announce_human_turn(send.arg["player_id"], send.arg["player_role"], "day_votes",
                                send.arg["current_day"],
                                valid_targets_for_action(send.arg, "day_votes"))
    return sends


# ---- The opening and closing rounds (Phase 2, discussion_evidence.md §7.2) -------------------
#
# A round sends several players their turn at once, on the vote's pattern: an entry node, a
# fan-out edge to the per-seat turn node (round_turn, with an uncached twin for a human), and a
# collecting node. The turns return their lines as round_candidates; collect_round orders and
# numbers them into day_channel, because parallel turns each count the same seq from the
# transcript they were given.


def _todays_entry_count(state: DayGraphState) -> int:
    """How many entries today's transcript already has: the next entry's seq."""
    current_day = state["current_day"]
    return sum(1 for entry in state.get("day_channel", []) if entry.day == current_day)


def start_opening(state: DayGraphState):
    """Entry node of the opening round: every living player gets a turn at once, their lines
    played in seat order."""
    surviving_players = state["surviving_villagers"] + state["surviving_wolves"]
    players = seat_order(surviving_players)
    return {"day_round": "opening", "round_players": players}


def start_closing(state: DayGraphState, config: RunnableConfig):
    """Entry node of the closing defence: the moderator names who is on trial and who is
    pressing, from the accusation tags alone (no model call), so the accused, the summary and
    the replay all see the same line. route_speaker only routes here when someone qualifies."""
    current_day = state["current_day"]
    surviving_players = state["surviving_villagers"] + state["surviving_wolves"]
    accused = closing_speakers(state.get("day_channel", []), current_day, surviving_players)
    if not accused:
        raise RuntimeError("start_closing ran with nobody accused by two players")

    announcement = DayChannel(
        day=current_day,
        seq=_todays_entry_count(state),
        player="game_master",
        message=closing_announcement(accused),
        day_round="closing",
    )
    players = []
    for trial in accused:
        players.append(trial.player)
    return {"day_round": "closing", "day_channel": [announcement], "round_players": players}


def fan_out_round(state: DayGraphState, config: RunnableConfig):
    """Router out of start_opening / start_closing: one round turn per player in the round, as
    the entry node listed them in round_players. A human's turn is announced here so the seat's
    prompt opens as the round starts (see announce_human_turn)."""
    day_round = state["day_round"]
    players = state["round_players"]
    sends = fan_out_day(state, "round_turn", day_round=day_round, players=players)
    for send in sends:
        if send.node == "round_turn_human":
            announce_human_turn(send.arg["player_id"], send.arg["player_role"], "day_channel",
                                send.arg["current_day"],
                                valid_targets_for_action(send.arg, "day_channel"),
                                day_round=day_round)
    return sends


def _round_order(state: DayGraphState) -> list[str]:
    """The order a round's lines are played in: the order the entry node listed the round's
    players (seat order for the opening, since nobody saw anyone else's line; the accused as
    they were called, most accused first, for the closing)."""
    return list(state["round_players"])


def collect_round(state: DayGraphState, config: RunnableConfig):
    """Barrier node after the round's turns: order the round's lines, run the opening's filter
    (humans exempt), number them, and write them into day_channel in sequence."""
    current_day = state["current_day"]
    day_round = state["day_round"]

    # Only this round's candidates: round_candidates accumulates all day, so the opening's are
    # still in it when the closing is collected.
    by_player: dict[str, DayChannel] = {}
    for candidate in state.get("round_candidates", []):
        same_round = candidate.day == current_day and candidate.day_round == day_round
        if same_round:
            by_player[candidate.entry.player] = candidate.entry
    if not by_player:
        return {}

    ordered: list[DayChannel] = []
    for player in _round_order(state):
        if player in by_player:
            ordered.append(by_player.pop(player))
    # Defensive: a candidate from a player the order did not name (should not happen) still lands.
    for player in seat_order(by_player):
        ordered.append(by_player[player])

    if day_round == "opening":
        ordered = _filter_keeping_humans(ordered, state, filter_openings)

    first_seq = _todays_entry_count(state)
    numbered: list[DayChannel] = []
    for offset, entry in enumerate(ordered):
        numbered.append(entry.model_copy(update={"seq": first_seq + offset}))
    return {"day_channel": numbered}


def _filter_keeping_humans(ordered: list[DayChannel], state: DayGraphState, round_filter) -> list[DayChannel]:
    """A round filter over the round's lines, with a human's line never held: the judge sees
    every line, but a verdict against a human's own line is undone."""
    filtered = round_filter(ordered)
    humans = set(state.get("human_players", []))
    restored: list[DayChannel] = []
    for before, after in zip(ordered, filtered):
        if before.player in humans and after.passed and not before.passed:
            restored.append(before)
        else:
            restored.append(after)
    return restored


def route_after_round(
    state: DayGraphState, config: RunnableConfig
) -> Literal["SCHEDULE", "SUMMARIZE_DAY_DISCUSSION"]:
    """Router after a round is collected. An opening on a voting day hands over to the
    scheduler for the discussion; an opening on day 1 (no vote, no discussion) and a closing
    (nobody replies) go straight to the summary."""
    game_config = game_config_from_runnable(config)
    if state["day_round"] == "opening" and state["current_day"] >= game_config.first_voting_day:
        return "SCHEDULE"
    return "SUMMARIZE_DAY_DISCUSSION"


def summarize_day_discussion(
    state: DayGraphState,
    config: RunnableConfig,
    runtime: Runtime[GraphContext],
    max_retries: int = 1,
):
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
    # game_id lives in config.configurable (pinned by build_runnable_config), not in
    # graph state — reading state here left the span name + case with an empty
    # game_id slot for every pre-2026-06-11 game (join those via trace_id).
    configurable = config.get("configurable", {}) if config else {}
    game_id = str(configurable.get("game_id") or "")
    span_name = day_summary_span_name(game_id, current_day)

    with langfuse.start_as_current_observation(
        as_type="span",
        name=span_name,
        input={"day": current_day, "raw_discussion": raw_discussion},
        metadata={"eval_schema": "day_summary_case_v1"},
    ) as summary_span:
        summary, model_used, structured = run_day_summary_agent(
            current_day, current_day_messages, max_retries,
            day_summaries=state.get("day_summaries", []),
            dead_roster=state.get("dead_roster", []),
            cast_role_counts=cast_role_counts(state.get("roles", {})),
            lineup=state.get("lineup", []),
            earlier_messages=[m for m in state.get("day_channel", []) if m.day < current_day],
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
            output={
                "day_summary_case": freeze_case(
                    summary_span,
                    day_summary_case,
                    kind="day_summary",
                    case_key="day_summary_case",
                    sink=runtime.context.get("eval_sink"),
                ),
            },
            metadata={
                "eval_schema": day_summary_case.schema_version,
                "day": current_day,
                "message_count": len(raw_discussion),
                "model_used": model_used,
            },
        )

    return {"day_summaries": [DaySummary(day=current_day, summary=summary, structured=structured)]}


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


