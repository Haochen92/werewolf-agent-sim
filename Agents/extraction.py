from Agents.formatters import (
    format_day_channel_postgame,
    format_investigator_results,
    format_roles,
    format_strategy_notes_postgame,
    format_wolf_channel,
)
from Agents.state import OrchestratorGraph
from Agents.schemas import GameStrategyOutput
from Agents.prompts import POSTGAME_EXTRACTION_PROMPT, SITUATION_STANDARDS
from Agents.agents import get_llm_pro, get_llm_pro_backup
from logging import getLogger

logger = getLogger(__name__)


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
    state: OrchestratorGraph,
    max_retries: int = 2,
    backup_max_retries: int = 2,
) -> GameStrategyOutput | None:
    """
    Post-game extraction: calls the Pro model with the full game transcript
    to extract observations and generate updated strategies per role.
    """
    # Format all inputs
    formatted_roles = format_roles(state.get("roles", {}))

    formatted_discussions = (
        "=== Day Discussions ===\n"
        + format_day_channel_postgame(state.get("day_channel", []), state.get("roles", {}))
        + "\n\n=== Wolf Night Discussions ===\n"
        + format_wolf_channel(state.get("wolf_channel", []))
        + "\n\n=== Investigator Results ===\n"
        + format_investigator_results(state.get("investigator_results", []))
    )

    formatted_strategy_notes = format_strategy_notes_postgame(
        state.get("agent_strategies", {}), state.get("roles", {})
    )
    formatted_previous_strategies = "No previous role strategy summaries were injected into this game."

    game_outcome = state.get("winner", "unknown")

    # Build the prompt
    prompt = POSTGAME_EXTRACTION_PROMPT.format(
        formatted_roles=formatted_roles,
        formatted_discussions=formatted_discussions,
        formatted_strategy_notes=formatted_strategy_notes,
        formatted_previous_strategies=formatted_previous_strategies,
        game_outcome=game_outcome,
        situation_standards=SITUATION_STANDARDS,
    )

    models = (
        ("primary", get_llm_pro(), max_retries),
        ("backup", get_llm_pro_backup(), backup_max_retries),
    )
    for label, llm, retries in models:
        for attempt in range(retries + 1):
            try:
                return _invoke_extraction_model(
                    llm,
                    prompt,
                    f"postgame_extraction_{label}",
                )
            except Exception as e:
                logger.warning(
                    "Post-game extraction failed with %s model on attempt %s: %s",
                    label,
                    attempt + 1,
                    e,
                )
        logger.warning("Post-game extraction exhausted %s model attempts.", label)

    return None
