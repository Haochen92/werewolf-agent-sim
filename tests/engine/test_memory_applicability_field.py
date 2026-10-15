"""Guard the per-memory applicability field on the decision output schemas.

memory_applicability must (1) exist on every memory-consuming decision output, (2) be ordered BEFORE
the action field (prospective commitment — the action follows the reasoning), and (3) default to an
empty list so memory-off / no-retrieval decisions construct without it. The "one verdict per memory"
instruction lives in the PROMPT BODY (MEMORY_APPLICABILITY_INSTRUCTION), not the field description.
"""

from typing import Literal, get_args, get_origin

import pytest

from Agents.prompts.memory import (
    DAY_DISCUSSION_MEMORY_CONTEXT,
    DAY_VOTE_MEMORY_CONTEXT,
    MEMORY_APPLICABILITY_INSTRUCTION,
    NIGHT_ACTION_MEMORY_CONTEXT,
)
from Agents.schemas.lineup_output import (
    carrier_output,
    day_discuss_output,
    day_vote_output,
    night_output,
    wolf_chat_output,
)
from Agents.schemas.output import MemoryVerdict
from Agents.schemas.roles import ALL_LINEUPS, ROLE_SPECS, roles

LINEUP = ALL_LINEUPS[0]


def _lineup_for(role: str) -> list[str]:
    return next(lineup for lineup in ALL_LINEUPS if role in lineup)


# (schema, the action field memory_applicability must precede): the day turns, the pack's chat
# and kill, and every role's night turn, each filled for a lineup that deals it.
SCHEMAS = [
    (day_vote_output(LINEUP), "vote_target"),
    (day_discuss_output(LINEUP), "pass_turn"),
    (wolf_chat_output(LINEUP), "pass_turn"),
    (carrier_output(LINEUP), "kill_target"),
    *[(night_output(role, _lineup_for(role)), ROLE_SPECS[role].target_field) for role in roles],
]


@pytest.mark.parametrize("schema, action_field", SCHEMAS)
def test_memory_applicability_present_and_before_action(schema, action_field):
    fields = list(schema.model_fields)
    assert "memory_applicability" in fields
    assert fields.index("memory_applicability") < fields.index(action_field), (
        f"{schema.__name__}: memory_applicability must precede {action_field} (prospective commitment)"
    )


@pytest.mark.parametrize("schema, action_field", SCHEMAS)
def test_deliberation_precedes_action(schema, action_field):
    # all deliberation (memory verdicts + the strategy note) is emitted BEFORE the action, so the
    # action follows the reasoning rather than rationalising it (decision-replay reorder finding)
    fields = list(schema.model_fields)
    a = fields.index(action_field)
    assert fields.index("memory_applicability") < a
    assert fields.index("updated_strategy") < a, (
        f"{schema.__name__}: updated_strategy must precede {action_field} (reason-before-act)"
    )


def _minimal_kwargs(schema) -> dict:
    """Dummy values for every REQUIRED field (so we can prove the optional ones default)."""
    out = {}
    for name, f in schema.model_fields.items():
        if not f.is_required():
            continue
        ann = f.annotation
        if ann is bool:
            out[name] = True
        elif get_origin(ann) is list:
            out[name] = []
        elif get_origin(ann) is Literal:
            out[name] = get_args(ann)[0]
        else:
            out[name] = "x"
    return out


@pytest.mark.parametrize("schema, action_field", SCHEMAS)
def test_memory_applicability_defaults_empty(schema, action_field):
    obj = schema(**_minimal_kwargs(schema))
    assert obj.memory_applicability == []


def test_memory_applicability_field_description_is_terse():
    # rich "how" lives in the prompt body, not the model-visible field description
    desc = day_vote_output(LINEUP).model_fields["memory_applicability"].description
    assert desc is not None and len(desc) < 120


def test_instruction_in_every_memory_context_block():
    # the instruction rides the observations block, which every memory context carries
    from Agents.prompts.memory import OBSERVATIONS_BLOCK

    assert MEMORY_APPLICABILITY_INSTRUCTION.strip()[:40] in OBSERVATIONS_BLOCK
    for block in (DAY_VOTE_MEMORY_CONTEXT, DAY_DISCUSSION_MEMORY_CONTEXT):
        assert "{observations_block}" in block
    assert "{night_observations_block}" in NIGHT_ACTION_MEMORY_CONTEXT


def test_memory_verdict_shape():
    v = MemoryVerdict(memory_index=1, verdict="partly_applies", why="x")
    assert v.verdict == "partly_applies"
    with pytest.raises(Exception):
        MemoryVerdict(memory_index=1, verdict="maybe", why="x")  # enum-constrained


def test_eval_case_captures_memory_applicability_and_roundtrips():
    from Agents.schemas.evaluation import EvalCase

    ec = EvalCase(
        player_id="p1", player_role="healer", day=2, round=1,
        action_phase="day_vote", memory_enabled=True,
        memory_applicability=[MemoryVerdict(memory_index=1, verdict="does_not_apply", why="x")],
    )
    dumped = ec.model_dump(mode="json")
    assert dumped["memory_applicability"] == [
        {"memory_index": 1, "verdict": "does_not_apply", "why": "x"}
    ]
    assert EvalCase(**dumped).memory_applicability[0].verdict == "does_not_apply"


def test_resolved_turn_effects_carry_memory_applicability_without_state_keys():
    from Agents.turn import resolve

    verdict = MemoryVerdict(
        memory_index=1,
        verdict="partly_applies",
        why="matches",
    )
    effects = resolve._turn_effects({
        "strategy": "keep pressure",
        "strategy_verdicts": [],
        "memory_verdicts": [verdict],
        "reads": [],
    })

    assert effects.memory_verdicts == [verdict]
    assert "_memory_applicability" not in effects.model_dump()
