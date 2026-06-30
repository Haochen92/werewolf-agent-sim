"""Verdict-aware memory-adherence judge for a frozen or replayed decision.

The 3a/3b half of the decision-replay screen — it complements the mechanical
outcome score (``decision_scoring``) and the existing decision-QUALITY judge
(``judges/application.py``, Track 3c). External and OUTCOME-BLIND: the judge sees
only the information set the agent had, the memories actually injected, and the
action taken — never the game result. Per retrieved memory it labels, read
VERDICT-AWARE (a net-negative memory recommends AVOIDING its approach, so
following it means NOT repeating that approach):

  - implied_direction: repeat / avoid / ambiguous
  - action_followed:   followed / contradicted / not_applicable
  - application:        applied / overrode_with_reason / ignored

Rollups (fraction followed, net direction) are computed in code, not asked of
the model. It labels observations now; strategy points slot into the same schema
later (their guidance text is ``action`` rather than approach+outcome). This is a
judge rubric (methodology), not a pipeline prompt — freeze-safe.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from Agents.llm_factory import create_chat_model
from Agents.prompts.prompt_formatters import format_agent_action, format_day_channel
from Agents.schemas.evaluation import EvalCase
from evaluation.src.judges.case_inputs import eval_case_to_judge_inputs

DEFAULT_ADHERENCE_JUDGE_MODEL = "gemini-2.5-pro"


class MemoryAdherence(BaseModel):
    """Adherence labels for ONE retrieved memory at one decision."""

    memory_index: int = Field(
        description="The [N] label of the memory being judged, from the list shown."
    )
    implied_direction: Literal["repeat", "avoid", "ambiguous"] = Field(
        description=(
            "What this memory's lesson recommends for the CURRENT decision, read "
            "verdict-aware: a positive-outcome memory recommends REPEATING its "
            "approach; a negative-outcome memory recommends AVOIDING it; "
            "mixed/unclear is ambiguous."
        )
    )
    action_followed: Literal["followed", "contradicted", "not_applicable"] = Field(
        description=(
            "Did the agent's action move the way implied_direction recommends? "
            "'not_applicable' if this memory's situation does not map onto the "
            "current board."
        )
    )
    application: Literal["applied", "overrode_with_reason", "ignored"] = Field(
        description=(
            "From the agent's stated reasoning ONLY: 'applied' if it used this "
            "memory, 'overrode_with_reason' if it engaged then set it aside with "
            "an explicit reason, 'ignored' if it never engaged it."
        )
    )
    evidence: str = Field(
        description="One short clause grounding the labels, quoting the action/reasoning."
    )


class DecisionAdherence(BaseModel):
    """One adherence row per retrieved memory shown, in order."""

    per_memory: list[MemoryAdherence]


_SYSTEM = """You are an evaluator scoring how a Werewolf agent USED the memories it was given for ONE decision. You judge ONLY adherence — whether the action followed each memory's lesson — never whether the decision was good, and never how the game turned out. You are not told the result; do not speculate about it.

Read each memory VERDICT-AWARE. A memory records a past approach and the outcome it led to:
- Outcome POSITIVE -> the lesson is "repeat this approach" -> implied_direction = repeat.
- Outcome NEGATIVE -> the lesson is "AVOID this approach" -> implied_direction = avoid. Following such a memory means NOT doing what its approach describes.
- Outcome mixed/unclear -> implied_direction = ambiguous.

Then judge the agent's actual action against that direction:
- followed: the action moved the way the lesson recommends (did the approach for 'repeat'; avoided it for 'avoid').
- contradicted: the action moved the opposite way.
- not_applicable: this memory's situation does not map onto the current board, so it gives no direction here.

Finally, from the agent's stated reasoning ONLY, mark whether it applied / overrode_with_reason / ignored the memory. Label every memory shown, one row each, in order."""

_USER = """ROLE: {player_role} | DECISION: {action_phase} (day {day}, round {round})

WHAT THE AGENT COULD SEE
Recent discussion:
{day_channel}

Private context:
{private_context}

Situation summary the agent formed:
{situations}

MEMORIES INJECTED (judge each, by index):
{observations_formatted}

THE AGENT'S ACTION:
{agent_decision}

THE AGENT'S STATED REASONING (its private strategy note after the action):
{agent_updated_strategy}

Label every memory shown above, one row each, in order."""


