"""Turn-level eval + leak-test capture — the instrumentation side of an agent's turn.

Everything here is a SIDE CHANNEL: it observes a turn (snapshots context, logs the prompt, records
reads, monitors read completeness) but never contributes to the state delta the node returns — that
belongs in the registered actor node. Split out so the decision path holds only input->output.

``prompt_log`` / ``reads_log`` are the leak-test capture points (tests/leak_test.py): every prompt
sent and read emitted is recorded so the boundary tests can assert no private state reached another
agent. Both are cleared at game start (Agents/main.py).
"""

from logging import getLogger
from typing import Any

from pydantic import BaseModel

from Agents.schemas import (
    EvalPrivateContext,
)

logger = getLogger(__name__)

prompt_log: list[dict] = []
reads_log: list[dict] = []


def log_prompt(payload: dict[str, Any], output_key: str, prompt_input: dict) -> None:
    """Record the prompt an agent was sent, for the leak check (a snapshot copy of prompt_input)."""
    prompt_log.append({
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
        reads_log.append({
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
    faction-split survivor lists) and night payloads (flat ``surviving_players``,
    plus ``vigilante_results`` for the vigilante).
    """
    return EvalPrivateContext(
        previous_strategy=payload.get("previous_strategy", "") or "",
        day_summaries=[
            summary
            for summary in payload.get("day_summaries", [])
            if summary.day < day
        ],
        wolf_channel=payload.get("wolf_channel", []),
        investigator_results=payload.get("investigator_results", []),
        vigilante_results=payload.get("vigilante_results", []),
        surviving_players=payload.get("surviving_players", []),
        surviving_wolves=payload.get("surviving_wolves", []),
        surviving_villagers=payload.get("surviving_villagers", []),
        dead_roster=payload.get("dead_roster", []),
        cast_role_counts=payload.get("cast_role_counts", {}),
    )
