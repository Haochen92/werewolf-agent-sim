"""The de-halo pass: a second model checks each extracted observation's verdict against the game.

Extraction judges each move's net effect, and those verdicts drift toward the outcome (a town move
called positive because town won). Synthesis weights strategies by them, so the pass rewrites a
verdict the record does not support to 'unclear' (or flips it when the record shows the move
worked against its own side) before the observations are shown or stored. The original verdicts
and the judge's reasons go into a de-halo record, so nothing is lost.

Configured by ``ExtractionConfig.dehalo``: on/off, the model (a Claude model through the Anthropic
SDK, anything else through the game's model factory) and its thinking level. It never breaks
extraction: a missing key or a failed call leaves the observations as they were.
"""

from __future__ import annotations

from logging import getLogger
from typing import Any

from Agents.memory.claude_structured import claude_api_key, parse_with_claude
from Agents.memory.persistence.config import DehaloConfig
from Agents.prompts.compose import rules_block
from Agents.prompts.extraction.dehalo import DEHALO_PROMPT
from Agents.schemas.dehalo import Judgments

logger = getLogger(__name__)


def _lessons(observations: list) -> str:
    rows = []
    for i, o in enumerate(observations, 1):
        rows.append(f"[{i}] {o.perspective} / {o.action_phase} — verdict: {o.net_verdict}\n"
                    f"  did: {o.approach}\n  immediately: {o.immediate_response}\n"
                    f"  end of game: {o.impact_on_final_game_outcome}")
    return "\n".join(rows)


def _judge_with_claude(prompt: str, config: DehaloConfig) -> tuple[Judgments | None, dict]:
    if not claude_api_key():
        logger.warning("De-halo skipped: no CLAUDE_API_KEY for %s.", config.model)
        return None, {}
    return parse_with_claude(prompt, Judgments, config.model, config.thinking_level)


def _judge_with_factory(prompt: str, config: DehaloConfig) -> tuple[Judgments | None, dict]:
    from langchain_core.callbacks import get_usage_metadata_callback

    from Agents.llm_factory.backends import create_chat_model

    llm = create_chat_model(config.model, temperature=1.0, thinking_level=config.thinking_level)
    with get_usage_metadata_callback() as cb:
        result = llm.with_structured_output(Judgments).invoke(prompt)
    if isinstance(result, dict):
        result = Judgments.model_validate(result)
    return result, dict(cb.usage_metadata)


def judge(prompt: str, config: DehaloConfig) -> tuple[Judgments | None, dict]:
    """The judge's verdicts and token usage for one game's lessons."""
    if config.model.startswith("claude"):
        return _judge_with_claude(prompt, config)
    return _judge_with_factory(prompt, config)


def dehalo_observations(observations: list, inputs: dict[str, Any], config: DehaloConfig) -> dict[str, Any] | None:
    """Rewrite the observations' halo verdicts in place; return the de-halo record (every lesson's
    original and revised verdict, the judge's reason, the model and its usage), or None when the
    pass did not run."""
    if not config.enabled or not observations:
        return None
    prompt = DEHALO_PROMPT.format(
        rules=rules_block(inputs.get("lineup") or []), record=inputs.get("formatted_discussions", ""),
        notes=inputs.get("formatted_strategy_notes", ""), outcome=inputs.get("game_outcome", "unknown"),
        lessons=_lessons(observations))
    try:
        judged, usage = judge(prompt, config)
    except Exception as e:  # noqa: BLE001 — the pass must never break extraction
        logger.warning("De-halo failed on %s (%s); verdicts left as extracted.", config.model, e)
        return None
    if judged is None:
        return None
    rows = []
    for j in judged.judgments:
        if not 1 <= j.index <= len(observations):
            continue
        o = observations[j.index - 1]
        rows.append({"index": j.index, "perspective": o.perspective, "action_phase": o.action_phase,
                     "approach": o.approach, "original_verdict": o.net_verdict,
                     "revised_verdict": j.revised_verdict, "halo": j.halo, "reason": j.reason})
        o.net_verdict = j.revised_verdict
    changed = sum(r["original_verdict"] != r["revised_verdict"] for r in rows)
    logger.info("De-halo (%s): %d of %d verdicts revised.", config.model, changed, len(observations))
    return {"model": config.model, "thinking_level": config.thinking_level, "usage": usage,
            "judged": len(rows), "revised": changed, "judgments": rows}
