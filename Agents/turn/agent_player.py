"""The agent seat — an agent's LLM turn.

``run_agent`` turns "it's this agent's turn to decide X" into a legal, game-ready action: it
constrains the answer space, GENERATEs a decision (one LLM call, retried), and hands it to the shared
``resolve_decision`` (``resolve.py``), which turns it into a typed resolved turn — with a random legal
fallback so the game never stalls. The human seat's parallel path is ``human_turn.py``; both route
through the same ``resolve_decision``, so agent and human decisions resolve identically.

The turn's instrumentation — the leak-test prompt/reads logs and the reads-completeness monitor —
lives in ``eval.py``; ``run_agent`` calls ``log_prompt`` / ``record_reads`` as side channels that
never touch the returned delta.
"""
from logging import getLogger
from typing import Any
import random

from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel

from Agents.llm_factory import get_llm, get_llm_game_fallback
from Agents.prompts.prompt_inputs import build_agent_prompt_input
from Agents.schemas.game_events import (
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
    ResolvedTurn,
    ResolvedVigilanteTarget,
    ResolvedWolfDiscussion,
    ResolvedWolfVote,
)
from Agents.turn.action_space import (
    valid_targets_for_action,
    output_schema_with_legal_targets,
)
from Agents.turn.eval import log_prompt, record_reads
from Agents.turn.resolve import (
    NIGHT_TARGET_KEYS,
    RETRY,
    extract_agent_reasoning,
    resolve_decision,
)

load_dotenv()
logger = getLogger(__name__)


def run_agent(
    payload: dict[str, Any],
    prompt_template: ChatPromptTemplate,
    output_schema: type[BaseModel],
    output_key: str,
    max_retries: int = 1,
) -> ResolvedTurn | None:
    """Run one agent decision: constrain -> generate -> resolve, retrying on an LLM error or a
    rejected decision, with a legal typed fallback if every attempt fails.

    The human seat's counterpart is ``run_human_decision`` (human_turn.py): it swaps ``_generate``
    for ``interrupt()`` but takes the same ``resolve_decision`` path.
    """
    valid_targets = valid_targets_for_action(payload, output_key)
    player_id = payload.get("player_id", "")

    # Constrain: bind the model to the legal-targets schema; build + log the prompt once.
    schema = output_schema_with_legal_targets(output_schema, output_key, valid_targets)
    chain = prompt_template | get_llm().with_structured_output(schema)
    prompt_input = build_agent_prompt_input(payload)
    log_prompt(payload, output_key, prompt_input)

    for _ in range(max_retries + 1):
        result = _generate(chain, prompt_input, output_key, player_id)
        if result is None:
            continue
        reasoning = extract_agent_reasoning(result)
        record_reads(reasoning["reads"], payload, output_key, output_schema)
        outcome = resolve_decision(result, reasoning, output_key, payload, valid_targets)
        if outcome is not RETRY:
            return outcome

    # Exhausted on the primary model: one shot on the fallback backend before resorting to a
    # random action — a different provider fails differently (DeepSeek's unconstrained
    # tool-calling emits off-schema output that Gemini's constrained decoding cannot).
    fallback_llm = get_llm_game_fallback()
    if fallback_llm is not None:
        fallback_chain = prompt_template | fallback_llm.with_structured_output(schema)
        result = _generate(fallback_chain, prompt_input, output_key, player_id)
        if result is not None:
            reasoning = extract_agent_reasoning(result)
            record_reads(reasoning["reads"], payload, output_key, output_schema)
            outcome = resolve_decision(result, reasoning, output_key, payload, valid_targets)
            if outcome is not RETRY:
                logger.warning(f"{player_id} rescued by the fallback model on {output_key}")
                return outcome

    # Exhausted discussion becomes a typed technical pass. Persisting the classification advances
    # the stateless day/wolf scheduler and makes failures countable without putting operational
    # attempt details in graph state; those remain in logs/traces. Target actions still need a
    # random legal move so their phase can complete.
    if output_key == "day_channel":
        current_day = payload.get("current_day", 1)
        seq = sum(
            1 for message in payload.get("day_channel", [])
            if message.day == current_day
        )
        logger.error(
            "%s failed all decision attempts on %s; recording technical pass",
            player_id,
            output_key,
        )
        return ResolvedDayDiscussion(
            entry=DayChannel(
                day=current_day,
                seq=seq,
                player=player_id,
                message="",
                passed=True,
                pass_reason=DiscussionPassReason.GENERATION_FAILED,
                firing_reason=payload.get("firing_reason"),
            )
        )
    if output_key == "wolf_channel":
        logger.error(
            "%s failed all decision attempts on %s; recording technical pass",
            player_id,
            output_key,
        )
        return ResolvedWolfDiscussion(
            entry=WolfChannel(
                day=payload.get("current_day", 1),
                round=payload.get("current_round", 1),
                wolf=player_id,
                message="",
                vote="",
                passed=True,
                pass_reason=DiscussionPassReason.GENERATION_FAILED,
            )
        )

    logger.error(f"{player_id} failed all retries on {output_key}, using random fallback")
    if output_key == "day_votes":
        return ResolvedDayVote(
            entry=DayVote(voter=player_id, votee=random.choice(valid_targets))
        )
    if output_key in NIGHT_TARGET_KEYS:
        result_type = _NIGHT_RESULT_BY_KEY[output_key]
        return result_type(entry=random.choice(valid_targets))
    if output_key == "wolf_vote":
        return ResolvedWolfVote(
            entry=WolfChannel(
                day=payload.get("current_day", 1),
                round=payload.get("current_round", 1),
                wolf=player_id,
                message="",
                vote=random.choice(valid_targets),
            )
        )
    return None


def _generate(chain: Any, prompt_input: dict, output_key: str, player_id: str):
    """One structured LLM call. Returns the parsed decision, or None on an API/parse error."""
    try:
        return chain.invoke(prompt_input, config={"run_name": f"{output_key}_{player_id}"})
    except Exception as e:
        logger.warning(f"LLM call failed for {player_id}: {e}")
        return None


_NIGHT_RESULT_BY_KEY = {
    "healer_target": ResolvedHealerTarget,
    "investigator_target": ResolvedInvestigatorTarget,
    "serial_killer_target": ResolvedSerialKillerTarget,
    "vigilante_target": ResolvedVigilanteTarget,
}
