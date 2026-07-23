"""Per-player suspicion "reads" bundle (T1c ship, 2026-07-09).

A validated decision-replay A/B promoted a reads bundle into the live pipeline: an "alive roles" line
+ a forced per-player suspicion list emitted in the structured output BEFORE the free-text strategy
note (verdicts -> reads -> strategy -> action). These tests pin the load-bearing surfaces: (1) the
schema field ORDER (the tested commitment lever); (2) legacy EvalCase records without reads still
load; (3) the dynamic target-enum rewrite preserves the required reads field; (4) the alive-roles
formatter (subtraction, fixed order, no pluralization, empty/none edges); (5) the derived
read_targets + alive_roles prompt keys (incl. the wolf payload shape); (6) the completeness tripwire
(monitor-only, never retried); (7) the reads leak check; (8) every changed template still renders.
"""
from __future__ import annotations

import logging

from langchain_core.runnables import RunnableLambda

from Agents.prompts.day_discuss import VILLAGER_DAY_DISCUSS
from Agents.prompts.day_vote import VILLAGER_DAY_VOTE
from Agents.prompts.night import HEALER_NIGHT
from Agents.prompts.prompt_formatters import format_alive_roles
from Agents.prompts.prompt_inputs import build_agent_prompt_input
from Agents.schemas.evaluation import EvalCase
from Agents.schemas.game_events import DeathRecord
from Agents.schemas.output import (
    DayDiscussOutput,
    DayVoteOutput,
    HealerOutput,
    PlayerRead,
)
from Agents.schemas.roles import cast_role_counts
from Agents.turn import agent_player as agent_mod
from Agents.turn.action_space import _output_schema_with_legal_targets
from Agents.turn.eval import _build_eval_private_context, _reads_coverage
from tests.leak_test import check_reads_isolation


_FULL_CAST = {
    "villager": 3, "wolf": 2, "healer": 1, "investigator": 1, "vigilante": 1, "serial_killer": 1,
}


# --- (1) schema field order = the tested commitment lever -------------------

def test_field_order_reads_between_verdicts_and_strategy():
    fields = list(DayDiscussOutput.model_fields)
    core = [f for f in fields if f in {
        "strategy_verdicts", "memory_applicability", "reads", "updated_strategy"}]
    assert core == ["strategy_verdicts", "memory_applicability", "reads", "updated_strategy"]
    # Action fields come AFTER the strategy note.
    assert fields.index("updated_strategy") < fields.index("pass_turn")
    assert fields.index("updated_strategy") < fields.index("message")


def test_field_order_on_healer_output():
    fields = list(HealerOutput.model_fields)
    assert fields.index("memory_applicability") < fields.index("reads")
    assert fields.index("reads") < fields.index("updated_strategy")
    assert fields.index("updated_strategy") < fields.index("healer_target")


# --- (2) legacy EvalCase records (pre-reads) still load ----------------------

def test_eval_case_loads_without_reads():
    minimal = {
        "player_id": "player_1", "player_role": "villager", "day": 1, "round": 0,
        "action_phase": "day_vote", "memory_enabled": False,
    }
    case = EvalCase.model_validate(minimal)
    assert case.reads == []


# --- (3) dynamic target-enum rewrite keeps reads (required) ------------------

def test_dynamic_target_enum_preserves_required_reads():
    schema = _output_schema_with_legal_targets(
        DayVoteOutput, "day_votes", ["player_1", "player_2", "abstain"]
    )
    assert "reads" in schema.model_fields
    assert schema.model_fields["reads"].is_required()


# --- (4) format_alive_roles: subtraction, fixed order, edges -----------------

def test_format_alive_roles_full_cast_fixed_order():
    line = format_alive_roles(_FULL_CAST, [])
    assert line == "2 wolf, 1 serial killer, 1 healer, 1 investigator, 1 vigilante, 3 villager"
    # No pluralization (matches the tested study text).
    assert "villagers" not in line and "wolves" not in line


def test_format_alive_roles_subtracts_revealed_dead():
    roster = [
        DeathRecord(player="player_2", role="villager", day=1, phase="night"),
        DeathRecord(player="player_5", role="wolf", day=2, phase="day"),
    ]
    assert format_alive_roles(_FULL_CAST, roster) == (
        "1 wolf, 1 serial killer, 1 healer, 1 investigator, 1 vigilante, 2 villager"
    )


def test_format_alive_roles_empty_census_returns_blank():
    assert format_alive_roles({}, []) == ""


def test_format_alive_roles_all_dead_returns_none():
    roster = [DeathRecord(player="p", role="villager", day=1, phase="night")]
    assert format_alive_roles({"villager": 1}, roster) == "none"


# --- (5) build_agent_prompt_input: read_targets + alive_roles ----------------

