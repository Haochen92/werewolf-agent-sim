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
from Agents.turn.echo_gate import line_echo_of

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
    handling, the sweep turns' echo gate, and target validation, then returns a ``Resolved*`` turn.
    Returns RETRY when a target is illegal; the agent caller regenerates and the human caller raises.
    """
    player_id = payload.get("player_id", "")

    if output_key == "day_channel":
        effects = _turn_effects(reasoning)
        current_day = payload.get("current_day", 1)
        firing_reason = payload.get("firing_reason")  # scheduler trace; rides the Send
        seq = sum(1 for m in payload.get("day_channel", []) if m.day == current_day)
        day_round = payload.get("day_round", "discussion")  # which round of the day this turn is

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
                    day_round=day_round,
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
                    day_round=day_round,
                    message="",
                    passed=True,
                    pass_reason=DiscussionPassReason.VOLUNTARY,
                    addressed_targets=discharges,
                    firing_reason=firing_reason,
                    gated=False,
                )
                return ResolvedDayDiscussion(entry=entry, effects=effects)

        is_proactive = firing_reason is not None and firing_reason.tier == "proactive"
        message = result.message.strip() if result.message else None
        if not message or message.lower() == "null":
            if is_proactive:
                # A sweep turn that came back empty is recorded as a pass, or the stateless
                # scheduler would give the same player the floor again at once.
                entry = DayChannel(
                    day=current_day,
                    seq=seq,
                    player=player_id,
                    day_round=day_round,
                    message="",
                    passed=True,
                    pass_reason=DiscussionPassReason.VOLUNTARY,
                    firing_reason=firing_reason,
                    gated=False,
                )
                return ResolvedDayDiscussion(entry=entry, effects=effects)
            return ResolvedDayDiscussion(entry=None, effects=effects)

        addressed_targets = getattr(result, "addressed_targets", [])

        # The echo gate: a sweep turn that makes a point already made today is held, not
        # published. Reactive turns are never gated (the answer is owed), nor is a human seat,
        # nor a player answering someone who named them (the ruling that a player confirming or
        # denying what was said about themselves is never a duplicate, decided from the tags, so
        # it holds even when the judge misses it; seen 2026-10-07, a mention tagged neutral left
        # the named player no reactive turn and the gate then held their denial).
        # The held marker keeps the text for its author; its tags stay for records only.
        if is_proactive and not payload.get("human_player"):
            earlier_today = [m for m in payload.get("day_channel", []) if m.day == current_day]
            if _answers_someone_who_named_me(addressed_targets, player_id, earlier_today):
                echo_of = ""
            else:
                echo_of = line_echo_of(message, player_id, earlier_today)
            if echo_of:
                logger.info("[echo gate] day=%d %s held: same point as %s", current_day, player_id, echo_of)
                entry = DayChannel(
                    day=current_day,
                    seq=seq,
                    player=player_id,
                    day_round=day_round,
                    message="",
                    addressed_targets=addressed_targets,
                    passed=True,
                    pass_reason=DiscussionPassReason.NOVELTY_GATED,
                    firing_reason=firing_reason,
                    gated=True,
                    gated_candidate=message,
                )
                return ResolvedDayDiscussion(entry=entry, effects=effects)

        entry = DayChannel(
            day=current_day,
            seq=seq,
            player=player_id,
            day_round=day_round,
            message=message,
            addressed_targets=addressed_targets,
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


def _answers_someone_who_named_me(
    addressed_targets: list[AddressedTarget], player_id: str, earlier_today: list[DayChannel]
) -> bool:
    """Whether the line is tagged as a response to a player whose earlier spoken line today
    named the speaker: the speaker is answering something said about them."""
    named_me: set[str] = set()
    for entry in earlier_today:
        if entry.passed or entry.player == "game_master":
            continue
        for tag in entry.addressed_targets:
            if tag.target == player_id:
                named_me.add(entry.player)
    for tag in addressed_targets:
        if tag.addressed_form == "response" and tag.target in named_me:
            return True
    return False


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
