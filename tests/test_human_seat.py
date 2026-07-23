"""The human seat (HITL) contract: opt-in seating, pipeline gating, resume validation, sanitization.

The load-bearing invariant is the FIRST test — an agent-only run never flags a human seat, so
``interrupt()`` never fires in eval/batch runs. The rest guard the human path: it bypasses the memory
pipeline entirely, validates the resumed action against the request, and cleans addressed-targets.
"""

import pytest

from Agents.config import RunConfig, build_runnable_config
from Agents.nodes.orchestrator import initialize_game
from Agents.schemas.game_events import AddressedTarget, DayVote, FiringReason
from Agents.schemas.human_player import HumanTurnRequest, HumanTurnResponse
from Agents.turn import human_turn as h
from Agents.turn import pipeline as pl
from Agents.turn.addressing_agent import _sanitize_against_roster
from Agents.turn.human_turn import HumanTurnContractError, validate_human_response


def _state(**run_kwargs):
    return initialize_game({}, build_runnable_config(RunConfig(game_id="seed-A", **run_kwargs)))


def _human_payload(**over):
    payload = dict(
        player_id="p1", player_role="villager", current_day=1, current_round=1,
        human_player=True, surviving_players=["p1", "p2", "p3"],
        day_channel=[], day_summaries=[], dead_roster=[], cast_role_counts={},
    )
    payload.update(over)
    return payload


def _request(**over):
    base = dict(
        player_id="p1", role="villager", phase="day_votes", day=1, instruction="",
        valid_targets=["p2", "p3"], can_pass=False, dialogue="", day_summaries="",
        surviving_players=["p1", "p2", "p3"], dead_roster="", alive_roles="", firing_brief="",
        wolf_channel="", investigator_results="", vigilante_results="", previous_strategy="",
    )
    base.update(over)
    return HumanTurnRequest(**base)


# ---- opt-in seating -------------------------------------------------------------------------------

def test_agent_only_run_flags_no_human_seat():
    # THE regression guard: default (agent-only) leaves human_player "" so interrupt() never fires.
    assert _state()["human_player"] == ""


def test_human_opt_in_assigns_a_real_seat():
    state = _state(human_player=True)
    assert state["human_player"] in state["roles"]


def test_human_role_preference_lands_on_the_human_seat():
    state = _state(human_player=True, human_role="wolf")
    assert state["roles"][state["human_player"]] == "wolf"


# ---- pipeline gating (no span / retrieval / adoption / EvalCase for a human) ----------------------

def test_day_pipeline_routes_human_before_retrieval(monkeypatch):
    monkeypatch.setattr(pl, "_run_human_decision", lambda payload, output_key: {"routed": output_key})
    monkeypatch.setattr(pl, "enrich_payload_with_memory",
                        lambda *a, **k: pytest.fail("retrieval ran for a human seat"))
    out = pl._run_memory_informed_action(
        _human_payload(), None, None, "day_vote", None, None, "day_votes"
    )
    assert out == {"routed": "day_votes"}


def test_night_pipeline_routes_human_before_retrieval(monkeypatch):
    monkeypatch.setattr(pl, "_run_human_decision", lambda payload, output_key: {"routed": output_key})
    monkeypatch.setattr(pl, "enrich_payload_with_memory",
                        lambda *a, **k: pytest.fail("retrieval ran for a human seat"))
    out = pl._run_memory_informed_night_action(
        _human_payload(human_player=True), None, None, None, None, "healer_target"
    )
    assert out == {"routed": "healer_target"}


def test_agent_seat_does_not_take_the_human_path(monkeypatch):
    # A non-human payload must fall THROUGH the gate into the normal (retrieval) path.
    monkeypatch.setattr(pl, "_run_human_decision",
                        lambda *a, **k: pytest.fail("human path taken for an agent seat"))
    monkeypatch.setattr(pl, "enrich_payload_with_memory",
                        lambda *a, **k: (_ for _ in ()).throw(RuntimeError("reached-retrieval")))
    with pytest.raises(RuntimeError, match="reached-retrieval"):
        pl._run_memory_informed_action(
            _human_payload(human_player=False), None, None, "day_vote", None, None, "day_votes"
        )


