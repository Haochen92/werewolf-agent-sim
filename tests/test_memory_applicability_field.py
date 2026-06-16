"""Guard the per-memory applicability field on the decision output schemas.

memory_applicability must (1) exist on every memory-consuming decision output, (2) be ordered BEFORE
the action field (prospective commitment — the action follows the reasoning), and (3) default to an
empty list so memory-off / no-retrieval decisions construct without it. The "one verdict per memory"
instruction lives in the PROMPT BODY (MEMORY_APPLICABILITY_INSTRUCTION), not the field description.
"""

import pytest

from Agents.prompts.memory import (
    DAY_DISCUSSION_MEMORY_CONTEXT,
    DAY_VOTE_MEMORY_CONTEXT,
    MEMORY_APPLICABILITY_INSTRUCTION,
    NIGHT_ACTION_MEMORY_CONTEXT,
)
from Agents.schemas.output import (
    DayDiscussOutput,
    DayVoteOutput,
    HealerOutput,
    InvestigatorOutput,
    MemoryVerdict,
    SerialKillerOutput,
    VigilanteOutput,
    WolfNightDiscussOutput,
)

# (schema, the action field memory_applicability must precede)
SCHEMAS = [
    (DayVoteOutput, "vote_target"),
    (DayDiscussOutput, "pass_turn"),
    (HealerOutput, "healer_target"),
    (InvestigatorOutput, "investigator_target"),
    (SerialKillerOutput, "serial_killer_target"),
    (VigilanteOutput, "vigilante_target"),
    (WolfNightDiscussOutput, "message"),
]


@pytest.mark.parametrize("schema, action_field", SCHEMAS)
def test_memory_applicability_present_and_before_action(schema, action_field):
    fields = list(schema.model_fields)
    assert "memory_applicability" in fields
    assert fields.index("memory_applicability") < fields.index(action_field), (
        f"{schema.__name__}: memory_applicability must precede {action_field} (prospective commitment)"
    )


def _minimal_kwargs(schema) -> dict:
    """Dummy values for every REQUIRED field (so we can prove the optional ones default)."""
    out = {}
    for name, f in schema.model_fields.items():
        if not f.is_required():
            continue
        ann = f.annotation
        out[name] = True if ann is bool else ([] if getattr(ann, "__origin__", None) is list else "x")
    return out


@pytest.mark.parametrize("schema, action_field", SCHEMAS)
def test_memory_applicability_defaults_empty(schema, action_field):
    obj = schema(**_minimal_kwargs(schema))
    assert obj.memory_applicability == []


def test_memory_applicability_field_description_is_terse():
    # rich "how" lives in the prompt body, not the model-visible field description
    desc = DayVoteOutput.model_fields["memory_applicability"].description
    assert desc is not None and len(desc) < 120


def test_instruction_in_every_memory_context_block():
    snippet = MEMORY_APPLICABILITY_INSTRUCTION.strip()[:40]
    for block in (DAY_VOTE_MEMORY_CONTEXT, DAY_DISCUSSION_MEMORY_CONTEXT, NIGHT_ACTION_MEMORY_CONTEXT):
        assert snippet in block


def test_memory_verdict_shape():
    v = MemoryVerdict(memory_index=1, verdict="partly_applies", why="x")
    assert v.verdict == "partly_applies"
    with pytest.raises(Exception):
        MemoryVerdict(memory_index=1, verdict="maybe", why="x")  # enum-constrained
