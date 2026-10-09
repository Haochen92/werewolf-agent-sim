from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime

from Agents.tracing import GraphContext

# Day actor nodes (thin wrappers over the shared runtime engine).
from Agents.turn import run_memory_informed_action
from Agents.turn.pipeline import preview_agent_action
from Agents.prompts.day_discuss import day_discuss_template
from Agents.prompts.day_vote import day_vote_template
from typing import TypedDict

from Agents.schemas import DayChannel, DayVote, RoundCandidate, day_discuss_output, day_vote_output
from Agents.schemas.game_events import DiscussionPassReason
from Agents.schemas.roles import roles
from Agents.schemas.turn import ResolvedDayDiscussion, ResolvedDayVote
from Agents.state import DayActorState

# The Send-payload shape, built by flow.py's builders (documentation-only — Send payloads are
# not runtime-validated; see state/day.py).
DayActorPayload = DayActorState


# The commit contracts: exactly what a turn's superstep can fold into graph state.
# Together with DayActorPayload these make the node signature the full turn contract:
# payload in, delta out — everything else in the call chain is implementation.
class DiscussDelta(TypedDict, total=False):
    day_channel: list[DayChannel]
    """One entry: the speech, or a pass marker (voluntary or novelty-gated)."""
    agent_strategies: dict[str, str]
    """{player_id: updated strategy note} — present only when the strategy changed."""


class RoundDelta(TypedDict, total=False):
    round_candidates: list[RoundCandidate]
    """One entry: this player's opening or closing line (or pass), held for collect_round."""
    agent_strategies: dict[str, str]
    """{player_id: updated strategy note} — present only when the strategy changed."""


class VoteDelta(TypedDict, total=False):
    day_votes: list[DayVote]
    """One vote (random-target fallback if every retry failed)."""
    agent_strategies: dict[str, str]
    """{player_id: updated strategy note} — present only when the strategy changed."""


# Every role's day-discuss / day-vote turn makes the identical call into the shared
# engine — only the prompt differs, and it is built once per role from the role's card.
# So the graph registers ONE generic node per phase and the role rides the Send payload
# (player_role, already attached by the payload builders in flow.py). The output schema
# depends on the dealt lineup (the roles a read or a claim may name), so it is looked up
# per payload.
DISCUSS_PROMPTS = {role: day_discuss_template(role) for role in roles}
VOTE_PROMPTS = {role: day_vote_template(role) for role in roles}


# The payload is the explicitly-built dict from build_speaker_send / fan_out_day (role-gated
# there — the leak boundary), not raw graph state.
def discuss(
    payload: DayActorPayload,
    config: RunnableConfig,
    runtime: Runtime[GraphContext],
) -> DiscussDelta | None:
    turn = run_memory_informed_action(
        payload,
        config,
        runtime,
        "day_discussion",
        DISCUSS_PROMPTS[payload["player_role"]],
        day_discuss_output(payload["lineup"]),
        "day_channel",
    )
    if turn is None:
        return None
    if not isinstance(turn, ResolvedDayDiscussion):
        raise TypeError(f"day discussion resolved to unexpected turn: {turn.kind}")

    updates: DiscussDelta = {}
    if turn.entry is not None:
        # DayGraphState.day_channel is an append-reduced list; this invocation contributes one entry.
        updates["day_channel"] = [turn.entry]
    if turn.effects.strategy:
        updates["agent_strategies"] = {
            payload["player_id"]: turn.effects.strategy,
        }
    return updates or None


def round_turn(
    payload: DayActorPayload,
    config: RunnableConfig,
    runtime: Runtime[GraphContext],
) -> RoundDelta | None:
    """An opening or closing turn: the same engine call as ``discuss`` (the prompt picks its
    rules block from the payload's ``day_round``), but the line goes to ``round_candidates``
    instead of ``day_channel``, because the round's turns run in parallel and only
    ``collect_round`` may number them into the transcript."""
    turn = run_memory_informed_action(
        payload,
        config,
        runtime,
        "day_discussion",
        DISCUSS_PROMPTS[payload["player_role"]],
        day_discuss_output(payload["lineup"]),
        "day_channel",
    )
    if turn is None:
        return None
    if not isinstance(turn, ResolvedDayDiscussion):
        raise TypeError(f"round turn resolved to unexpected turn: {turn.kind}")

    updates: RoundDelta = {}
    if turn.entry is not None:
        updates["round_candidates"] = [
            RoundCandidate(day=payload["current_day"], day_round=payload["day_round"],
                           entry=turn.entry)
        ]
    if turn.effects.strategy:
        updates["agent_strategies"] = {
            payload["player_id"]: turn.effects.strategy,
        }
    return updates or None


def preview_discuss(
    payload: DayActorPayload,
    config: RunnableConfig,
    runtime: Runtime[GraphContext],
    direction: str = "",
) -> str:
    """What this seat's agent would say on the discussion turn in ``payload``, said nowhere.

    The same agent, prompt and context as ``discuss`` when the seat's human hands the turn
    over (see ``preview_agent_action``), but nothing is committed: no line, no strategy note.
    ``direction`` is the human's steer, sent after the prompt; empty = the prompt as is.
    Returns the line, or "" when the agent would pass. RuntimeError when every attempt failed.
    """
    turn = preview_agent_action(
        payload,
        config,
        runtime,
        "day_discussion",
        DISCUSS_PROMPTS[payload["player_role"]],
        day_discuss_output(payload["lineup"]),
        "day_channel",
        direction,
    )
    entry = turn.entry if isinstance(turn, ResolvedDayDiscussion) else None
    if entry is not None and entry.pass_reason == DiscussionPassReason.GENERATION_FAILED:
        raise RuntimeError("the agent produced no line")
    return entry.message if entry is not None else ""


def vote(
    payload: DayActorPayload,
    config: RunnableConfig,
    runtime: Runtime[GraphContext],
) -> VoteDelta | None:
    turn = run_memory_informed_action(
        payload,
        config,
        runtime,
        "day_vote",
        VOTE_PROMPTS[payload["player_role"]],
        day_vote_output(payload["lineup"]),
        "day_votes",
    )
    if turn is None:
        return None
    if not isinstance(turn, ResolvedDayVote):
        raise TypeError(f"day vote resolved to unexpected turn: {turn.kind}")

    updates: VoteDelta = {
        # Parallel voter invocations each contribute one item to the add-reduced vote channel.
        "day_votes": [turn.entry],
    }
    if turn.effects.strategy:
        updates["agent_strategies"] = {
            payload["player_id"]: turn.effects.strategy,
        }
    return updates