# ---- resume validation ----------------------------------------------------------------------------

def test_valid_vote_resumes():
    assert validate_human_response(_request(), {"target": "p2"}).target == "p2"


def test_every_offered_target_is_accepted():
    req = _request(valid_targets=["p2", "p3", "abstain"])
    for t in req.valid_targets:
        assert validate_human_response(req, {"target": t}).target == t


@pytest.mark.parametrize("bad", [{"target": "dead"}, {"target": None}, {"pass_turn": True}])
def test_illegal_or_missing_vote_rejected(bad):
    with pytest.raises(HumanTurnContractError):
        validate_human_response(_request(), bad)


def test_extra_field_rejected():
    with pytest.raises(Exception):  # pydantic ValidationError via extra="forbid"
        validate_human_response(_request(), {"target": "p2", "sneaky": 1})


def test_proactive_pass_ok_reactive_pass_rejected():
    proactive = _request(phase="day_channel", can_pass=True, valid_targets=[])
    assert validate_human_response(proactive, {"pass_turn": True}).pass_turn is True
    reactive = _request(phase="day_channel", can_pass=False, valid_targets=[])
    with pytest.raises(HumanTurnContractError):
        validate_human_response(reactive, {"pass_turn": True})


def test_discussion_message_ok_but_target_forbidden():
    req = _request(phase="day_channel", can_pass=True, valid_targets=[])
    assert validate_human_response(req, {"message": "p2 is quiet"}).message
    with pytest.raises(HumanTurnContractError):
        validate_human_response(req, {"message": "hi", "target": "p2"})


# ---- end-to-end decision path (stubbed interrupt) -------------------------------------------------

def test_human_vote_produces_delta(monkeypatch):
    monkeypatch.setattr(h, "interrupt", lambda req: {"target": "p2"})
    out = h._run_human_decision(_human_payload(), "day_votes")
    assert out == {"day_votes": [DayVote(voter="p1", votee="p2")]}


def test_driver_contract_breach_raises_not_silently_dropped(monkeypatch):
    # An illegal resumed target (driver skipped validation) must raise, never degrade to None.
    monkeypatch.setattr(h, "interrupt", lambda req: {"target": "ghost"})
    with pytest.raises(HumanTurnContractError):
        h._run_human_decision(_human_payload(), "day_votes")


# ---- addressed-target sanitization ----------------------------------------------------------------

def test_sanitize_drops_offroster_and_dedups():
    raw = [
        AddressedTarget(target="p2", addressed_form="question", stance="accusation"),
        AddressedTarget(target="ghost", addressed_form="mention", stance="neutral"),   # invented
        AddressedTarget(target="p1", addressed_form="mention", stance="neutral"),       # self (not in roster)
        AddressedTarget(target="p2", addressed_form="question", stance="neutral"),       # dup (p2,question)
    ]
    out = _sanitize_against_roster(raw, ["p2", "p3"])
    assert [(t.target, t.addressed_form) for t in out] == [("p2", "question")]


def test_extractor_failure_permits_the_human_action(monkeypatch):
    # The extractor fails open: an LLM error yields no addressees, never an exception up the turn.
    from Agents.turn import addressing_agent as aa

    monkeypatch.setattr(aa, "get_llm_extractor", lambda: (_ for _ in ()).throw(RuntimeError("boom")))
    assert aa.extract_addressed_targets("p2 is lying", _human_payload(), 1) == []


def test_reactive_debt_discharged_from_owes(monkeypatch):
    # A reactive human who speaks clears their obligation even if the extractor tags nothing.
    monkeypatch.setattr(h, "extract_addressed_targets", lambda msg, payload, day: [])
    payload = _human_payload(firing_reason=FiringReason(tier="reactive", owes=["p2"]))
    out = h._human_addressed_targets(HumanTurnResponse(message="not me"), payload, "day_channel")
    assert [(t.target, t.addressed_form) for t in out] == [("p2", "response")]
