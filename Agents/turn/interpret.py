"""Decision -> legal state delta — the interpretation BOTH player seats share.

An agent's LLM output and a human's interrupt response are shaped into the same decision object, and
``_interpret`` turns either into a validated state delta (a day/wolf message, a vote, a night target),
applying the pass / novelty-gate / target-validation rules uniformly. It is split out from the
agent-generation path (``agent_player.py``) and the human path (``human_turn.py``) so both import ONE
interpretation — that shared path is exactly what keeps agent and human seats behaviourally identical
downstream of the decision.

``_extract_side_outputs`` / ``_attach_side_outputs`` shape the strategy note (real state) and the
private eval carriers (``_``-prefixed, popped in pipeline.py before graph state) onto that delta.
"""

from logging import getLogger
from typing import Any

from pydantic import BaseModel

from Agents.schemas.game_events import DayChannel, DayVote, WolfChannel
from Agents.turn.action_space import _validate_target
from Agents.turn.novelty_agent import judge_proactive_novelty

logger = getLogger(__name__)

# _interpret sentinel: the decision was rejected (invalid target) — re-generate.
_RETRY = object()
NIGHT_TARGET_KEYS = (
    "healer_target",
    "investigator_target",
    "serial_killer_target",
    "vigilante_target",
)


def _interpret(result: BaseModel, side_outputs: dict[str, Any], output_key: str,
               payload: dict[str, Any], valid_targets: list[str]):
    """A decision -> a legal state delta. Returns the delta (dict), None (valid but no delta — a
    null-message day turn), or _RETRY (invalid target — re-generate)."""
    player_id = payload.get("player_id", "")

    if output_key == "day_channel":
        current_day = payload.get("current_day", 1)
        firing_reason = payload.get("firing_reason")  # scheduler trace; rides the Send
        seq = sum(1 for m in payload.get("day_channel", []) if m.day == current_day)

        # Reactive picks must answer (a pass wouldn't discharge the obligation) — honor a pass only
        # when not reactive.
        is_reactive = firing_reason is not None and firing_reason.tier == "reactive"
        if getattr(result, "pass_turn", False) and not is_reactive:
            entry = DayChannel(day=current_day, seq=seq, player=player_id,
                               message="", passed=True, firing_reason=firing_reason, gated=False)
            return _attach_side_outputs({"day_channel": [entry]}, side_outputs, player_id, strategy_as_map=True)

        message = result.message.strip() if result.message else None
        if not message or message.lower() == "null":
            return _attach_side_outputs({}, side_outputs, player_id, strategy_as_map=True) or None

        # Proactive novelty gate: an echo/restatement proactive turn becomes a hidden pass. Reactive
        # turns are never gated; the day's first opener_floor real utterances bypass the gate so every
        # day opens substantively before echo-gating engages. A human seat is never gated — we don't
        # silence a person's message as an "echo".
        is_proactive = firing_reason is not None and firing_reason.tier == "proactive"
        today_real = sum(
            1 for m in payload.get("day_channel", [])
            if m.day == current_day and m.player != "game_master" and not getattr(m, "passed", False)
        )
        if (is_proactive and today_real >= payload.get("opener_floor", 0)
                and not payload.get("human_player")
                and not judge_proactive_novelty(message, payload, current_day)):
            # Gated silence: substantive enough to write but judged an echo. gated_candidate is kept
            # for a selectivity audit and MUST stay out of every agent prompt (DayChannel leak note).
            entry = DayChannel(day=current_day, seq=seq, player=player_id, message="", passed=True,
                               firing_reason=firing_reason, gated=True, gated_candidate=message)
        else:
            entry = DayChannel(day=current_day, seq=seq, player=player_id, message=message,
                               addressed_targets=getattr(result, "addressed_targets", []),
                               firing_reason=firing_reason)
        return _attach_side_outputs({"day_channel": [entry]}, side_outputs, player_id, strategy_as_map=True)

    if output_key == "day_votes":
        validated = _validate_target(result.vote_target, valid_targets, player_id)
        if not validated:
            logger.warning(f"{player_id} voted for invalid target: {result.vote_target}")
            return _RETRY
        return _attach_side_outputs({"day_votes": [DayVote(voter=player_id, votee=validated)]},
                                    side_outputs, player_id, strategy_as_map=True)

    if output_key == "wolf_channel":
        validated = _validate_target(result.vote_target, valid_targets, player_id)
        if not validated:
            logger.warning(f"{player_id} voted for invalid target: {result.vote_target}")
            return _RETRY
        output = {"wolf_channel": [WolfChannel(
            day=payload.get("current_day", 1), round=payload.get("current_round", 1),
            wolf=player_id, message=result.message, vote=validated,
        )]}
        return _attach_side_outputs(output, side_outputs, player_id, strategy_as_map=True, include_reads=False)

    if output_key in NIGHT_TARGET_KEYS:
        # vigilante "hold_fire" is a valid sentinel (bank the bullet); _validate_target accepts it.
        target = getattr(result, output_key)
        validated = _validate_target(target, valid_targets, player_id)
        if not validated:
            logger.warning(f"{player_id} chose an invalid {output_key}: {target}")
            return _RETRY
        return _attach_side_outputs({output_key: validated}, side_outputs, player_id, strategy_as_map=False)

    return None


def _extract_side_outputs(result: BaseModel) -> dict[str, Any]:
    """The outputs an agent emits ALONGSIDE its action: its strategy note (real gameplay state) and
    the private eval carriers — its per-item strategy/memory verdicts and per-player reads. Anything
    on ``result`` not pulled out here is dropped."""
    return {
        "strategy": getattr(result, "updated_strategy", None),
        "strategy_verdicts": getattr(result, "strategy_verdicts", []) or [],
        "memory_verdicts": getattr(result, "memory_applicability", []) or [],
        "reads": getattr(result, "reads", []) or [],
    }


def _attach_side_outputs(
    output: dict[str, Any],
    side_outputs: dict[str, Any],
    player_id: str,
    *,
    strategy_as_map: bool,
    include_reads: bool = True,
) -> dict[str, Any]:
    """Attach the side outputs to a state delta (every branch routes through here, so a new return
    can't forget one). The strategy note is real state: day/wolf write it as a {player_id: note} map
    (merge_strategies channel), night writes a bare ``updated_strategy``. The verdicts/reads are
    private eval CARRIERS — ``_``-prefixed, POPped downstream (pipeline.py) before graph state."""
    if side_outputs["strategy"]:
        if strategy_as_map:
            output["agent_strategies"] = {player_id: side_outputs["strategy"]}
        else:
            output["updated_strategy"] = side_outputs["strategy"]
    if side_outputs["strategy_verdicts"]:
        output["_strategy_verdicts"] = side_outputs["strategy_verdicts"]
    if side_outputs["memory_verdicts"]:
        output["_memory_applicability"] = side_outputs["memory_verdicts"]
    if include_reads and side_outputs["reads"]:
        output["_reads"] = side_outputs["reads"]
    return output