def test_read_targets_excludes_self():
    pi = build_agent_prompt_input({
        "player_id": "player_1", "player_role": "villager", "current_day": 2,
        "surviving_players": ["player_1", "player_3", "player_4"],
        "cast_role_counts": _FULL_CAST,
    })
    assert pi["read_targets"] == "player_3, player_4"
    assert pi["alive_roles"].startswith("2 wolf")


def test_read_targets_wolf_payload_shape():
    # Wolf day payload splits survivors into wolves + villagers (no surviving_players key).
    pi = build_agent_prompt_input({
        "player_id": "player_1", "player_role": "wolf", "current_day": 2,
        "surviving_wolves": ["player_1", "player_2"],
        "surviving_villagers": ["player_3", "player_4"],
        "cast_role_counts": _FULL_CAST,
    })
    assert pi["read_targets"] == "player_2, player_3, player_4"


# --- (6) completeness tripwire: monitor-only, never retried ------------------

def test_reads_coverage_helper():
    payload = {"player_id": "player_1", "surviving_players": [f"player_{i}" for i in range(1, 9)]}
    reads = [PlayerRead(player=f"player_{i}", why="unchanged", suspected_role="unclear",
                        confidence="low") for i in range(2, 7)]  # covers 5 of 7 non-self
    coverage, missing = _reads_coverage(reads, payload)
    assert missing == ["player_7", "player_8"]
    assert coverage == 5 / 7


def test_reads_coverage_full_and_wolf_shape():
    # Full coverage -> 1.0, no missing.
    payload = {"player_id": "player_1", "surviving_players": ["player_1", "player_2", "player_3"]}
    reads = [PlayerRead(player="player_2", why="unchanged", suspected_role="unclear", confidence="low"),
             PlayerRead(player="player_3", why="unchanged", suspected_role="unclear", confidence="low")]
    assert _reads_coverage(reads, payload) == (1.0, [])
    # Wolf-shaped payload (wolves + villagers, no surviving_players) enumerates the same way.
    wolf_payload = {"player_id": "player_1", "surviving_wolves": ["player_1", "player_2"],
                    "surviving_villagers": ["player_3"]}
    coverage, missing = _reads_coverage([], wolf_payload)
    assert coverage == 0.0 and missing == ["player_2", "player_3"]


class _FakeLLM:
    """Stand-in for get_llm(): with_structured_output returns a runnable that ignores its input and
    yields a canned decision, so _run_agent exercises the tripwire branch without a real model call."""

    def __init__(self, result):
        self._result = result

    def with_structured_output(self, _schema):
        return RunnableLambda(lambda _input: self._result)


def _healer_payload():
    return {
        "player_id": "player_1", "player_role": "healer", "current_day": 2,
        "surviving_players": [f"player_{i}" for i in range(2, 10)],  # 8 targets, self excluded
        "dead_roster": [], "cast_role_counts": _FULL_CAST,
    }


def _healer_result(read_players):
    return HealerOutput(
        strategy_verdicts=[], memory_applicability=[],
        reads=[PlayerRead(player=p, why=f"a distinct read reason about {p}",
                          suspected_role="unclear", confidence="low") for p in read_players],
        updated_strategy="", healer_target="player_3",
    )


def test_tripwire_warns_on_undercoverage(monkeypatch, caplog):
    payload = _healer_payload()
    result = _healer_result([f"player_{i}" for i in range(2, 8)])  # 6 of 8 -> 0.75
    monkeypatch.setattr(agent_mod, "get_llm", lambda: _FakeLLM(result))
    with caplog.at_level(logging.WARNING, logger="Agents.turn.eval"):
        out = agent_mod._run_agent(payload, HEALER_NIGHT, HealerOutput, "healer_target")
    assert out["healer_target"] == "player_3"
    assert "reads under-covered" in caplog.text
    assert "player_8" in caplog.text and "player_9" in caplog.text


def test_tripwire_silent_on_full_coverage(monkeypatch, caplog):
    payload = _healer_payload()
    result = _healer_result(payload["surviving_players"])  # all 8
    monkeypatch.setattr(agent_mod, "get_llm", lambda: _FakeLLM(result))
    with caplog.at_level(logging.WARNING, logger="Agents.turn.eval"):
        agent_mod._run_agent(payload, HEALER_NIGHT, HealerOutput, "healer_target")
    assert "reads under-covered" not in caplog.text


# --- (7) check_reads_isolation: private reads never reach ANOTHER prompt -----

def _log(prompt_input: dict, player: str = "player_3") -> list[dict]:
    return [{"player_id": player, "player_role": "villager", "prompt_input": prompt_input}]


def _reads_of(author: str, why: str) -> list[dict]:
    return [{"player_id": author, "reads": [{"player": "player_9", "why": why,
                                             "suspected_role": "wolf", "confidence": "low"}]}]


_LONG_WHY = "pushed the only counted lynch with no evidence and flipped after the reveal"


