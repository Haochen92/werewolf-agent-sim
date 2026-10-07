from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime

from Agents.tracing import GraphContext

# Day actor nodes (thin wrappers over the shared runtime engine).
from Agents.turn import run_memory_informed_action
from Agents.turn.pipeline import preview_agent_action
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
from typing import TypedDict

from Agents.schemas import DayChannel, DayDiscussOutput, DayVote, DayVoteOutput, RoundCandidate
from Agents.schemas.game_events import DiscussionPassReason
from Agents.schemas.turn import ResolvedDayDiscussion, ResolvedDayVote
from Agents.state import HealerDayState, InvestigatorDayState, VillagerDayState, WolfDayState

# The Send-payload shape: one of the role-gated payload TypedDicts built by flow.py's
# builders (documentation-only — Send payloads are not runtime-validated; see state/day.py).
DayActorPayload = VillagerDayState | HealerDayState | WolfDayState | InvestigatorDayState


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
# engine — only the prompt differs. So the graph registers ONE generic node per phase
# and the role rides the Send payload (player_role, already attached by the role-gated
# payload builders in flow.py). Role-specific behaviour is data (the prompt tables),
# not code: adding a role = one prompt entry per phase.
DISCUSS_PROMPTS: dict[str, str] = {
    "villager": VILLAGER_DAY_DISCUSS,
    "healer": HEALER_DAY_DISCUSS,
    "wolf": WOLF_DAY_DISCUSS,
    "investigator": INVESTIGATOR_DAY_DISCUSS,
    "serial_killer": SERIAL_KILLER_DAY_DISCUSS,
    "vigilante": VIGILANTE_DAY_DISCUSS,
}

VOTE_PROMPTS: dict[str, str] = {
    "villager": VILLAGER_DAY_VOTE,
    "healer": HEALER_DAY_VOTE,
    "wolf": WOLF_DAY_VOTE,
    "investigator": INVESTIGATOR_DAY_VOTE,
    "serial_killer": SERIAL_KILLER_DAY_VOTE,
    "vigilante": VIGILANTE_DAY_VOTE,
}


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
        DayDiscussOutput,
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
        DayDiscussOutput,
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
                           round_no=payload.get("round_no", 0), entry=turn.entry)
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
        DayDiscussOutput,
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
        DayVoteOutput,
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
