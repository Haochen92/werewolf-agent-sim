"""The human seat (HITL) contract: opt-in seating, pipeline gating, resume validation, sanitization.

The load-bearing invariant is the FIRST test — an agent-only run never flags a human seat, so
``interrupt()`` never fires in eval/batch runs. The rest guard the human path: it bypasses the memory
pipeline entirely, validates the resumed action against the request, and cleans addressed-targets.
"""

import pytest

from Agents.config import RunConfig, build_runnable_config
from Agents.nodes.orchestrator import initialize_game
from Agents.schemas.game_events import AddressedTarget, DayChannel, DayVote, FiringReason
from Agents.schemas.human_player import HumanTurnResponse
from Agents.turn import human_turn as h
from Agents.turn import pipeline as pl
from Agents.turn.addressing_agent import _sanitize_against_roster
from Agents.turn.human_turn import HumanTurnContractError, validate_human_response
from tests.factories.builders import human_turn_request as _request


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


# ---- opt-in seating -------------------------------------------------------------------------------

def test_agent_only_run_flags_no_human_seat():
    # THE regression guard: default (agent-only) deals no human seats so interrupt() never fires.
    assert _state()["human_players"] == []


def test_human_opt_in_assigns_a_real_seat():
    state = _state(human_player=True)  # legacy bool call sites coerce to 1 seat
    assert len(state["human_players"]) == 1
    assert state["human_players"][0] in state["roles"]


def test_human_role_preference_lands_on_the_human_seat():
    state = _state(human_player=True, human_role="wolf")
    assert state["roles"][state["human_players"][0]] == "wolf"


def test_multi_human_deals_distinct_seats():
    state = _state(human_player=3)
    seats = state["human_players"]
    assert len(seats) == len(set(seats)) == 3
    assert all(seat in state["roles"] for seat in seats)


def test_extra_humans_do_not_perturb_the_role_draw():
    # The reproducibility contract: seats 2..N draw AFTER the shuffle, so one game_id
    # deals the same cast whether 0, 1, or N humans sit down — and the first human is
    # the same historical pre-shuffle candidate in all of them.
    solo, multi = _state(human_player=1), _state(human_player=3)
    assert _state()["roles"] == solo["roles"] == multi["roles"]
    assert solo["human_players"][0] == multi["human_players"][0]


def test_role_preference_is_ignored_for_multi_human_games():
    # The solo-only rule at the engine root: a shared room always deals random roles.
    assert _state(human_player=2, human_role="wolf")["roles"] == _state()["roles"]


def test_human_seat_count_caps_at_the_cast():
    assert len(_state(human_player=99)["human_players"]) == len(_state()["roles"])


# ---- pipeline gating (no span / retrieval / adoption / EvalCase for a human) ----------------------

def test_day_pipeline_routes_human_before_retrieval(monkeypatch):
    monkeypatch.setattr(pl, "run_human_decision", lambda payload, output_key: {"routed": output_key})
    monkeypatch.setattr(pl, "enrich_payload_with_memory",
                        lambda *a, **k: pytest.fail("retrieval ran for a human seat"))
    out = pl.run_memory_informed_action(
        _human_payload(), None, None, "day_vote", None, None, "day_votes"
    )
    assert out == {"routed": "day_votes"}


def test_night_pipeline_routes_human_before_retrieval(monkeypatch):
    monkeypatch.setattr(pl, "run_human_decision", lambda payload, output_key: {"routed": output_key})
    monkeypatch.setattr(pl, "enrich_payload_with_memory",
                        lambda *a, **k: pytest.fail("retrieval ran for a human seat"))
    out = pl.run_memory_informed_night_action(
        _human_payload(human_player=True), None, None, None, None, "healer_target"
    )
    assert out == {"routed": "healer_target"}