def test_check_reads_isolation_structural_pass_flags_rendered_objects():
    # A rendered read OBJECT in any prompt_input is the realistic regression — token-detected.
    leaked = _log({"memory_block": "[{'player': 'player_9', 'suspected_role': 'wolf'}]"})
    assert check_reads_isolation(leaked, [])
    leaked = _log({"context": '{"reads": [{"player": "player_9"}]}'})
    assert check_reads_isolation(leaked, [])
    assert check_reads_isolation(_log({"day_channel": "plain talk"}), []) == []


def test_check_reads_isolation_flags_long_why_in_other_prompt():
    leaked = _log({"day_channel": f"player_2: {_LONG_WHY}"}, player="player_3")
    assert check_reads_isolation(leaked, _reads_of("player_1", _LONG_WHY))


def test_check_reads_isolation_author_own_prompt_exempt():
    # The author's own strategy note legitimately echoes its own reads (2026-07-09 smoke FP class).
    own = _log({"previous_strategy": _LONG_WHY}, player="player_1")
    assert check_reads_isolation(own, _reads_of("player_1", _LONG_WHY)) == []


def test_check_reads_isolation_shared_vocabulary_not_attributable():
    # Short generic whys ("confirmed healer") and whys echoed in the public channel were the
    # 2026-07-09 smoke's false positives — both are excluded from the prose pass.
    generic = _log({"day_channel": "player_4 is a confirmed healer"})
    assert check_reads_isolation(generic, _reads_of("player_1", "confirmed healer")) == []
    public = _log({"day_channel": f"player_2: {_LONG_WHY}"})
    assert check_reads_isolation(
        public, _reads_of("player_1", _LONG_WHY), public_text=f"someone said || {_LONG_WHY}"
    ) == []


# --- (8) every changed template renders with the new keys -------------------

def _render_payload() -> dict:
    return build_agent_prompt_input({
        "player_id": "player_1", "player_role": "villager", "current_day": 2,
        "surviving_players": ["player_1", "player_3", "player_4"],
        "dead_roster": [DeathRecord(player="player_2", role="villager", day=1, phase="night")],
        "cast_role_counts": _FULL_CAST,
    })


def test_changed_templates_render():
    pi = _render_payload()
    for tpl in (VILLAGER_DAY_DISCUSS, VILLAGER_DAY_VOTE, HEALER_NIGHT):
        rendered = tpl.invoke(pi).to_string()
        assert "record your current read" in rendered  # reads instruction present
        assert "Roles still in play" in rendered        # alive-roles block present
        assert "player_3, player_4" in rendered          # read_targets enumerated


# --- (9) the shared census helper: counts only, no identities ----------------

def test_cast_role_counts_is_name_free():
    role_map = {"player_1": "wolf", "player_2": "wolf", "player_3": "villager"}
    counts = cast_role_counts(role_map)
    assert counts == {"wolf": 2, "villager": 1}
    # The payload-safe invariant: no player identity survives the census.
    assert not set(counts) & set(role_map)


# --- (10) the EvalCase captures the board inputs the turn saw ----------------

def test_eval_private_context_captures_board_inputs():
    roster = [DeathRecord(player="player_2", role="villager", day=1, phase="night")]
    ctx = _build_eval_private_context(
        {**_healer_payload(), "dead_roster": roster}, day=2,
    )
    assert ctx.dead_roster == roster
    assert ctx.cast_role_counts == _FULL_CAST
    # Legacy payloads (pre-board) still snapshot cleanly with empty defaults.
    legacy = _build_eval_private_context({"player_id": "player_1"}, day=1)
    assert legacy.dead_roster == [] and legacy.cast_role_counts == {}


def test_check_reads_isolation_recipient_own_strategy_convergence_exempt():
    """Regression (2026-07-17 v7 run false-halt): a RECIPIENT's own strategy note independently
    phrased a public event identically to another player's read why ("abstained during the serial
    killer lynch", exactly the 40-char floor). Recipient-authored prose (previous_strategy) is
    convergence, not receipt — excluded from the prose pass. The same needle in any OTHER field
    still leaks, and a rendered read object in previous_strategy still trips the structural pass."""
    needle = "abstained during the serial killer lynch"
    convergent = _log({"previous_strategy": f"Focus scrutiny on the players who {needle}, as they"},
                      player="player_4")
    assert check_reads_isolation(convergent, _reads_of("player_9", needle)) == []
    foreign = _log({"day_summaries": f"note: {needle}"}, player="player_4")
    assert check_reads_isolation(foreign, _reads_of("player_9", needle))
    rendered = _log({"previous_strategy": "[{'player': 'p9', 'suspected_role': 'wolf'}]"},
                    player="player_4")
    assert check_reads_isolation(rendered, _reads_of("player_9", needle))
