"""Net-horizon outcome schema (the v5_0_nethorizon treatment): outcome is COMPOSED net-first from
two required fields, stays OUT of the model's input schema (computed), but remains readable by every
downstream `.outcome` consumer. See evidence/.../paired_ab/nethorizon_design.md."""

import pytest
from pydantic import ValidationError

from Agents.schemas.memory import Observation


def _obs(**kw):
    base = dict(perspective="wolf", action_phase="day_vote", situation="s",
               information_landscape="il", game_phase="mid", approach="voted off-pile",
               impact_on_final_game_outcome="NET NEGATIVE: this vote got me lynched next day",
               immediate_response="it bought survival that turn", net_verdict="negative")
    base.update(kw)
    return Observation(**base)


def test_outcome_is_composed_net_first():
    o = _obs()
    # net effect leads, immediate response trails — the primacy fix.
    assert o.outcome == "NET NEGATIVE: this vote got me lynched next day it bought survival that turn"
    assert o.outcome.startswith("NET NEGATIVE")


def test_immediate_response_empty_drops_cleanly():
    o = _obs(immediate_response="")
    assert o.outcome == "NET NEGATIVE: this vote got me lynched next day"


def test_outcome_excluded_from_model_input_schema_but_in_dump():
    # The leak/treatment boundary: the model is asked for the two halves, never for `outcome`;
    # `outcome` is derived. But model_dump still carries it (back-compat for the store/sidecars).
    props = Observation.model_json_schema()["properties"]
    assert "outcome" not in props
    assert {"impact_on_final_game_outcome", "immediate_response", "net_verdict"} <= set(props)
    assert "outcome" in _obs().model_dump()


def test_net_verdict_is_a_required_enum():
    with pytest.raises(ValidationError):
        _obs(net_verdict="great")  # not in {positive,negative,mixed,unclear}