def test_agent_seat_does_not_take_the_human_path(monkeypatch):
    # A non-human payload must fall THROUGH the gate into the normal (retrieval) path.
    monkeypatch.setattr(pl, "run_human_decision",
                        lambda *a, **k: pytest.fail("human path taken for an agent seat"))
    monkeypatch.setattr(pl, "enrich_payload_with_memory",
                        lambda *a, **k: (_ for _ in ()).throw(RuntimeError("reached-retrieval")))
    with pytest.raises(RuntimeError, match="reached-retrieval"):
        pl.run_memory_informed_action(
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


def test_pass_honored_when_offered_rejected_when_not():
    # Every human discussion turn now offers a pass (reactive included — a mention isn't a
    # demand); the validator still hard-rejects a pass against a request that didn't offer one.
    offered = _request(phase="day_channel", can_pass=True, valid_targets=[])
    assert validate_human_response(offered, {"pass_turn": True}).pass_turn is True
    not_offered = _request(phase="day_channel", can_pass=False, valid_targets=[])
    with pytest.raises(HumanTurnContractError):
        validate_human_response(not_offered, {"pass_turn": True})


def test_reactive_request_offers_a_pass():
    payload = _human_payload(firing_reason=FiringReason(tier="reactive", owes=["p2"]))
    request = h._build_human_request(payload, "day_channel", [])
    assert request.can_pass is True


def test_human_reactive_pass_discharges_the_obligation(monkeypatch):
    # A declined reactive turn must close the ledger debt — the pass entry carries synthetic
    # neutral responses to everyone owed, or the scheduler would re-fire the turn forever.
    from Agents.turn.scheduler import build_reactive_queue

    monkeypatch.setattr(h, "interrupt", lambda req: {"pass_turn": True})
    ask = DayChannel(day=1, seq=0, player="p2", message="p1, thoughts?",
                       addressed_targets=[AddressedTarget(
                           target="p1", addressed_form="question", stance="neutral")])
    payload = _human_payload(day_channel=[ask],
                             firing_reason=FiringReason(tier="reactive", owes=["p2"]))
    out = h.run_human_decision(payload, "day_channel")

    entry = out.entry
    assert entry is not None
    assert entry.passed and entry.message == ""
    assert [(t.target, t.addressed_form) for t in entry.addressed_targets] == [("p2", "response")]
    assert build_reactive_queue([ask, entry], per_pair_cap=2, reengagement_cooldown=10,
                                valid_players={"p1", "p2", "p3"}) == []


def test_discussion_message_ok_but_target_forbidden():
    req = _request(phase="day_channel", can_pass=True, valid_targets=[])
    assert validate_human_response(req, {"message": "p2 is quiet"}).message
    with pytest.raises(HumanTurnContractError):
        validate_human_response(req, {"message": "hi", "target": "p2"})


# ---- end-to-end decision path (stubbed interrupt) -------------------------------------------------

def test_human_vote_produces_resolved_turn(monkeypatch):
    monkeypatch.setattr(h, "interrupt", lambda req: {"target": "p2"})
    out = h.run_human_decision(_human_payload(), "day_votes")
    assert out.entry == DayVote(voter="p1", votee="p2")


def test_driver_contract_breach_raises_not_silently_dropped(monkeypatch):
    # An illegal resumed target (driver skipped validation) must raise, never degrade to None.
    monkeypatch.setattr(h, "interrupt", lambda req: {"target": "ghost"})
    with pytest.raises(HumanTurnContractError):
        h.run_human_decision(_human_payload(), "day_votes")


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


# ---- cache/interrupt node split (2026-08-19): humans vote through the UNCACHED twin ----------

def _day_vote_state(human_players):
    return {
        "surviving_villagers": ["p1", "p2"], "surviving_wolves": ["p3"],
        "roles": {"p1": "villager", "p2": "healer", "p3": "wolf"},
        "human_players": human_players, "agent_strategies": {},
        "day_channel": [], "day_summaries": [], "dead_roster": [],
        "current_round": 0, "current_day": 1, "no_lynch_streak": 0,
    }


def test_day_vote_fanout_routes_humans_to_the_uncached_twin():
    from Agents.nodes.day.flow import fan_out_day

    sends = fan_out_day(_day_vote_state(["p2"]), "vote", True)
    assert {(s.node, s.arg["player_id"]) for s in sends} == {
        ("vote", "p1"), ("vote_human", "p2"), ("vote", "p3")}


def test_wolf_vote_fanout_routes_human_wolves_to_the_uncached_twin():
    from Agents.nodes.night.wolf import wolf_fan_out_vote

    state = {
        "surviving_wolves": ["p3", "p4"], "surviving_villagers": ["p1"],
        "human_players": ["p4"], "agent_strategies": {},
        "day_channel": [], "day_summaries": [], "wolf_channel": [],
        "current_day": 1, "current_round": 3,
    }
    sends = wolf_fan_out_vote(state)
    assert {(s.node, s.arg["player_id"]) for s in sends} == {
        ("WOLF_NIGHT_VOTE", "p3"), ("WOLF_NIGHT_VOTE_HUMAN", "p4")}
