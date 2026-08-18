"""The HITL resume driver: retry-until-valid collection, CLI action parsing, menu resolution.

The driver's contract: only a response that passes ``validate_human_response`` escapes
``collect_human_response``; a rejected attempt re-prompts with the validator's error and the SAME
request (no graph involvement); exhaustion aborts loudly. The CLI transport stays dumb — it returns
raw dicts and passes typos through for the validator to judge.
"""

import builtins

import pytest

from Agents.driver import hitl_loop
from Agents.driver.hitl_loop import MAX_ATTEMPTS, _resolve_target, _send_request, collect_human_response
from tests.factories.builders import human_turn_request as _request


def _feed_inputs(monkeypatch, answers):
    it = iter(answers)
    monkeypatch.setattr(builtins, "input", lambda prompt="": next(it))


# ---- collect_human_response: the retry loop -------------------------------------------------------

def test_valid_first_attempt_returns_validated_response(monkeypatch):
    monkeypatch.setattr(hitl_loop, "_send_request", lambda req, err: {"target": "p2"})
    assert collect_human_response(_request()).target == "p2"


def test_invalid_attempt_reprompts_with_the_validator_error(monkeypatch):
    seen_errs = []

    def scripted(req, err):
        seen_errs.append(err)
        return {"target": "ghost"} if len(seen_errs) == 1 else {"target": "p3"}

    monkeypatch.setattr(hitl_loop, "_send_request", scripted)
    assert collect_human_response(_request()).target == "p3"
    assert seen_errs[0] is None
    assert "ghost" in seen_errs[1]  # the validator's message, surfaced to the human


def test_exhaustion_aborts_loudly(monkeypatch):
    calls = []
    monkeypatch.setattr(hitl_loop, "_send_request", lambda req, err: calls.append(1) or {"target": "ghost"})
    with pytest.raises(RuntimeError, match="failed to receive"):
        collect_human_response(_request())
    assert len(calls) == MAX_ATTEMPTS


# ---- _send_request: CLI action parsing (raw dicts, no judgment) -----------------------------------

def test_cli_vote_by_menu_number(monkeypatch):
    _feed_inputs(monkeypatch, ["1"])
    assert _send_request(_request(), None) == {"target": "p2"}


def test_cli_discussion_message_and_pass(monkeypatch):
    req = _request(phase="day_channel", can_pass=True, valid_targets=[])
    _feed_inputs(monkeypatch, ["p2 is too quiet"])
    assert _send_request(req, None) == {"message": "p2 is too quiet"}
    _feed_inputs(monkeypatch, ["pass"])
    assert _send_request(req, None) == {"pass_turn": True}


def test_cli_reactive_turn_takes_pass_as_literal_text(monkeypatch):
    # can_pass=False: "pass" is not an escape hatch, it's a (weird) message for the validator to see.
    _feed_inputs(monkeypatch, ["pass"])
    out = _send_request(_request(phase="day_channel", can_pass=False, valid_targets=[]), None)
    assert out == {"message": "pass"}


def test_cli_wolf_talk_is_message_only(monkeypatch):
    # Sequential-talk wolf night: the talk turn collects no target — the vote is its own turn.
    req = _request(phase="wolf_channel", valid_targets=[])
    _feed_inputs(monkeypatch, ["take p3 tonight"])
    assert _send_request(req, None) == {"message": "take p3 tonight"}


def test_cli_wolf_vote_uses_the_generic_target_path(monkeypatch):
    req = _request(phase="wolf_vote", valid_targets=["p2", "p3"])
    _feed_inputs(monkeypatch, ["2"])
    assert _send_request(req, None) == {"target": "p3"}


# ---- _resolve_target: menu numbers resolve, everything else passes through ------------------------

@pytest.mark.parametrize("raw,expected", [
    ("1", "p2"),        # menu number -> target
    ("2", "abstain"),   # sentinel offered like any target
    ("p2", "p2"),       # name passes through
    ("0", "0"),         # out-of-range number passes through for the validator to reject
    ("7", "7"),
    ("ghost", "ghost"), # typo passes through — validator is the judge
])
def test_resolve_target(raw, expected):
    assert _resolve_target(raw, ["p2", "abstain"]) == expected
