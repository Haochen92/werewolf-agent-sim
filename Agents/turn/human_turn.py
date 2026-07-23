"""The human seat — a human's substitute for an LLM decision, via LangGraph ``interrupt()``.

``_run_agent`` (decision.py) branches here when ``payload["human_player"]`` is set: instead of
prompting an LLM, we pause the graph, surface a ``HumanTurnRequest`` to the driver, and resume with
the human's ``HumanTurnResponse``. The response is then shaped into an object **indistinguishable
from an LLM decision** to the downstream consumers (``_extract_side_outputs`` / ``_interpret``), so
the human takes the exact same interpret path — no retry, no random fallback, no LLM prompt.

A human types free text, so ``addressed_targets`` (which drive the reactive scheduler) are tagged
after the fact: the extractor classifies the message, and the human's own reactive debts are
discharged deterministically from ``firing_reason.owes``. This module is generation-only — the
interpret/validation of what it returns stays in decision.py.
"""

from types import SimpleNamespace
from typing import Any

from langgraph.types import interrupt

from Agents.prompts.prompt_inputs import build_agent_prompt_input as _build_agent_prompt_input
from Agents.schemas.game_events import AddressedTarget
from Agents.schemas.human_player import HumanTurnRequest, HumanTurnResponse
from Agents.turn.action_space import _TARGET_FIELD_BY_OUTPUT_KEY, _valid_targets_for_action
from Agents.turn.addressing_agent import extract_addressed_targets
from Agents.turn.interpret import _RETRY, _extract_side_outputs, _interpret


class HumanTurnContractError(ValueError):
    """A resumed human action violated the turn contract for its request. The driver is expected to
    run ``validate_human_response`` BEFORE ``Command(resume=...)`` and surface a UI error, so this
    firing means the driver resumed with an action the request never permitted — a driver bug, not a
    user typo. Raised loudly rather than degraded to a silent no-op."""


def validate_human_response(request: HumanTurnRequest, raw_response: Any) -> HumanTurnResponse:
    """Validate a raw resume payload against the exact pending request. Pure — no side effects — so
    the resume driver can call it to gate ``Command(resume=...)`` and the node can re-check defensively.

    Discussion (day_channel): a pass needs ``can_pass``; otherwise a non-empty message is required and
    no target may be set. Every other phase (votes, wolf night, night actions): no pass, and the
    target must be one of the request's ``valid_targets`` (which already includes the abstain /
    hold_fire sentinels)."""
    response = HumanTurnResponse.model_validate(raw_response)

    if request.phase == "day_channel":
        if response.pass_turn:
            if not request.can_pass:
                raise HumanTurnContractError("You must respond on this reactive turn.")
        elif not (response.message and response.message.strip()):
            raise HumanTurnContractError("Enter a message or choose pass.")
        if response.target is not None:
            raise HumanTurnContractError("A discussion turn cannot include a target.")
    else:
        if response.pass_turn:
            raise HumanTurnContractError(f"{request.phase} cannot be passed.")
        if response.target not in request.valid_targets:
            raise HumanTurnContractError(f"Invalid target: {response.target!r}")

    return response


# Human-readable ask per phase, shown to the human seat in the interrupt request.
_PHASE_INSTRUCTION = {
    "day_channel": "Your turn in the day discussion — speak, or pass if you have nothing to add.",
    "day_votes": "Cast your vote for who to eliminate today.",
    "wolf_channel": "Wolf night — send a message to your pack and cast your kill vote.",
    "healer_target": "Choose a player to protect tonight.",
    "investigator_target": "Choose a player to investigate tonight.",
    "serial_killer_target": "Choose a player to kill tonight.",
    "vigilante_target": "Choose a player to shoot tonight, or hold your fire.",
}


def _run_human_decision(payload: dict[str, Any], output_key: str) -> dict[str, Any] | None:
    """The human seat's whole turn — the counterpart of ``_run_agent``, taking the SAME ``_interpret``
    path but none of the agent scaffolding. The pipeline routes here BEFORE the span / memory retrieval
    / adoption / EvalCase, so a human turn pays for none of them (they'd feed a prompt/eval the human
    never participates in).

    ``_human_player_action`` pauses for input (interrupt) and returns an object shaped like an LLM
    decision; ``_interpret`` turns it into the same legal state delta. No retry, no random fallback —
    an invalid resumed action means the driver breached its contract, so raise rather than degrade.
    """
    valid_targets = _valid_targets_for_action(payload, output_key)
    result = _human_player_action(payload, output_key, valid_targets)
    side_outputs = _extract_side_outputs(result)
    outcome = _interpret(result, side_outputs, output_key, payload, valid_targets)
    if outcome is _RETRY:
        raise HumanTurnContractError(f"invalid resumed human action for {output_key}")
    return outcome


