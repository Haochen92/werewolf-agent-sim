"""Turn-level eval + leak-test capture — the instrumentation side of an agent's turn.

Everything here is a SIDE CHANNEL: it observes a turn (snapshots context, logs the prompt, records
reads, monitors read completeness) but never contributes to the state delta the node returns — that
belongs in the registered actor node. Split out so the decision path holds only input->output.

``prompt_log`` / ``reads_log`` are the leak-test capture points (tests/leak_test.py): every prompt
sent and read emitted is recorded so the boundary tests can assert no private state reached another
agent. Both are cleared at game start (Agents/main.py). They are the default ``TURN_CAPTURE``; a
process running several games at once (the server) sets its own capture per game instead.
"""

from contextvars import ContextVar
from dataclasses import dataclass, field
from logging import getLogger
from typing import Any

from pydantic import BaseModel

from Agents.schemas import (
    EvalPrivateContext,
)

logger = getLogger(__name__)

prompt_log: list[dict] = []
reads_log: list[dict] = []


@dataclass
class TurnCapture:
    """Where one game's prompts and reads are recorded for the leak checks."""

    prompts: list[dict] = field(default_factory=list)
    reads: list[dict] = field(default_factory=list)


# The capture of the game this turn belongs to, set like GAME_LLM (Agents/llm_factory/chat.py): the
# server's GameSession sets its own inside the game's task, so concurrent games never share a list.
# The default is the process globals above, which one-game-at-a-time callers read after run_game.
TURN_CAPTURE: ContextVar[TurnCapture] = ContextVar(
    "TURN_CAPTURE", default=TurnCapture(prompt_log, reads_log)
)


def log_prompt(payload: dict[str, Any], output_key: str, prompt_input: dict) -> None:
    """Record the prompt an agent was sent, for the leak check (a snapshot copy of prompt_input)."""
    TURN_CAPTURE.get().prompts.append({
        "player_id": payload.get("player_id", ""),
        "player_role": payload.get("player_role", ""),
        "output_key": output_key,
        "day": payload.get("current_day", 1),
        "round": payload.get("current_round", 1),
        "prompt_input": prompt_input.copy(),
    })


def record_reads(
    reads: list, payload: dict[str, Any], output_key: str, output_schema: type[BaseModel]
) -> None:
    """T4 completeness tripwire (MONITOR only — never retry) + reads_log capture for the leak check.
    The coverage warning fires whenever the schema carries reads, even if the agent returned none."""
    if reads or "reads" in output_schema.model_fields:
        coverage, missing = _reads_coverage(reads, payload)
        if coverage < 0.85:
            logger.warning(
                "reads under-covered: player=%s phase=%s coverage=%.0f%% missing=%s",
                payload.get("player_id", ""), output_key, coverage * 100, missing,
            )
    if reads:
        TURN_CAPTURE.get().reads.append({
            "player_id": payload.get("player_id", ""),
            "day": payload.get("current_day", 1),
            "output_key": output_key,
            "reads": [r.model_dump() for r in reads],
        })


def _reads_coverage(reads: list, payload: dict[str, Any]) -> tuple[float, list[str]]:
    """Fraction of the enumerated read targets the agent covered, plus the missing players.

    Targets are enumerated exactly as build_agent_prompt_input builds {read_targets} (surviving
    players, or the wolf-day wolves+villagers shape, minus self), so coverage measures against what
    the prompt asked for. Pure, so the policy is unit-testable; the caller only MONITORS on it (T4).
    """
    expected = payload.get("surviving_players") or (
        payload.get("surviving_wolves", []) + payload.get("surviving_villagers", [])
    )
    self_id = payload.get("player_id")
    expected = [p for p in expected if p != self_id]
    if not expected:
        return 1.0, []
    covered = {getattr(r, "player", None) for r in reads}
    missing = [p for p in expected if p not in covered]
    return (len(expected) - len(missing)) / len(expected), missing


def build_eval_private_context(
    payload: dict[str, Any],
    day: int,
) -> EvalPrivateContext:
    """Snapshot the private context an agent acted on, for the eval case.

    Reads everything via ``.get`` so it works for both day payloads (which carry
    faction-split survivor lists) and night payloads (flat ``surviving_players``).
    """
    return EvalPrivateContext(
        previous_strategy=payload.get("previous_strategy", "") or "",
        day_summaries=[
            summary
            for summary in payload.get("day_summaries", [])
            if summary.day < day
        ],
        wolf_channel=payload.get("wolf_channel", []),
        night_actions=payload.get("night_actions", []),
        surviving_players=payload.get("surviving_players", []),
        surviving_wolves=payload.get("surviving_wolves", []),
        surviving_villagers=payload.get("surviving_villagers", []),
        dead_roster=payload.get("dead_roster", []),
        cast_role_counts=payload.get("cast_role_counts", {}),
    )
