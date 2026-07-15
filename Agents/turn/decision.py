"""The decision-LLM runner — the single chokepoint every agent decision call routes through.

``_run_agent`` builds the prompt, enforces the dynamic target enum, invokes the model (with retry and
pass handling), and returns the structured decision. ``prompt_log`` is the leak-test capture point:
every prompt sent to the model is appended here so the boundary tests can assert no private state
leaked into an agent's context.
"""
from logging import getLogger
from typing import Any
import random

from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel

from Agents.llm_factory import get_llm


from Agents.prompts.prompt_inputs import build_agent_prompt_input as _build_agent_prompt_input
from Agents.schemas.game_events import (
    DayChannel,
    DayVote,
    WolfChannel,
)
from Agents.turn.novelty_agent import judge_proactive_novelty
from Agents.turn.action_space import (
    _valid_targets_for_action,
    _validate_target,
    _with_dynamic_target_enum,
)

load_dotenv()
logger = getLogger(__name__)
prompt_log: list[dict] = []
# Capture point for the reads leak check (see tests/leak_test.py): every emitted read is recorded
# here so check_reads_isolation can scan every OTHER agent's prompt_input for its why-text. Cleared
# at game start alongside prompt_log (Agents/main.py).
reads_log: list[dict] = []


def _reads_coverage(reads: list, payload: dict[str, Any]) -> tuple[float, list[str]]:
    """Fraction of the enumerated read targets the agent actually covered, plus the missing players.

    Expected targets are enumerated EXACTLY as build_agent_prompt_input builds {read_targets}
    (surviving_players, or the wolf-day wolves+villagers shape, minus self), so the tripwire measures
    against what the prompt asked for. Pure/side-effect-free so the completeness policy is unit-testable
    on its own; the caller only MONITORS on it (T4: enumerate + warn, never retry)."""
    expected = payload.get("surviving_players") or (
        payload.get("surviving_wolves", []) + payload.get("surviving_villagers", [])
    )
    self_id = payload.get("player_id")
    expected = [p for p in expected if p != self_id]
    if not expected:
        return 1.0, []
    covered = {getattr(r, "player", None) for r in reads}
    missing = [p for p in expected if p not in covered]
    coverage = (len(expected) - len(missing)) / len(expected)
    return coverage, missing