def judge_decision_adherence(
    case: EvalCase,
    *,
    model: str = DEFAULT_ADHERENCE_JUDGE_MODEL,
    max_retries: int = 1,
) -> DecisionAdherence | None:
    """Label how the (recorded or replayed) action adhered to each injected
    memory. ``case`` must carry the action (agent_vote/agent_message) and
    updated_strategy — for a replay, copy them onto the case first
    (``application_case_for_judge`` does exactly that)."""
    if not case.retrieved_observations:
        return DecisionAdherence(per_memory=[])

    inputs = eval_case_to_judge_inputs(case)
    user = _USER.format(
        player_role=inputs["player_role"],
        action_phase=inputs["action_phase"],
        day=inputs["day"],
        round=inputs["round"],
        day_channel=format_day_channel(case.visible_discussion),
        private_context=inputs["private_context"],
        situations=inputs["situations"],
        observations_formatted=inputs["observations_formatted"],
        agent_decision=format_agent_action(
            case.action_phase, message=case.agent_message, vote=case.agent_vote
        ),
        agent_updated_strategy=case.updated_strategy or "(none)",
    )
    llm = create_chat_model(model).with_structured_output(DecisionAdherence)
    for attempt in range(max_retries + 1):
        try:
            return llm.invoke(
                [
                    {"role": "system", "content": _SYSTEM},
                    {"role": "user", "content": user},
                ],
                config={"run_name": f"adherence_judge_{case.player_role}_day_{case.day}"},
            )
        except Exception as exc:  # noqa: BLE001 - judge is best-effort
            if attempt < max_retries:
                continue
            print(f"  adherence judge failed: {exc}", flush=True)
            return None


class DiscussionStance(BaseModel):
    """Outcome-blind read of one regenerated town discussion turn — the
    anti-aggression probe: did memory make the turn more passive / less likely to
    name a real threat, on the same board?"""

    stance: Literal[
        "drives_suspicion", "supports_suspicion", "passive_or_hedging", "defensive_only"
    ] = Field(
        description=(
            "drives_suspicion: makes a concrete new accusation/read against a "
            "specific player; supports_suspicion: backs an existing accusation; "
            "passive_or_hedging: no concrete read, asks-for-info, or general "
            "caution; defensive_only: only defends self / deflects."
        )
    )
    accused_player: str | None = Field(
        default=None,
        description="The player_id this turn concretely accuses or reads as a threat, if any; else null.",
    )


_STANCE_SYSTEM = """You classify ONE town player's single discussion turn in a Werewolf game. Judge only the turn's STANCE — how assertively it pushes the hunt — never whether it's correct, and you are not told any roles or the outcome.

stance:
- drives_suspicion: makes a concrete NEW accusation or suspicion read against a specific player.
- supports_suspicion: backs/echoes an existing accusation without adding a new target.
- passive_or_hedging: no concrete read — asks for information, counsels caution/patience, or speaks in generalities.
- defensive_only: only defends itself or deflects, no read on anyone else.

accused_player: the exact player_id (e.g. player_4) the turn concretely accuses or reads as a threat, or null if none."""

_STANCE_USER = """Discussion so far (day {day}):
{day_channel}

The turn to classify (spoken by {player_id}):
{message}

Classify this turn's stance and the player it accuses (if any)."""


def judge_discussion_stance(
    message: str,
    day_channel_text: str,
    player_id: str,
    day: int,
    *,
    model: str = "gemini-2.5-flash",
    max_retries: int = 1,
) -> DiscussionStance | None:
    """Classify a regenerated discussion turn's assertiveness (outcome-blind)."""
    if not message or not message.strip():
        return DiscussionStance(stance="passive_or_hedging", accused_player=None)
    user = _STANCE_USER.format(
        day=day, day_channel=day_channel_text, player_id=player_id, message=message
    )
    llm = create_chat_model(model).with_structured_output(DiscussionStance)
    for attempt in range(max_retries + 1):
        try:
            return llm.invoke(
                [
                    {"role": "system", "content": _STANCE_SYSTEM},
                    {"role": "user", "content": user},
                ],
                config={"run_name": f"discussion_stance_{player_id}_day_{day}"},
            )
        except Exception as exc:  # noqa: BLE001 - judge is best-effort
            if attempt < max_retries:
                continue
            print(f"  discussion-stance judge failed: {exc}", flush=True)
            return None


def summarize_adherence(result: DecisionAdherence) -> dict[str, float | int]:
    """Code-side rollups over the per-memory labels (the model is never asked
    for these)."""
    rows = result.per_memory
    applicable = [r for r in rows if r.action_followed != "not_applicable"]
    followed = sum(r.action_followed == "followed" for r in applicable)
    return {
        "n_memories": len(rows),
        "n_applicable": len(applicable),
        "followed_fraction": round(followed / len(applicable), 3) if applicable else None,
        "n_avoid_direction": sum(r.implied_direction == "avoid" for r in rows),
        "n_ignored": sum(r.application == "ignored" for r in rows),
    }
