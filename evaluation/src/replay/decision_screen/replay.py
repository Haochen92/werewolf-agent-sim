"""Off-policy regeneration of one frozen decision with a SWAPPED memory block.
Rebuilds the agent payload from the EvalCase, injects the arm's retrieved
observations (empty for the memory-off arm) and the correct abstain choice set,
and re-runs the production action prompt (or an override prompt/schema). Covers
day votes (``_replay_vote``), the forced-structured applicability probe
(``_replay_vote_structured``), and night targets (``_replay_night``)."""

from __future__ import annotations

from typing import Any

from Agents.prompts import (
    HEALER_NIGHT,
    INVESTIGATOR_NIGHT,
    SERIAL_KILLER_NIGHT,
    VIGILANTE_NIGHT,
    WOLF_NIGHT_DISCUSS,
)
from Agents.schemas.output import (
    HealerOutput,
    InvestigatorOutput,
    SerialKillerOutput,
    VigilanteOutput,
    WolfNightDiscussOutput,
)
from Agents.schemas.evaluation import EvalCase
from Agents.llm_factory import get_llm
from Agents.prompts.prompt_inputs import build_agent_prompt_input
from Agents.turn import _run_agent
from Agents.turn.action_space import _valid_targets_for_action, _with_dynamic_target_enum
from evaluation.src.replay.turn_action import action_spec_for
from evaluation.src.replay.situation_summary import eval_case_to_agent_payload
from evaluation.src.replay.decision_screen.schemas import DayVoteOutputStructuredApplicability

# Night-action spec map (role -> prompt, output schema, output_key) mirroring
# application.ACTION_SPECS for the day. _run_agent already handles these night
# output_keys; the wolf kill rides the wolf_channel vote field.
NIGHT_SPECS: dict[str, tuple[Any, Any, str]] = {
    "wolf": (WOLF_NIGHT_DISCUSS, WolfNightDiscussOutput, "wolf_channel"),
    "serial_killer": (SERIAL_KILLER_NIGHT, SerialKillerOutput, "serial_killer_target"),
    "healer": (HEALER_NIGHT, HealerOutput, "healer_target"),
    "investigator": (INVESTIGATOR_NIGHT, InvestigatorOutput, "investigator_target"),
    "vigilante": (VIGILANTE_NIGHT, VigilanteOutput, "vigilante_target"),
}


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
    result = _run_agent(
        payload,
        prompt_template or spec.prompt_template,
        schema_override or spec.output_schema,
        spec.output_key,
    )
    if not result:
        return None, ""
    votes = result.get("day_votes", [])
    votee = votes[0].votee if votes else None
    updated = (result.get("agent_strategies") or {}).get(case.player_id, "")
    return votee, updated


def _replay_night(
    case: EvalCase,
    retrieved_observations: list[Any],
    prompt_template: Any | None = None,
    strategy_points: list[Any] | None = None,
) -> str | None:
    """Regenerate one night target with a swapped memory block. The wolf kill
    rides the wolf_channel vote field; other roles return their *_target directly.
    strategy_points swaps the injected SP block (defaults to none — the
    observations-only screen convention; the checkpoint sweep passes snapshot SPs)."""
    payload = eval_case_to_agent_payload(case)
    payload["retrieved_observations"] = retrieved_observations
    payload["strategy_points"] = strategy_points or []
    prompt, schema, output_key = NIGHT_SPECS[case.player_role]
    result = _run_agent(payload, prompt_template or prompt, schema, output_key)
    if not result:
        return None
    if output_key == "wolf_channel":
        wc = result.get("wolf_channel", [])
        return wc[0].vote if wc else None
    return result.get(output_key)


def _replay_vote_structured(
    case: EvalCase, retrieved_observations: list[Any], allow_abstain: bool
) -> Any | None:
    """Regenerate one vote under DayVoteOutputStructuredApplicability, returning the RAW
    structured object — _run_agent's mapping drops unknown fields, so the per-memory
    memory_applicability list would be lost through it. Mirrors _run_agent's structured
    call (dynamic target enum keeps vote_target a legal player) without the mapping."""
    payload = eval_case_to_agent_payload(case)
    payload["retrieved_observations"] = retrieved_observations
    payload["strategy_points"] = []
    payload["allow_abstain"] = allow_abstain
    spec = action_spec_for(case)
    valid_targets = _valid_targets_for_action(payload, spec.output_key)
    schema = _with_dynamic_target_enum(
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
