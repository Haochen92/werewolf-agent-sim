"""Post-game extraction prompt construction + input formatting.

Turns finished-game state into the formatted strings and full prompt the extraction agent
consumes. The `llm.invoke` itself lives in extraction_agent.py (this package).
"""

from __future__ import annotations

from logging import getLogger

from Agents.prompts.prompt_formatters import (
    format_day_channel_postgame,
    format_investigator_results,
    format_roles,
    format_strategy_notes_postgame,
    format_wolf_channel,
)
from Agents.prompts import (
    EPISTEMIC_STATUS_RULE,
    GAME_RULES,
    POSTGAME_EXTRACTION_PROMPT,
    ROLE_EXTRACTION_PREFIX,
    ROLE_EXTRACTION_TAIL,
    ROLE_PHASE_EXTRACTION_TAIL,
    SITUATION_STANDARDS,
)
from Agents.state import OrchestratorGraph

logger = getLogger(__name__)

# One-line meaning of each action phase, injected into the namespace-augment tail
# so the focused pass anchors on the assigned phase without re-deriving it.
_PHASE_DEFINITIONS: dict[str, str] = {
    "day_discussion": (
        "The day_discussion phase is public debate: what to say, how to argue, "
        "when to stay silent, how to read others, and how to manage suspicion "
        "during the discussion rounds."
    ),
    "day_vote": (
        "The day_vote phase is the elimination vote: vote target selection, vote "
        "timing, voting to preserve cover, and reading voting patterns."
    ),
    "night_action": (
        "The night_action phase is the secret night move: night target selection "
        "— whom wolves kill, whom the healer protects, whom the investigator "
        "checks, whom the serial killer or vigilante targets."
    ),
}


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
        game_rules=GAME_RULES,
        **inputs,
    )


def build_role_extraction_prefix(inputs: dict[str, str]) -> str:
    """Build the role-NEUTRAL extraction prefix (rules + standards + full game
    data + field definitions). Byte-identical across all roles, so it is the unit
    cached once per game and reused by every role fan-out call."""
    return ROLE_EXTRACTION_PREFIX.format(
        situation_standards=SITUATION_STANDARDS,
        epistemic_status_rule=EPISTEMIC_STATUS_RULE,
        game_rules=GAME_RULES,
        **inputs,
    )


def build_role_extraction_tail(role: str) -> str:
    """Build the tiny per-role lock appended after the cached prefix."""
    return ROLE_EXTRACTION_TAIL.format(role=role)


def build_role_phase_extraction_tail(role: str, phase: str) -> str:
    """Build the (role, action_phase) lock tail for namespace augmentation.

    Sharper than the role-only tail: pins the assigned phase too and asks for an
    exhaustive deep pass on that single namespace. Shares the cached prefix."""
    return ROLE_PHASE_EXTRACTION_TAIL.format(
        role=role,
        phase=phase,
        phase_definition=_PHASE_DEFINITIONS.get(phase, ""),
    )


def extraction_inputs_from_frozen_case(case: dict) -> dict[str, str]:
    """Rebuild extraction prompt inputs from a stored extraction EvalCase.

    The frozen extraction set carries the same pre-formatted game data the live
    extraction node produced (roles, discussions, strategy notes, outcome), so a
    finished game can be re-mined offline with no transcript or Langfuse access.
    Mirrors the dict shape of `format_extraction_inputs`."""
    return {
        "formatted_roles": format_roles(case.get("roles", {})),
        "formatted_discussions": case.get("formatted_discussions", ""),
        "formatted_strategy_notes": case.get("formatted_strategy_notes", ""),
        "formatted_previous_strategies": (
            "No previous role strategy summaries were injected into this game."
        ),
        "game_outcome": case.get("game_outcome", "unknown"),
    }


def build_role_extraction_prompt(inputs: dict[str, str], role: str) -> str:
    """Build the full role-specific extraction prompt (prefix + tail) as one
    string — the non-cached path (backup model, experiments)."""
    return build_role_extraction_prefix(inputs) + build_role_extraction_tail(role)
