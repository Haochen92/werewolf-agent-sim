"""Decision -> resolved domain action — the resolution BOTH player seats share.

An agent's LLM output and a human's interrupt response are shaped into the same decision object.
``resolve_decision`` applies the game rules and returns a typed resolved turn. It deliberately does
not know graph channel names or reducer shapes: registered actor nodes own the final
resolved-turn -> graph-delta conversion.
"""

from logging import getLogger
from typing import Any

from pydantic import BaseModel

from Agents.schemas.game_events import (
    AddressedTarget,
    DayChannel,
    DayVote,
    DiscussionPassReason,
    WolfChannel,
)
from Agents.schemas.turn import (
    ResolvedDayDiscussion,
    ResolvedDayVote,
    ResolvedHealerTarget,
    ResolvedInvestigatorTarget,
    ResolvedSerialKillerTarget,
    ResolvedVigilanteTarget,
    ResolvedWolfDiscussion,
    ResolvedWolfVote,
    TurnEffects,
)
from Agents.turn.action_space import validate_target
from Agents.turn.novelty_agent import judge_proactive_novelty

logger = getLogger(__name__)

# resolve_decision sentinel: the decision was rejected (invalid target) — re-generate.
RETRY = object()
NIGHT_TARGET_KEYS = (
    "healer_target",
    "investigator_target",
    "serial_killer_target",
    "vigilante_target",
)


