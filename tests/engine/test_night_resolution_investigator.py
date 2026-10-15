"""Investigator result-delivery rulings in night_resolution (parallel-night redesign).

All night actors act in one parallel superstep, so the investigator's probe may have
been made by a player who died tonight, or aimed at one. Rulings: delivery is gated on
the investigator surviving (a dead investigator learns nothing); a probe on a same-night
victim IS delivered (fixed truth, redundant with the dawn reveal). The result is the
investigator's own night record ("Suspicious" / "Not suspicious"). The night metric records
the act either way.
"""
from __future__ import annotations

from tests.factories.builders import night_runtime as _runtime

from Agents.nodes.night.resolution import night_resolution
from Agents.schemas.metrics import Metrics
from Agents.schemas.night import NightChoice
from Agents.schemas.roles import lineup

ROLES = {
    "w0": "chanteuse",
    "w1": "illusionist",
    "inv": "investigator",
    "h": "healer",
    "t0": "sentinel",
}


def _state(kill=None, check=None) -> dict:
    """Night state at the barrier: every choice committed by the parallel fan-out."""
    choices = []
    if kill:
        choices.append(NightChoice("w0", "chanteuse", "kill", kill))
    if check:
        choices.append(NightChoice("inv", "investigator", "investigate", check))
    return {
        "current_day": 1,
        "roles": ROLES,
        "lineup": lineup("serial_killer", "speculator"),
        "surviving_wolves": ["w0", "w1"],
        "surviving_villagers": ["inv", "h", "t0"],
        "day_channel": [],
        "night_choices": choices,
    }


def _checks(update) -> list:
    return [r for r in update.get("night_actions", []) if r.action == "investigate"]


def test_result_delivered_when_investigator_survived():
    update = night_resolution(_state(check="w0"), _runtime())
    (result,) = _checks(update)
    assert (result.actor, result.target, result.result) == ("inv", "w0", "suspicious")
    assert result.outcome == "w0 reads Suspicious."


def test_no_delivery_when_investigator_died_tonight():
    update = night_resolution(_state(kill="inv", check="w0"), _runtime())
    assert _checks(update) == []
    assert "inv" not in update["surviving_villagers"]  # the death took the seat out of its bucket


def test_whiffed_probe_on_same_night_victim_still_delivered():
    update = night_resolution(_state(kill="t0", check="t0"), _runtime())
    (result,) = _checks(update)
    assert (result.target, result.result) == ("t0", "not_suspicious")


def test_no_act_no_delivery():
    update = night_resolution(_state(), _runtime())
    assert _checks(update) == []


def test_metric_records_act_even_when_investigator_died():
    metrics = Metrics()
    night_resolution(_state(kill="inv", check="w0"), _runtime(metrics))
    nr = metrics.night_resolutions[-1]
    # the act is on the diagnostic record
    assert {"actor": "inv", "role": "investigator", "kind": "investigate", "target": "w0",
            "via": None, "role_named": None} in nr.choices
    assert nr.deaths == ["inv"]
