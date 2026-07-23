"""The agent decision runner — the single chokepoint every agent decision routes through.

``_run_agent`` turns "it's this agent's turn to decide X" into a legal, game-ready action: it
constrains the answer space, GENERATEs a decision (one LLM call, retried), and INTERPRETs it into a
validated state delta, falling back to a random legal move so the game never stalls. The
generate/interpret seam is where a human seat branches in — ``interrupt()`` for the decision instead
of ``_generate``, then the same ``_interpret`` path.

This file holds only the input->output decision path. The turn's instrumentation — the leak-test
prompt/reads logs and the reads-completeness monitor — lives in ``eval.py``; ``_run_agent`` calls
``_log_prompt`` / ``_record_reads`` as side channels that never touch the returned delta.
"""
from logging import getLogger
from typing import Any
import random

from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel

from Agents.llm_factory import get_llm
from Agents.prompts.prompt_inputs import build_agent_prompt_input as _build_agent_prompt_input
from Agents.schemas.game_events import DayChannel, DayVote, WolfChannel
from Agents.turn.eval import _log_prompt, _record_reads
from Agents.turn.novelty_agent import judge_proactive_novelty
from Agents.turn.action_space import (
    _valid_targets_for_action,
    _validate_target,
    _output_schema_with_legal_targets,
)

load_dotenv()
logger = getLogger(__name__)

# _interpret sentinel: the decision was rejected (invalid target) — re-generate.
_RETRY = object()
NIGHT_TARGET_KEYS = (
    "healer_target",
    "investigator_target",
    "serial_killer_target",
    "vigilante_target",
)


def _run_agent(
    payload: dict[str, Any],
    prompt_template: ChatPromptTemplate,
    output_schema: type[BaseModel],
    output_key: str,
    max_retries: int = 1,
) -> dict[str, Any] | None:
    """Run one agent decision: constrain -> generate -> interpret, retrying on an LLM error or a
    rejected (invalid-target) decision, with a random legal fallback if every attempt fails.

    A human seat branches in here: ``interrupt()`` for the decision instead of ``_generate``, then
    the same ``_interpret`` path. Insert before the chain is built — the human gets no LLM prompt.
    """
    valid_targets = _valid_targets_for_action(payload, output_key)
    player_id = payload.get("player_id", "")

    # Constrain: bind the model to the legal-targets schema; build + log the prompt once.
    schema = _output_schema_with_legal_targets(output_schema, output_key, valid_targets)
    chain = prompt_template | get_llm().with_structured_output(schema)
    prompt_input = _build_agent_prompt_input(payload)
    _log_prompt(payload, output_key, prompt_input)

    for _ in range(max_retries + 1):
        result = _generate(chain, prompt_input, output_key, player_id)
        if result is None:
            continue
        side_outputs = _extract_side_outputs(result)
        _record_reads(side_outputs["reads"], payload, output_key, output_schema)
        outcome = _interpret(result, side_outputs, output_key, payload, valid_targets)
        if outcome is not _RETRY:
            return outcome

    # Exhausted: random legal fallback so the game progresses (day discussion may skip -> None).
    logger.error(f"{player_id} failed all retries on {output_key}, using random fallback")
    if output_key == "day_votes":
        return {"day_votes": [DayVote(voter=player_id, votee=random.choice(valid_targets))]}
    if output_key in NIGHT_TARGET_KEYS:
        return {output_key: random.choice(valid_targets)}
    if output_key == "wolf_channel":
        return {"wolf_channel": [WolfChannel(
            day=payload.get("current_day", 1), round=payload.get("current_round", 1),
            wolf=player_id, message="...", vote=random.choice(valid_targets),
        )]}
    return None


def _generate(chain: Any, prompt_input: dict, output_key: str, player_id: str):
    """One structured LLM call. Returns the parsed decision, or None on an API/parse error."""
    try:
        return chain.invoke(prompt_input, config={"run_name": f"{output_key}_{player_id}"})
    except Exception as e:
        logger.warning(f"LLM call failed for {player_id}: {e}")
        return None


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
        # day opens substantively before echo-gating engages.
        is_proactive = firing_reason is not None and firing_reason.tier == "proactive"
        today_real = sum(
            1 for m in payload.get("day_channel", [])
            if m.day == current_day and m.player != "game_master" and not getattr(m, "passed", False)
        )
        if (is_proactive and today_real >= payload.get("opener_floor", 0)
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
