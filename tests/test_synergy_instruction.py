"""Guard the combined-arm synergy instruction: data-driven (fires ONLY when both memory types are
present), absent in obs-only / sp-only arms, and wired into every memory-context template."""

from Agents.prompts.prompt_inputs import _retrieved_present, build_agent_prompt_input
from Agents.prompts.memory import (
    DAY_DISCUSSION_MEMORY_CONTEXT,
    DAY_VOTE_MEMORY_CONTEXT,
    NIGHT_ACTION_MEMORY_CONTEXT,
    OBS_STRATEGY_SYNERGY_INSTRUCTION,
)

_OBS_SENTINEL = "No past observations available."
_SP_SENTINEL = "No dynamic strategy points available."


def test_retrieved_present_logic():
    assert _retrieved_present(["x"]) and not _retrieved_present([])
    assert not _retrieved_present(_OBS_SENTINEL) and not _retrieved_present(_SP_SENTINEL)
    assert _retrieved_present("[1] a real formatted memory")
    assert not _retrieved_present("") and not _retrieved_present("   ")


def _synergy(obs, sp):
    # strings flow through build_agent_prompt_input unchanged (the isinstance-str fast path)
    return build_agent_prompt_input(
        {"player_role": "wolf", "retrieved_observations": obs, "strategy_points": sp}
    )["synergy_instruction"]


def test_synergy_fires_only_when_both_present():
    assert _synergy("[1] obs", "[1] sp").strip()          # both → fires
    assert _synergy("[1] obs", _SP_SENTINEL) == ""        # sp absent → empty
    assert _synergy(_OBS_SENTINEL, "[1] sp") == ""        # obs absent → empty
    assert _synergy(_OBS_SENTINEL, _SP_SENTINEL) == ""    # neither → empty


def test_slot_in_every_memory_context_template():
    for template in (DAY_VOTE_MEMORY_CONTEXT, NIGHT_ACTION_MEMORY_CONTEXT, DAY_DISCUSSION_MEMORY_CONTEXT):
        assert "{synergy_instruction}" in template


def test_synergy_text_points_to_override():
    # the synergy lesson must route an obs-contradicted strategy to `override`, not blind follow
    assert "override" in OBS_STRATEGY_SYNERGY_INSTRUCTION
    assert "cross-check" in OBS_STRATEGY_SYNERGY_INSTRUCTION.lower()