def _human_player_action(
    payload: dict[str, Any], output_key: str, valid_targets: list[str]
) -> SimpleNamespace:
    """The human seat's substitute for ``_generate``: pause the graph, collect the human's action,
    and return it shaped exactly like an LLM decision so the shared ``_extract_side_outputs`` ->
    ``_interpret`` path treats it identically.

    The human's free text is tagged for ``addressed_targets`` after the fact so day discussion drives
    the reactive scheduler the same way an agent's self-tagged output would.
    """
    request = _build_human_request(payload, output_key, valid_targets)
    # Defensive re-validation: the driver validates before resuming, so a failure here means the
    # driver resumed with an action the request never permitted (a contract breach) — raise loudly.
    response = validate_human_response(request, interrupt(request.model_dump()))
    addressed = _human_addressed_targets(response, payload, output_key)
    return _human_result_shaped(response, output_key, addressed)


def _build_human_request(
    payload: dict[str, Any], output_key: str, valid_targets: list[str]
) -> HumanTurnRequest:
    """The interrupt request: the same board the LLM sees (role-filtered upstream), curated to what a
    human needs to decide, plus the legal choices and whether a pass is allowed this turn."""
    ctx = _build_agent_prompt_input(payload)
    firing_reason = payload.get("firing_reason")
    is_reactive = firing_reason is not None and firing_reason.tier == "reactive"
    return HumanTurnRequest(
        player_id=payload.get("player_id", ""),
        role=payload.get("player_role", ""),
        phase=output_key,
        day=payload.get("current_day", 1),
        instruction=_PHASE_INSTRUCTION.get(output_key, "Make your move."),
        valid_targets=valid_targets,
        can_pass=(output_key == "day_channel" and not is_reactive),
        dialogue=ctx["day_channel"],
        day_summaries=ctx["day_summaries"],
        surviving_players=payload.get("surviving_players")
        or (payload.get("surviving_wolves", []) + payload.get("surviving_villagers", [])),
        dead_roster=ctx["dead_roster"],
        alive_roles=ctx["alive_roles"],
        firing_brief=ctx["firing_brief"],
        wolf_channel=ctx["wolf_channel"],
        investigator_results=ctx["investigator_results"],
        vigilante_results=ctx["vigilante_results"],
        previous_strategy=ctx["previous_strategy"],
    )


def _human_result_shaped(
    response: HumanTurnResponse, output_key: str, addressed: list[AddressedTarget]
) -> SimpleNamespace:
    """Shape the human's response into an object indistinguishable from an LLM decision to the
    consumers: they read the action via attributes, so expose exactly those — the target under the
    field name ``_interpret`` expects for this ``output_key``. No reads/verdicts/strategy note is set,
    so ``_extract_side_outputs`` finds no private carriers (a human has none)."""
    result = SimpleNamespace(
        message=response.message,
        pass_turn=response.pass_turn,
        addressed_targets=addressed,
    )
    target_field = _TARGET_FIELD_BY_OUTPUT_KEY.get(output_key)
    if target_field:
        setattr(result, target_field, response.target)
    return result


def _human_addressed_targets(
    response: HumanTurnResponse, payload: dict[str, Any], output_key: str
) -> list[AddressedTarget]:
    """Whom the human's message addresses — day discussion only (the reactive scheduler runs there).
    The extractor tags the free text; the human's own reactive debts (``firing_reason.owes``) are
    discharged deterministically, so a reactive human who speaks always clears their obligation even
    if the extractor misses it. ``[]`` for a pass, an empty message, or any non-discussion turn."""
    if (
        output_key != "day_channel"
        or response.pass_turn
        or not (response.message and response.message.strip())
    ):
        return []
    extracted = extract_addressed_targets(response.message, payload, payload.get("current_day", 1))
    firing_reason = payload.get("firing_reason")
    owes = firing_reason.owes if firing_reason is not None and firing_reason.tier == "reactive" else []
    discharge = [
        AddressedTarget(target=creditor, addressed_form="response", stance="neutral")
        for creditor in owes
    ]
    return _dedup_addressed(extracted + discharge)


def _dedup_addressed(targets: list[AddressedTarget]) -> list[AddressedTarget]:
    """Drop exact (target, form) duplicates while preserving order — the extractor and the
    owes-discharge can both name the same creditor with the same form."""
    seen: set[tuple[str, str]] = set()
    deduped = []
    for target in targets:
        key = (target.target, target.addressed_form)
        if key not in seen:
            seen.add(key)
            deduped.append(target)
    return deduped