def _run_agent(
    payload: dict[str, Any],
    prompt_template: ChatPromptTemplate,
    output_schema: type[BaseModel],
    output_key: str,
    max_retries: int = 1
) -> dict[str, Any] | None:
    valid_targets = _valid_targets_for_action(payload, output_key)
    effective_output_schema = _with_dynamic_target_enum(
        output_schema,
        output_key,
        valid_targets,
    )
    chain = prompt_template | get_llm().with_structured_output(effective_output_schema)
    prompt_input = _build_agent_prompt_input(payload)

    player_id = payload.get("player_id", "")
    prompt_log.append(
        {
            "player_id": player_id,
            "player_role": payload.get("player_role", ""),
            "output_key": output_key,
            "day": payload.get("current_day", 1),
            "round": payload.get("current_round", 1),
            "prompt_input": prompt_input.copy(),
        }
    )

    for attempt in range(max_retries + 1):
        try:
            result = chain.invoke(
                prompt_input,
                config={"run_name": f"{output_key}_{player_id}"},
            )
        except Exception as e:
            logger.warning(f"LLM call failed for {player_id}: {e}")
            if attempt < max_retries:
                continue
            break

        # Extract strategy note + the two per-item verdict lists (strategy points / observations) if
        # present on the result. The _strategy_verdicts and _memory_applicability carriers ride the
        # curated output — _run_agent drops everything off `result` that isn't explicitly carried, and
        # actions.py reads these carriers into the EvalCase (and adoption.py applies the SP verdicts).
        strategy_update = getattr(result, "updated_strategy", None)
        strategy_verdicts = getattr(result, "strategy_verdicts", []) or []
        memory_verdicts = getattr(result, "memory_applicability", []) or []
        # Per-player reads (T1c). The _reads carrier rides the curated output the same way
        # _strategy_verdicts does; pipeline.py POPs it so it never reaches graph state (reads are
        # private), and reads_log records it for the leak check.
        reads = getattr(result, "reads", []) or []
        # T4 completeness tripwire: enumerate the read targets and MONITOR coverage — never RETRY on
        # it. A ~7% soft denominator (occasional under-coverage) was accepted in exchange for zero
        # added latency (plan T4). Only fires when the schema carries reads (the in-scope roles).
        if reads or "reads" in output_schema.model_fields:
            coverage, missing = _reads_coverage(reads, payload)
            if coverage < 0.85:
                logger.warning(
                    "reads under-covered: player=%s phase=%s coverage=%.0f%% missing=%s",
                    player_id, output_key, coverage * 100, missing,
                )
        if reads:
            reads_log.append({
                "player_id": player_id,
                "day": payload.get("current_day", 1),
                "output_key": output_key,
                "reads": [r.model_dump() for r in reads],
            })

        if output_key == "day_channel":
            current_day = payload.get("current_day", 1)
            firing_reason = payload.get("firing_reason")  # scheduler trace; rides the Send
            seq = sum(1 for m in payload.get("day_channel", []) if m.day == current_day)

            # Reactive picks must answer: a reactive pass wouldn't discharge the obligation,
            # so the scheduler would just re-pick them. Honor pass_turn only when not reactive.
            is_reactive = firing_reason is not None and firing_reason.tier == "reactive"
            pass_turn = getattr(result, "pass_turn", False) and not is_reactive

            if pass_turn:
                # Proactive decline -> hidden pass marker (the stateless scheduler reads it).
                # gated=False: this is a VOLUNTARY pass, not a novelty-gate silence.
                entry = DayChannel(
                    day=current_day, seq=seq, player=player_id,
                    message="", passed=True, firing_reason=firing_reason, gated=False,
                )
            else:
                message = result.message.strip() if result.message else None
                if not message or message.lower() == "null":
                    output = {}
                    if strategy_update:
                        output["agent_strategies"] = {player_id: strategy_update}
                    if strategy_verdicts:
                        output["_strategy_verdicts"] = strategy_verdicts
                    if memory_verdicts:
                        output["_memory_applicability"] = memory_verdicts
                    if reads:
                        output["_reads"] = reads
                    return output if output else None
                # Proactive novelty gate: a low-novelty (echo/restatement) proactive turn is
                # converted to a hidden pass. Reactive turns are never gated (accountability),
                # and the day's first `opener_floor` real utterances bypass the gate so every
                # day gets a substantive opening before echo-gating engages.
                is_proactive = firing_reason is not None and firing_reason.tier == "proactive"
                today_real = sum(
                    1 for m in payload.get("day_channel", [])
                    if m.day == current_day and m.player != "game_master" and not getattr(m, "passed", False)
                )
                past_opener_floor = today_real >= payload.get("opener_floor", 0)
                if (is_proactive and past_opener_floor
                        and not judge_proactive_novelty(message, payload, current_day)):
                    # Novelty-gate SILENCE: the candidate was substantive-enough to write but
                    # judged an echo/restatement. gated=True + the discarded text is persisted for
                    # a future gate-selectivity audit — and MUST stay out of every agent prompt
                    # (see DayChannel.gated_candidate leak-boundary note).
                    entry = DayChannel(
                        day=current_day, seq=seq, player=player_id,
                        message="", passed=True, firing_reason=firing_reason,
                        gated=True, gated_candidate=message,
                    )
                else:
                    entry = DayChannel(
                        day=current_day, seq=seq, player=player_id,
                        message=message,
                        addressed_targets=getattr(result, "addressed_targets", []),
                        firing_reason=firing_reason,
                    )

            output = {"day_channel": [entry]}
            if strategy_update:
                output["agent_strategies"] = {player_id: strategy_update}
            if strategy_verdicts:
                output["_strategy_verdicts"] = strategy_verdicts
            if memory_verdicts:
                output["_memory_applicability"] = memory_verdicts
            if reads:
                output["_reads"] = reads
            return output

        if output_key == "day_votes":
            validated = _validate_target(
                result.vote_target,
                valid_targets,
                player_id,
            )
            if validated:
                output = {"day_votes": [DayVote(voter=player_id, votee=validated)]}
                if strategy_update:
                    output["agent_strategies"] = {player_id: strategy_update}
                if strategy_verdicts:
                    output["_strategy_verdicts"] = strategy_verdicts
                if memory_verdicts:
                    output["_memory_applicability"] = memory_verdicts
                if reads:
                    output["_reads"] = reads
                return output
            logger.warning(f"{player_id} voted for invalid target: {result.vote_target}")
            continue

        if output_key == "wolf_channel":
            validated = _validate_target(
                result.vote_target,
                valid_targets,
                player_id,
            )
            if validated:
                output = {
                    "wolf_channel": [
                        WolfChannel(
                            day=payload.get("current_day", 1),
                            round=payload.get("current_round", 1),
                            wolf=player_id,
                            message=result.message,
                            vote=validated,
                        )
                    ]
                }
                if strategy_update:
                    output["agent_strategies"] = {player_id: strategy_update}
                if strategy_verdicts:
                    output["_strategy_verdicts"] = strategy_verdicts
                if memory_verdicts:
                    output["_memory_applicability"] = memory_verdicts
                return output
            logger.warning(f"{player_id} voted for invalid target: {result.vote_target}")
            continue

        if output_key == "healer_target":
            validated = _validate_target(
                result.healer_target,
                valid_targets,
                player_id,
            )
            if validated:
                output = {"healer_target": validated}
                if strategy_update:
                    output["updated_strategy"] = strategy_update
                if strategy_verdicts:
                    output["_strategy_verdicts"] = strategy_verdicts
                if memory_verdicts:
                    output["_memory_applicability"] = memory_verdicts
                if reads:
                    output["_reads"] = reads
                return output
            logger.warning(f"Healer targeted invalid player: {result.healer_target}")
            continue

        if output_key == "investigator_target":
            validated = _validate_target(
                result.investigator_target,
                valid_targets,
                player_id,
            )
            if validated:
                output = {"investigator_target": validated}
                if strategy_update:
                    output["updated_strategy"] = strategy_update
                if strategy_verdicts:
                    output["_strategy_verdicts"] = strategy_verdicts
                if memory_verdicts:
                    output["_memory_applicability"] = memory_verdicts
                if reads:
                    output["_reads"] = reads
                return output
            logger.warning(f"Investigator targeted invalid player: {result.investigator_target}")
            continue

        if output_key == "serial_killer_target":
            validated = _validate_target(
                result.serial_killer_target,
                valid_targets,
                player_id,
            )
            if validated:
                output = {"serial_killer_target": validated}
                if strategy_update:
                    output["updated_strategy"] = strategy_update
                if strategy_verdicts:
                    output["_strategy_verdicts"] = strategy_verdicts
                if memory_verdicts:
                    output["_memory_applicability"] = memory_verdicts
                if reads:
                    output["_reads"] = reads
                return output
            logger.warning(f"Serial killer targeted invalid player: {result.serial_killer_target}")
            continue

        if output_key == "vigilante_target":
            # "hold_fire" is a valid sentinel target (the vigilante banks the bullet).
            validated = _validate_target(
                result.vigilante_target,
                valid_targets,
                player_id,
            )
            if validated:
                output = {"vigilante_target": validated}
                if strategy_update:
                    output["updated_strategy"] = strategy_update
                if strategy_verdicts:
                    output["_strategy_verdicts"] = strategy_verdicts
                if memory_verdicts:
                    output["_memory_applicability"] = memory_verdicts
                if reads:
                    output["_reads"] = reads
                return output
            logger.warning(f"Vigilante targeted invalid player: {result.vigilante_target}")
            continue

    # All retries exhausted — random fallback
    logger.error(f"{player_id} failed all retries, using random fallback")
    if output_key == "day_votes":
        fallback = random.choice(valid_targets)
        return {"day_votes": [DayVote(voter=player_id, votee=fallback)]}
    if output_key in (
        "healer_target",
        "investigator_target",
        "serial_killer_target",
        "vigilante_target",
    ):
        fallback = random.choice(valid_targets)
        return {output_key: fallback}
    if output_key == "wolf_channel":
        fallback = random.choice(valid_targets)
        return {"wolf_channel": [WolfChannel(
            day=payload.get("current_day", 1),
            round=payload.get("current_round", 1),
            wolf=player_id,
            message="...",
            vote=fallback,
        )]}

    return None


