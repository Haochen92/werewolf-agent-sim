from Agents.formatters import (
    format_day_channel_postgame,
    format_investigator_results,
    format_roles,
    format_strategy_notes_postgame,
    format_wolf_channel,
)
from Agents.state import OrchestratorGraph
from Agents.schemas import GameStrategyOutput
from Agents.prompts import POSTGAME_EXTRACTION_PROMPT
from Agents.agents import get_llm_pro
from logging import getLogger

logger = getLogger(__name__)

def extract_postgame(state: OrchestratorGraph, max_retries: int = 2 ) -> GameStrategyOutput | None:
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
    )

    # Call Pro model with structured output
    llm_pro = get_llm_pro()
    for attempt in range(max_retries + 1):
        try:
            result = llm_pro.with_structured_output(GameStrategyOutput).invoke(
                prompt,
                config={"run_name": "postgame_extraction"},
            )
            if isinstance(result, GameStrategyOutput):
                return result

            if isinstance(result, dict):
                logger.warning(f"Received dict instead of GameStrategyOutput, attempting to cast: {result}")
                return GameStrategyOutput.model_validate(result)
        except Exception as e:
            logger.warning(f"Post-game extraction failed on attempt {attempt + 1}: {e}")

    return None
