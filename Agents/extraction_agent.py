"""Extraction agent: the post-game `llm.invoke` (primary → backup, with retries) that turns a
finished game's pre-built prompt into a structured GameStrategyOutput. Prompt construction and
input formatting live in extraction.py."""

from __future__ import annotations

from dataclasses import dataclass
from logging import getLogger

from Agents.llm_factory import get_llm_pro, get_llm_pro_backup
from Agents.schemas import GameStrategyOutput

logger = getLogger(__name__)


@dataclass
class ExtractionResult:
    output: GameStrategyOutput
    model_used: str


def _invoke_extraction_model(llm, prompt: str, run_name: str) -> GameStrategyOutput:
    result = llm.with_structured_output(GameStrategyOutput).invoke(
        prompt,
        config={"run_name": run_name},
    )
    if isinstance(result, GameStrategyOutput):
        return result

    if isinstance(result, dict):
        logger.warning(
            "Received dict instead of GameStrategyOutput, attempting to cast: %s",
            result,
        )
        return GameStrategyOutput.model_validate(result)

    raise TypeError(f"Unexpected post-game extraction result type: {type(result)!r}")


def extract_postgame(
    prompt: str,
    max_retries: int = 2,
    backup_max_retries: int = 2,
) -> ExtractionResult | None:
    """Call the extraction LLM with a pre-built prompt.

    Returns an ExtractionResult with the output and model label, or None if
    all attempts fail.
    """
    models = (
        ("primary", get_llm_pro(), max_retries),
        ("backup", get_llm_pro_backup(), backup_max_retries),
    )
    for label, llm, retries in models:
        for attempt in range(retries + 1):
            try:
                output = _invoke_extraction_model(
                    llm,
                    prompt,
                    f"postgame_extraction_{label}",
                )
                return ExtractionResult(output=output, model_used=label)
            except Exception as e:
                logger.warning(
                    "Post-game extraction failed with %s model on attempt %s: %s",
                    label,
                    attempt + 1,
                    e,
                )
        logger.warning("Post-game extraction exhausted %s model attempts.", label)

    return None
