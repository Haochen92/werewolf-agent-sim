"""Post-game extraction prompt construction + input formatting.

Turns finished-game state into the formatted strings and full prompt the extraction agent
consumes. The `llm.invoke` itself lives in extraction_agent.py (this package).
"""

from __future__ import annotations

from logging import getLogger

from Agents.formatters import (
    format_day_channel_postgame,
    format_investigator_results,
    format_roles,
    format_strategy_notes_postgame,
    format_wolf_channel,
)
from Agents.prompts import EPISTEMIC_STATUS_RULE, POSTGAME_EXTRACTION_PROMPT, ROLE_EXTRACTION_PROMPT, SITUATION_STANDARDS
from Agents.state import OrchestratorGraph

logger = getLogger(__name__)


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
