from __future__ import annotations

from dataclasses import dataclass
from logging import getLogger

from Agents.agents import get_llm_pro, get_llm_pro_backup
from Agents.formatters import (
    format_day_channel_postgame,
    format_investigator_results,
    format_roles,
    format_strategy_notes_postgame,
    format_wolf_channel,
)
from Agents.prompts import EPISTEMIC_STATUS_RULE, POSTGAME_EXTRACTION_PROMPT, ROLE_EXTRACTION_PROMPT, SITUATION_STANDARDS
from Agents.schemas import GameStrategyOutput
from Agents.state import OrchestratorGraph

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


def format_extraction_inputs(state: OrchestratorGraph) -> dict[str, str]:
    """Format game state into the strings needed for the extraction prompt.

    Returns a dict with keys: formatted_roles, formatted_discussions,
    formatted_strategy_notes, formatted_previous_strategies, game_outcome.
    """
    formatted_roles = format_roles(state.get("roles", {}))

    formatted_discussions = (
        "=== Day Discussions ===\n"
        + format_day_channel_postgame(
            state.get("day_channel", []), state.get("roles", {})
        )
        + "\n\n=== Wolf Night Discussions ===\n"
        + format_wolf_channel(state.get("wolf_channel", []))
        + "\n\n=== Investigator Results ===\n"
        + format_investigator_results(state.get("investigator_results", []))
    )

    formatted_strategy_notes = format_strategy_notes_postgame(
        state.get("agent_strategies", {}), state.get("roles", {})
    )

    return {
        "formatted_roles": formatted_roles,
        "formatted_discussions": formatted_discussions,
        "formatted_strategy_notes": formatted_strategy_notes,
        "formatted_previous_strategies": (
            "No previous role strategy summaries were injected into this game."
        ),
        "game_outcome": state.get("winner", "unknown"),
    }


def build_extraction_prompt(inputs: dict[str, str]) -> str:
    """Build the full extraction prompt from pre-formatted inputs."""
    return POSTGAME_EXTRACTION_PROMPT.format(
        situation_standards=SITUATION_STANDARDS,
        epistemic_status_rule=EPISTEMIC_STATUS_RULE,
        **inputs,
    )


def build_role_extraction_prompt(inputs: dict[str, str], role: str) -> str:
    """Build a role-specific extraction prompt from pre-formatted inputs."""
    role_prompt = ROLE_EXTRACTION_PROMPT.format(role=role)
    return role_prompt.format(
        situation_standards=SITUATION_STANDARDS,
        epistemic_status_rule=EPISTEMIC_STATUS_RULE,
        **inputs,
    )


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
