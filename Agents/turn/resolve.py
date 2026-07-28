"""Decision -> game-state update — the resolution BOTH player seats share.

An agent's LLM output and a human's interrupt response are shaped into the same decision object, and
``resolve_decision`` turns either into a validated state delta (a day/wolf message, a vote, a night target),
applying the pass / novelty-gate / target-validation rules uniformly. It is split out from the
agent-generation path (``agent_player.py``) and the human path (``human_turn.py``) so both import ONE
resolution — that shared path is exactly what keeps agent and human seats behaviourally identical
downstream of the decision.

``extract_agent_reasoning`` / ``_attach_agent_reasoning`` shape the strategy note (real state) and the
private eval carriers (``_``-prefixed, popped in pipeline.py before graph state) onto that delta.
"""

from logging import getLogger
from typing import Any

from pydantic import BaseModel

from Agents.schemas.game_events import AddressedTarget, DayChannel, DayVote, WolfChannel
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


def resolve_decision(result: BaseModel, reasoning: dict[str, Any], output_key: str,
                     payload: dict[str, Any], valid_targets: list[str]):
    """Resolve a player's decision into the partial state update LangGraph merges into game state.

    The decision object states an INTENT — "say this", "vote p2", "protect p3" — which may be
    illegal. Resolution applies the turn rules (pass handling, the proactive novelty gate, target
    validation) and returns what actually enters game state, keyed by ``output_key``'s channel:

    - day_channel:  ``{"day_channel": [DayChannel]}`` — the message, a pass entry, or a
      novelty-gated hidden pass
    - day_votes:    ``{"day_votes": [DayVote]}``
    - wolf_channel: ``{"wolf_channel": [WolfChannel]}`` — pack message + kill vote
    - night keys:   ``{"<output_key>": "<target>"}``

    plus whatever ``_attach_agent_reasoning`` adds (strategy note as real state; ``_``-prefixed
    private eval carriers, popped in pipeline.py before they can reach graph state).

    Returns None when the turn legitimately produces no update (a null-message day turn), or RETRY
    when the target is illegal — the agent caller re-generates, the human caller raises."""
    player_id = payload.get("player_id", "")

    if output_key == "day_channel":
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
                entry = DayChannel(day=current_day, seq=seq, player=player_id,
                                   message="", passed=True, firing_reason=firing_reason, gated=False)
                return _attach_agent_reasoning({"day_channel": [entry]}, reasoning, player_id, strategy_as_map=True)
            if payload.get("human_player"):
                discharges = [
                    AddressedTarget(target=creditor, addressed_form="response", stance="neutral")
                    for creditor in firing_reason.owes
                ]
                entry = DayChannel(day=current_day, seq=seq, player=player_id, message="",
                                   passed=True, addressed_targets=discharges,
                                   firing_reason=firing_reason, gated=False)
                return _attach_agent_reasoning({"day_channel": [entry]}, reasoning, player_id, strategy_as_map=True)

        message = result.message.strip() if result.message else None
        if not message or message.lower() == "null":
            return _attach_agent_reasoning({}, reasoning, player_id, strategy_as_map=True) or None

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
        return _attach_agent_reasoning({"day_channel": [entry]}, reasoning, player_id, strategy_as_map=True)

    if output_key == "day_votes":
        validated = validate_target(result.vote_target, valid_targets, player_id)
        if not validated:
            logger.warning(f"{player_id} voted for invalid target: {result.vote_target}")
            return RETRY
        return _attach_agent_reasoning({"day_votes": [DayVote(voter=player_id, votee=validated)]},
                                    reasoning, player_id, strategy_as_map=True)

    if output_key == "wolf_channel":
        # Sequential talk turn: message-only, no target to validate. vote="" keeps the
        # transcript formatter's no-vote rendering and stays out of the vote tally.
        output = {"wolf_channel": [WolfChannel(
            day=payload.get("current_day", 1), round=payload.get("current_round", 1),
            wolf=player_id, message=result.message, vote="",
        )]}
        return _attach_agent_reasoning(output, reasoning, player_id, strategy_as_map=True, include_reads=False)

    if output_key == "wolf_vote":
        # Parallel binding vote after the talk rounds: message-less, rides the wolf channel
        # so the tally (and the pack transcript) reads votes from the same place as ever.
        validated = validate_target(result.vote_target, valid_targets, player_id)
        if not validated:
            logger.warning(f"{player_id} voted for invalid target: {result.vote_target}")
            return RETRY
        output = {"wolf_channel": [WolfChannel(
            day=payload.get("current_day", 1), round=payload.get("current_round", 1),
            wolf=player_id, message="", vote=validated,
        )]}
        return _attach_agent_reasoning(output, reasoning, player_id, strategy_as_map=True, include_reads=False)

    if output_key in NIGHT_TARGET_KEYS:
        # vigilante "hold_fire" is a valid sentinel (bank the bullet); validate_target accepts it.
        target = getattr(result, output_key)
        validated = validate_target(target, valid_targets, player_id)
        if not validated:
            logger.warning(f"{player_id} chose an invalid {output_key}: {target}")
            return RETRY
        return _attach_agent_reasoning({output_key: validated}, reasoning, player_id, strategy_as_map=False)

    return None


def extract_agent_reasoning(result: BaseModel) -> dict[str, Any]:
    """The outputs an agent emits ALONGSIDE its action: its strategy note (real gameplay state) and
    the private eval carriers — its per-item strategy/memory verdicts and per-player reads. Anything
    on ``result`` not pulled out here is dropped."""
    return {
        "strategy": getattr(result, "updated_strategy", None),
        "strategy_verdicts": getattr(result, "strategy_verdicts", []) or [],
        "memory_verdicts": getattr(result, "memory_applicability", []) or [],
        "reads": getattr(result, "reads", []) or [],
    }


def _attach_agent_reasoning(
    output: dict[str, Any],
    reasoning: dict[str, Any],
    player_id: str,
    *,
    strategy_as_map: bool,
    include_reads: bool = True,
) -> dict[str, Any]:
    """Attach the agent reasoning to a state delta (every branch routes through here, so a new return
    can't forget one). The strategy note is real state: day/wolf write it as a {player_id: note} map
    (merge_strategies channel), night writes a bare ``updated_strategy``. The verdicts/reads are
    private eval CARRIERS — ``_``-prefixed, kept out of graph state downstream (_reads popped in
    pipeline.py, _strategy_verdicts popped in adoption.py, _memory_applicability dropped by the
    engine — LangGraph silently discards unknown keys in a node's return)."""
    if reasoning["strategy"]:
        if strategy_as_map:
            output["agent_strategies"] = {player_id: reasoning["strategy"]}
        else:
            output["updated_strategy"] = reasoning["strategy"]
    if reasoning["strategy_verdicts"]:
        output["_strategy_verdicts"] = reasoning["strategy_verdicts"]
    if reasoning["memory_verdicts"]:
        output["_memory_applicability"] = reasoning["memory_verdicts"]
    if include_reads and reasoning["reads"]:
        output["_reads"] = reasoning["reads"]
    return output
