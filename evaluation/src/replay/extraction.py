"""Replay the postgame extraction prompt on a frozen ``ExtractionCase``.

Re-runs extraction with a chosen model so the regenerated observations and
strategy points can be judged in the same ``ExtractionDatasetRecord`` shape as
the original. The CLI wrapper (``experiments/cli_runners/regen/extraction_regen``)
adds retries, record assembly, and player-id leakage reporting.
"""

from __future__ import annotations

from Agents.llm_factory import create_chat_model
from Agents.memory.extraction import build_extraction_prompt
from Agents.schemas import GameStrategyOutput
from Agents.schemas.evaluation import ExtractionCase


def make_extraction_llm(model: str, temperature: float = 0.0, **kwargs):
    return create_chat_model(model, temperature=temperature, **kwargs)


def build_prompt_from_case(case: ExtractionCase) -> str:
    inputs = {
        "formatted_roles": "\n".join(
            f"{pid}: {role}" for pid, role in case.roles.items()
        ),
        "formatted_discussions": case.formatted_discussions,
        "formatted_strategy_notes": case.formatted_strategy_notes,
        "formatted_previous_strategies": "No previous role strategy summaries.",
        "game_outcome": case.game_outcome,
    }
    return build_extraction_prompt(inputs)


def run_extraction(llm, prompt: str) -> GameStrategyOutput:
    result = llm.with_structured_output(GameStrategyOutput).invoke(prompt)
    if isinstance(result, GameStrategyOutput):
        return result
    if isinstance(result, dict):
        return GameStrategyOutput.model_validate(result)
    raise TypeError(f"Unexpected extraction result type: {type(result)!r}")
