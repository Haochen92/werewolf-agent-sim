"""Investigator result-delivery rulings in night_resolution (parallel-night redesign).

All night actors act in one parallel superstep, so the investigator's probe may have
been made by a player who died tonight, or aimed at one. Rulings: delivery is gated on
the investigator surviving (a dead investigator learns nothing); a probe on a same-night
victim IS delivered (fixed truth, redundant with the dawn reveal). The night metric
records the act either way.
"""
from __future__ import annotations

from types import SimpleNamespace

from Agents.nodes.night.resolution import night_resolution
from Agents.schemas.metrics import Metrics

ROLES = {
    "w0": "wolf",
    "w1": "wolf",
    "inv": "investigator",
    "h": "healer",
    "t0": "villager",
}


def _runtime(metrics: Metrics | None = None) -> SimpleNamespace:
    return SimpleNamespace(context={"metrics": metrics or Metrics()})


def _state(**overrides) -> dict:
    """Night state at the barrier: all targets committed by the parallel fan-out."""
    s = {
        "current_day": 1,
        "roles": ROLES,
        "surviving_wolves": ["w0", "w1"],
        "surviving_villagers": ["inv", "h", "t0"],
        "healer_player": "h",
        "investigator_player": "inv",
        "serial_killer_player": None,
        "vigilante_player": None,
        "day_channel": [],
        "wolves_kill_target": None,
        "healer_target": None,
        "serial_killer_target": None,
        "vigilante_target": None,
        "investigator_target": None,
    }
    s.update(overrides)
    return s


def test_result_delivered_when_investigator_survived():
    update = night_resolution(_state(investigator_target="w0"), _runtime())
    (result,) = update["investigator_results"]
    assert result.player_investigated == "w0"
    assert result.role_revealed == "wolf"


def test_no_delivery_when_investigator_died_tonight():
    update = night_resolution(
        _state(wolves_kill_target="inv", investigator_target="w0"), _runtime()
    )
    assert "investigator_results" not in update
    assert update["investigator_player"] is None  # marker cleared by the death


def test_whiffed_probe_on_same_night_victim_still_delivered():
    update = night_resolution(
        _state(wolves_kill_target="t0", investigator_target="t0"), _runtime()
    )
    (result,) = update["investigator_results"]
    assert result.player_investigated == "t0"
    assert result.role_revealed == "villager"


def test_no_act_no_delivery():
    update = night_resolution(_state(), _runtime())
    assert "investigator_results" not in update


def test_metric_records_act_even_when_investigator_died():
    metrics = Metrics()
    night_resolution(
        _state(wolves_kill_target="inv", investigator_target="w0"), _runtime(metrics)
    )
    nr = metrics.night_resolutions[-1]
    assert nr.investigator_target == "w0"  # the act is on the diagnostic record
    assert nr.investigator_target_role == "wolf"
    assert nr.deaths == ["inv"]
