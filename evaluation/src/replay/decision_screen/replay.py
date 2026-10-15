"""Off-policy regeneration of one frozen decision with a SWAPPED memory block.
Rebuilds the agent payload from the EvalCase, injects the arm's retrieved
observations (empty for the memory-off arm) and the correct abstain choice set,
and re-runs the production action prompt (or an override prompt/schema). Covers
day votes (``_replay_vote``), the forced-structured applicability probe
(``_replay_vote_structured``), and night targets (``_replay_night``)."""

from __future__ import annotations

from typing import Any

from Agents.prompts import night_template
from Agents.schemas.lineup_output import night_output
from Agents.schemas.roles import ROLE_SPECS
from Agents.schemas.evaluation import EvalCase
from Agents.llm_factory import get_llm
from Agents.prompts.prompt_inputs import build_agent_prompt_input
from Agents.turn import run_agent
from Agents.turn.action_space import valid_targets_for_action, output_schema_with_legal_targets
from evaluation.src.replay.turn_action import action_spec_for
from evaluation.src.replay.situation_summary import case_lineup, eval_case_to_agent_payload
from evaluation.src.replay.decision_screen.schemas import DayVoteOutputStructuredApplicability

def night_spec(case: EvalCase) -> tuple[Any, Any, str]:
    """A ten-seat role's night turn (prompt, output schema, output_key), mirroring
    turn_action.action_spec_for for the day: built from the role's card and the case's
    lineup. A wolf's own night turn is its skill; the pack's kill is the carrier's turn and is
    not replayed here. The nine-seat roles (the wolf's pack vote) are refused."""
    role = case.player_role
    lineup = case_lineup(case)
    spec = ROLE_SPECS.get(role)
    if spec is None or spec.retired or role not in lineup:
        raise ValueError(f"Unsupported night replay role: {role!r}")
    return night_template(role), night_output(role, lineup), spec.target_field


def _replay_vote(
    case: EvalCase,
    retrieved_observations: list[Any],
    allow_abstain: bool,
    prompt_template: Any | None = None,
    schema_override: Any | None = None,
    strategy_points: list[Any] | None = None,
) -> tuple[str | None, str]:
    """Regenerate one vote with a swapped memory block and the correct abstain
    choice set. Returns (votee, replayed updated_strategy). prompt_template and
    schema_override let an arm vary the prompt or the output schema (e.g. the
    reason-first DayVoteOutput); defaults are the role's live template + schema.
    strategy_points swaps the injected strategy-point block too (defaults to none,
    the observations-only convention every existing screen relies on); the
    checkpoint-replay sweep passes the snapshot's retrieved SPs so it measures the
    loop's synthesized-SP growth, not just observations."""
    payload = eval_case_to_agent_payload(case)
    payload["retrieved_observations"] = retrieved_observations
    payload["strategy_points"] = strategy_points or []
    payload["allow_abstain"] = allow_abstain
    spec = action_spec_for(case)
    result = run_agent(
        payload,
        prompt_template or spec.prompt_template,
        schema_override or spec.output_schema,
        spec.output_key,
    )
    if not result:
        return None, ""
    # run_agent returns a resolved turn: the vote is its entry.
    return result.entry.votee, result.effects.strategy or ""


def _replay_night(
    case: EvalCase,
    retrieved_observations: list[Any],
    prompt_template: Any | None = None,
    strategy_points: list[Any] | None = None,
) -> str | None:
    """Regenerate one night target with a swapped memory block: the role's target, its
    no-action word when it declined ("hold_fire", "keep_sigil", ...), the kind for a choice with
    no target ("conceal"), None on a dropped call.
    strategy_points swaps the injected SP block (defaults to none — the
    observations-only screen convention; the checkpoint sweep passes snapshot SPs)."""
    payload = eval_case_to_agent_payload(case)
    payload["retrieved_observations"] = retrieved_observations
    payload["strategy_points"] = strategy_points or []
    prompt, schema, output_key = night_spec(case)
    result = run_agent(payload, prompt_template or prompt, schema, output_key)
    if not result:
        return None
    choice = result.entry  # None when the role declined; hold_fire and conceal carry no target
    if choice is None:
        return ROLE_SPECS[case.player_role].no_action or None
    return choice.target or choice.kind


def _replay_vote_structured(
    case: EvalCase, retrieved_observations: list[Any], allow_abstain: bool
) -> Any | None:
    """Regenerate one vote under DayVoteOutputStructuredApplicability, returning the RAW
    structured object — run_agent's mapping drops unknown fields, so the per-memory
    memory_applicability list would be lost through it. Mirrors run_agent's structured
    call (dynamic target enum keeps vote_target a legal player) without the mapping."""
    payload = eval_case_to_agent_payload(case)
    payload["retrieved_observations"] = retrieved_observations
    payload["strategy_points"] = []
    payload["allow_abstain"] = allow_abstain
    spec = action_spec_for(case)
    valid_targets = valid_targets_for_action(payload, spec.output_key)
    schema = output_schema_with_legal_targets(
        DayVoteOutputStructuredApplicability, spec.output_key, valid_targets
    )
    chain = spec.prompt_template | get_llm().with_structured_output(schema)
    try:
        return chain.invoke(
            build_agent_prompt_input(payload),
            config={"run_name": f"applic_{case.player_id}"},
        )
    except Exception:  # noqa: BLE001 - best-effort replay
        return None