def resolve_decision(
    result: BaseModel,
    reasoning: dict[str, Any],
    output_key: str,
    payload: dict[str, Any],
    valid_targets: list[str],
):
    """Resolve a player's decision into a legal, typed domain action.

    The decision states an intent — speak, vote, or target a player. Resolution applies pass
    handling, the proactive novelty gate, and target validation, then returns a ``Resolved*`` turn.
    Returns RETRY when a target is illegal; the agent caller regenerates and the human caller raises.
    """
    player_id = payload.get("player_id", "")

    if output_key == "day_channel":
        effects = _turn_effects(reasoning)
        current_day = payload.get("current_day", 1)
        firing_reason = payload.get("firing_reason")  # scheduler trace; rides the Send
        seq = sum(1 for m in payload.get("day_channel", []) if m.day == current_day)

        # Reactive picks must answer — an agent's bare pass wouldn't discharge the obligation, so
        # it falls through to message handling. The human seat MAY decline (a mention isn't a
        # demand): its pass entry carries synthetic neutral responses to everyone owed, closing
        # the ledger debts so the scheduler doesn't re-fire the same turn forever.
        is_reactive = firing_reason is not None and firing_reason.tier == "reactive"
        if getattr(result, "pass_turn", False):
            if not is_reactive:
                entry = DayChannel(
                    day=current_day,
                    seq=seq,
                    player=player_id,
                    message="",
                    passed=True,
                    pass_reason=DiscussionPassReason.VOLUNTARY,
                    firing_reason=firing_reason,
                    gated=False,
                )
                return ResolvedDayDiscussion(entry=entry, effects=effects)
            if payload.get("human_player"):
                discharges = [
                    AddressedTarget(
                        target=creditor,
                        addressed_form="response",
                        stance="neutral",
                    )
                    for creditor in firing_reason.owes
                ]
                entry = DayChannel(
                    day=current_day,
                    seq=seq,
                    player=player_id,
                    message="",
                    passed=True,
                    pass_reason=DiscussionPassReason.VOLUNTARY,
                    addressed_targets=discharges,
                    firing_reason=firing_reason,
                    gated=False,
                )
                return ResolvedDayDiscussion(entry=entry, effects=effects)

        message = result.message.strip() if result.message else None
        if not message or message.lower() == "null":
            return ResolvedDayDiscussion(entry=None, effects=effects)

        # Proactive novelty gate: an echo/restatement proactive turn becomes a hidden pass. Reactive
        # turns are never gated; the day's first opener_floor real utterances bypass the gate so every
        # day opens substantively before echo-gating engages. A human seat is never gated.
        is_proactive = firing_reason is not None and firing_reason.tier == "proactive"
        today_real = sum(
            1
            for m in payload.get("day_channel", [])
            if m.day == current_day
            and m.player != "game_master"
            and not getattr(m, "passed", False)
        )
        if (
            is_proactive
            and today_real >= payload.get("opener_floor", 0)
            and not payload.get("human_player")
            and not judge_proactive_novelty(message, payload, current_day)
        ):
            # gated_candidate is persisted for selectivity audits but hidden by prompt formatters.
            entry = DayChannel(
                day=current_day,
                seq=seq,
                player=player_id,
                message="",
                passed=True,
                pass_reason=DiscussionPassReason.NOVELTY_GATED,
                firing_reason=firing_reason,
                gated=True,
                gated_candidate=message,
            )
        else:
            entry = DayChannel(
                day=current_day,
                seq=seq,
                player=player_id,
                message=message,
                addressed_targets=getattr(result, "addressed_targets", []),
                firing_reason=firing_reason,
            )
        return ResolvedDayDiscussion(entry=entry, effects=effects)

    if output_key == "day_votes":
        validated = validate_target(result.vote_target, valid_targets, player_id)
        if not validated:
            logger.warning(f"{player_id} voted for invalid target: {result.vote_target}")
            return RETRY
        return ResolvedDayVote(
            entry=DayVote(voter=player_id, votee=validated),
            effects=_turn_effects(reasoning),
        )

    if output_key == "wolf_channel":
        # Sequential talk turn: message-only, no target to validate.
        return ResolvedWolfDiscussion(
            entry=WolfChannel(
                day=payload.get("current_day", 1),
                round=payload.get("current_round", 1),
                wolf=player_id,
                message=result.message,
                vote="",
            ),
            effects=_turn_effects(reasoning, include_reads=False),
        )

    if output_key == "wolf_vote":
        validated = validate_target(result.vote_target, valid_targets, player_id)
        if not validated:
            logger.warning(f"{player_id} voted for invalid target: {result.vote_target}")
            return RETRY
        return ResolvedWolfVote(
            entry=WolfChannel(
                day=payload.get("current_day", 1),
                round=payload.get("current_round", 1),
                wolf=player_id,
                message="",
                vote=validated,
            ),
            effects=_turn_effects(reasoning, include_reads=False),
        )

    if output_key in NIGHT_TARGET_KEYS:
        target = getattr(result, output_key)
        validated = validate_target(target, valid_targets, player_id)
        if not validated:
            logger.warning(f"{player_id} chose invalid {output_key}: {target}")
            return RETRY
        result_type = _NIGHT_RESULT_BY_KEY[output_key]
        return result_type(entry=validated, effects=_turn_effects(reasoning))

    return None


def extract_agent_reasoning(result: BaseModel) -> dict[str, Any]:
    """Extract the non-action outputs emitted alongside a model decision."""
    return {
        "strategy": getattr(result, "updated_strategy", None),
        "strategy_verdicts": getattr(result, "strategy_verdicts", []) or [],
        "memory_verdicts": getattr(result, "memory_applicability", []) or [],
        "reads": getattr(result, "reads", []) or [],
    }


def _turn_effects(
    reasoning: dict[str, Any],
    *,
    include_reads: bool = True,
) -> TurnEffects:
    """Convert model-side reasoning into typed non-action effects.

    These values never share a dictionary with graph state, so private reads and verdicts cannot
    reach a state channel through an unknown-key filtering convention.
    """
    return TurnEffects(
        strategy=reasoning["strategy"] or None,
        strategy_verdicts=reasoning["strategy_verdicts"],
        memory_verdicts=reasoning["memory_verdicts"],
        reads=reasoning["reads"] if include_reads else [],
    )


_NIGHT_RESULT_BY_KEY = {
    "healer_target": ResolvedHealerTarget,
    "investigator_target": ResolvedInvestigatorTarget,
    "serial_killer_target": ResolvedSerialKillerTarget,
    "vigilante_target": ResolvedVigilanteTarget,
}
