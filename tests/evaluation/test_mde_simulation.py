"""Guard the power/MDE simulation's two load-bearing pieces: the per-game de-luck scorer factored out
of measure.py (game_score), and the resampling detector's calibration (near-alpha at effect 0, ~100%
on a huge effect). Pure, synthetic fixtures, a couple of cheap resampling cells; the full pool x N x G x
effect sweep is NOT run here."""

import json

import numpy as np

from evaluation.src.instrument_validation.power.mde_simulation import analytic_power, detect_primary
from evaluation.src.loop.measure import game_score

ROLES = {"p_town": "villager", "p_wolf": "wolf"}


def _case(day, role, votee, memory_enabled=True):
    return {"kind": "agent_action_eval", "output": {"eval_case": {
        "day": day, "player_role": role, "action_phase": "day_vote",
        "memory_enabled": memory_enabled, "agent_vote": {"votee": votee}}}}


def _record(tmp_path, cases):
    """A whole-game record dict whose eval_cases_path points at a written cases jsonl.
    villager->wolf vote = +1 (hit threat), villager->town = -1 (mislynch)."""
    ec = tmp_path / "cases.jsonl"
    ec.write_text("\n".join(json.dumps(c) for c in cases))
    return {"roles": ROLES, "eval_cases_path": str(ec), "day_resolutions": []}


def test_game_score_known_mean(tmp_path):
    # Two creditable day-2 town votes: one hits the wolf (+1), one mislynches a townie (-1) -> mean 0.
    rec = _record(tmp_path, [
        _case(1, "villager", "p_wolf"),   # day-1 -> dropped
        _case(2, "villager", "p_wolf"),   # +1
        _case(2, "villager", "p_town"),   # -1
    ])
    sums, ns = game_score(rec, "off")
    assert ns["town"] == 2
    assert sums["town"] == 0.0            # (+1) + (-1)
    assert ns["overall"] == 2

    # Three hits -> mean +1.0.
    rec2 = _record(tmp_path, [_case(2, "villager", "p_wolf") for _ in range(3)])
    s2, n2 = game_score(rec2, "off")
    assert n2["town"] == 3 and s2["town"] / n2["town"] == 1.0


def test_game_score_no_cases_file_is_empty():
    sums, ns = game_score({"roles": ROLES, "eval_cases_path": "/does/not/exist.jsonl"}, "off")
    assert not sums and not ns


def test_detector_high_power_on_huge_effect():
    rng = np.random.default_rng(1)
    pool = np.array([0.0, 0.1, -0.1, 0.2, -0.2, 0.0])  # SD ~0.14
    # A +2.0 total lift over G=10 dwarfs the pool noise -> ~always detected.
    rate = detect_primary(pool, n=20, g=10, total_effect=2.0, rng=rng)
    assert rate > 0.99


def test_analytic_power_hand_checkable_points():
    # Zero effect: detection = P(Z > z_0.975) = 0.025 exactly, at any sd/N/G.
    assert abs(analytic_power(0.3, 4, 6, 0.0) - 0.025) < 1e-9
    # Huge effect: slope/SE explodes -> power ~ 1.
    assert analytic_power(0.3, 20, 10, 2.0) > 0.999
    # Hand-check vs the closed form at the v2-like anchor: sd=0.332, N=4, G=6 ->
    # Sxx = 17.5, SE = 0.332/sqrt(70) ~ 0.0397, slope = 0.15/5 = 0.03,
    # P(Z > 1.96 - 0.756) ~ 0.114.
    assert abs(analytic_power(0.332, 4, 6, 0.15) - 0.114) < 0.005


def test_detector_near_alpha_at_zero_effect():
    rng = np.random.default_rng(2)
    pool = np.array([0.5, -0.5, 0.3, -0.3, 0.0, 0.1, -0.1])
    # Detection = p<0.05 AND slope>0 -> one-directional, so ~2.5% expected (half of two-sided 5%).
    # Scalar resampling is cheap, so the module's default replicate count runs in well under a second.
    rates = [detect_primary(pool, n=n, g=g, total_effect=0.0, rng=rng)
             for n, g in ((4, 6), (10, 8))]
    assert all(r < 0.10 for r in rates)
