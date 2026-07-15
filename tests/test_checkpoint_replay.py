"""Stubbed ($0) coverage for the checkpoint-replay compounding readout.

No real LLM or embedding calls: the decision replay and the snapshot retrieval are
monkeypatched. Covers the leakage guard (trips on overlap / passes clean), the
case-major arm sweep with correct pairing + a hand-checkable McNemar, case-major
ordering (arms adjacent per case), the empty-store arm injecting [], and night
cases scored through the loop's credit lens (credit_backfill._night_credit) with
hand-checkable verdicts (investigator hit, vigilante friendly fire / hold).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from Agents.schemas.evaluation import EvalCase
from evaluation.src.replay.decision_screen import checkpoint_replay as cr


def _case(game_id: str, player_id: str = "player_1", day: int = 2) -> cr._CaseSpec:
    """A minimal town day-vote spec; the frozen query is a non-empty situations list."""
    case = EvalCase(
        player_id=player_id,
        player_role="villager",
        day=day,
        round=1,
        action_phase="day_vote",
        memory_enabled=True,
        situations=[f"situation for {player_id}"],
    )
    game = {
        "game_id": game_id,
        "roles": {"player_1": "villager", "player_2": "wolf"},
        "day_resolutions": [],
    }
    return cr._CaseSpec(case=case, game=game, lens="town")


def _write_snapshot(directory: Path, obs_game_ids: list[str]) -> None:
    """Write a minimal observations.json whose entries carry the given source game_ids."""
    directory.mkdir(parents=True, exist_ok=True)
    payload = {
        "namespaces": {
            "observations/villager/day_vote": [
                {"key": f"k{i}", "value": {"situation": "s", "game_id": gid}}
                for i, gid in enumerate(obs_game_ids)
            ]
        }
    }
    (directory / "observations.json").write_text(json.dumps(payload))
    (directory / "strategy_points.json").write_text(json.dumps({"namespaces": {}}))


# ---------------------------------------------------------------------------
# leakage guard
# ---------------------------------------------------------------------------


def test_leakage_guard_trips_on_overlap():
    specs = [_case("game-A"), _case("game-B", player_id="player_2")]
    snap = cr._Snapshot(
        label="gen1", directory=Path("."), game_ids=frozenset({"game-B", "game-Z"}), store=None
    )
    with pytest.raises(cr.CheckpointLeakageError) as exc:
        cr.assert_no_leakage(specs, [snap])
    assert "game-B" in str(exc.value)
    assert "gen1" in str(exc.value)


def test_leakage_guard_passes_on_clean():
    specs = [_case("game-A"), _case("game-B", player_id="player_2")]
    snap = cr._Snapshot(
        label="gen1", directory=Path("."), game_ids=frozenset({"game-X", "game-Y"}), store=None
    )
    cr.assert_no_leakage(specs, [snap])  # no raise


def test_snapshot_game_ids_reads_observation_provenance(tmp_path):
    _write_snapshot(tmp_path, ["g1", "g2", "g2", ""])  # empty game_id ignored
    assert cr._snapshot_game_ids(tmp_path) == frozenset({"g1", "g2"})


# ---------------------------------------------------------------------------
# arm sweep: pairing + hand-checkable McNemar + empty-arm injection
# ---------------------------------------------------------------------------


def _stub_retrieval_by_arm(monkeypatch, verdicts: dict[str, dict[str, bool]]):
    """Stub retrieval + decision so a case's correctness per arm is fully determined by
    a fixture: verdicts[arm][player_id] -> bool. Records every (case, arm, injected-obs)
    call so ordering + empty-arm injection can be asserted."""
    calls: list[tuple[str, str, int]] = []

    def fake_retrieve(store, case, top_k, keep):
        # a snapshot arm hands the decision a sentinel obs list carrying the arm label
        return [store], []  # store is the arm label string in these tests

    def fake_decide(spec, observations, strategy_points):
        arm = observations[0] if observations else cr.EMPTY_ARM
        calls.append((spec.case.player_id, arm, len(observations)))
        ok = verdicts[arm].get(spec.case.player_id)
        if ok is None:
            return None
        return {"correct": ok, "value": 1.0 if ok else -1.0}

    monkeypatch.setattr(cr, "_retrieve_for_case", fake_retrieve)
    monkeypatch.setattr(cr, "_decide_and_score", fake_decide)
    return calls


def test_sweep_pairs_same_cases_across_arms_and_scores_curve(monkeypatch):
    specs = [_case("game-A", "player_1"), _case("game-B", "player_2")]
    arm_order = [cr.EMPTY_ARM, "gen1", "gen2"]
    stores = {"gen1": "gen1", "gen2": "gen2"}  # store == arm label (see fake_retrieve)
    verdicts = {
        cr.EMPTY_ARM: {"player_1": False, "player_2": False},
        "gen1": {"player_1": True, "player_2": False},
        "gen2": {"player_1": True, "player_2": True},
    }
    _stub_retrieval_by_arm(monkeypatch, verdicts)

    per_case = cr.run_sweep(specs, arm_order, stores, max_workers=1)
    summary = cr.summarize(per_case, arm_order)

    # every arm scored the SAME 2 cases (paired), and the curve rises empty<gen1<gen2
    assert [c["n"] for c in summary["curve"].values()] == [2, 2, 2]
    assert summary["curve"][cr.EMPTY_ARM]["accuracy"] == 0.0
    assert summary["curve"]["gen1"]["accuracy"] == 0.5
    assert summary["curve"]["gen2"]["accuracy"] == 1.0

    # PRIMARY gen-final(gen2) vs gen-1: player_2 flips wrong->right (helped=1), none hurt
    prim = summary["primary_gen_final_vs_gen1"]
    assert (prim["helped"], prim["hurt"]) == (1, 0)
    assert prim["mcnemar_p"] == pytest.approx(1.0)  # exact binomial, m=1 -> 2*0.5

    # SECONDARY empty vs gen1: player_1 flips wrong->right (helped=1)
    sec = summary["secondary_empty_vs_gen1"]
    assert (sec["helped"], sec["hurt"]) == (1, 0)


def _r(correct: bool, value: float | None = None) -> dict:
    """A per-arm result record; value defaults to +1/-1 off correctness."""
    return {"correct": correct, "value": value if value is not None else (1.0 if correct else -1.0)}


def test_mcnemar_hand_fixture_two_sided():
    # 4 discordant: 1 hurt, 3 helped -> two-sided exact p = 2 * P(X<=1 | n=4) = 2*(1+4)/16 = 0.625
    per_case = [
        {"gen1": _r(True), "gen6": _r(False)},   # hurt
        {"gen1": _r(False), "gen6": _r(True)},   # helped
        {"gen1": _r(False), "gen6": _r(True)},   # helped
        {"gen1": _r(False), "gen6": _r(True)},   # helped
        {"gen1": _r(True), "gen6": _r(True)},    # concordant (ignored)
        {"gen1": None, "gen6": _r(True)},        # dropped call (ignored)
    ]
    res = cr._paired_mcnemar(per_case, "gen1", "gen6")
    assert (res["hurt"], res["helped"]) == (1, 3)
    assert res["mcnemar_p"] == pytest.approx(0.625)


def test_sweep_is_case_major_arms_adjacent(monkeypatch):
    specs = [_case("game-A", "player_1"), _case("game-B", "player_2")]
    arm_order = [cr.EMPTY_ARM, "gen1", "gen2"]
    stores = {"gen1": "gen1", "gen2": "gen2"}
    verdicts = {a: {"player_1": True, "player_2": True} for a in arm_order}
    calls = _stub_retrieval_by_arm(monkeypatch, verdicts)

    cr.run_sweep(specs, arm_order, stores, max_workers=1)

    # all three arms of player_1 are contiguous, then all three of player_2 —
    # no interleaving of a snapshot index across the two cases (anti-drift).
    players_in_order = [player for player, _arm, _n in calls]
    assert players_in_order == ["player_1"] * 3 + ["player_2"] * 3
    # and each case visited the arms in arm_order
    arms_first_case = [arm for player, arm, _n in calls if player == "player_1"]
    assert arms_first_case == arm_order


def test_empty_arm_injects_no_retrieved_observations(monkeypatch):
    spec = _case("game-A", "player_1")
    arm_order = [cr.EMPTY_ARM, "gen1"]
    stores = {"gen1": "gen1"}
    verdicts = {cr.EMPTY_ARM: {"player_1": True}, "gen1": {"player_1": True}}
    calls = _stub_retrieval_by_arm(monkeypatch, verdicts)

    cr.run_sweep([spec], arm_order, stores, max_workers=1)

    injected = {arm: n_obs for _player, arm, n_obs in calls}
    assert injected[cr.EMPTY_ARM] == 0   # empty store -> [] injected
    assert injected["gen1"] == 1         # snapshot arm -> retrieved sentinel obs


# ---------------------------------------------------------------------------
# night cases: scored through the loop's credit lens (credit_backfill._night_credit)
# ---------------------------------------------------------------------------

_NIGHT_ROLES = {
    "player_1": "investigator",
    "player_2": "vigilante",
    "player_3": "wolf",
    "player_4": "villager",
}


def _night_case(player_id: str, role: str, game_id: str = "game-N") -> cr._CaseSpec:
    case = EvalCase(
        player_id=player_id,
        player_role=role,
        day=2,
        round=1,
        action_phase="night_action",
        memory_enabled=True,
        situations=[f"night situation for {player_id}"],
    )
    game = {"game_id": game_id, "roles": dict(_NIGHT_ROLES), "day_resolutions": []}
    return cr._CaseSpec(case=case, game=game, lens="night_credit")


def test_town_faction_plan_now_covers_healer_night():
    plans = cr.FACTION_PLANS["town"]
    night = [p for p in plans if p.phase == "night_action"]
    assert len(night) == 1
    # healer is in the town night pool, graded by the loop's own credit lens since its
    # 2026-07-13 promotion into production credit; villager (no night action) stays out.
    assert night[0].roles == frozenset({"investigator", "vigilante", "healer"})
    assert "villager" not in night[0].roles
    assert "healer" in cr.NIGHT_CREDIT_ROLES


def test_night_cases_scored_through_night_credit_in_sweep(monkeypatch):
    """The REAL _decide_and_score + _night_credit run; only the LLM (_replay_night)
    and retrieval are stubbed. Hand-checkable verdicts:
      investigator: empty->villager probe (miss=neutral),  gen1->wolf probe (positive)
      vigilante:    empty->villager shot (friendly fire=NEGATIVE), gen1->hold (neutral)
    """
    specs = [
        _night_case("player_1", "investigator"),
        _night_case("player_2", "vigilante"),
    ]
    arm_order = [cr.EMPTY_ARM, "gen1"]
    stores = {"gen1": object()}
    targets = {  # (player_id, arm) -> regenerated night target
        ("player_1", cr.EMPTY_ARM): "player_4",
        ("player_1", "gen1"): "player_3",
        ("player_2", cr.EMPTY_ARM): "player_4",
        ("player_2", "gen1"): "hold_fire",
    }
    current_arm: dict[str, str] = {}

    def fake_retrieve(store, case, top_k, keep):
        return [], []  # no memory needed; the arm is tracked via the wrapper below

    def tracking_replay_all_arms(spec, arms, sts, top_k, keep):
        # record which arm each _replay_night call belongs to via a per-case shim
        results = {}
        for arm in arms:
            current_arm["arm"] = arm
            obs, sps = ([], []) if arm == cr.EMPTY_ARM else fake_retrieve(sts[arm], spec.case, top_k, keep)
            results[arm] = cr._decide_and_score(spec, obs, sps)
        return results

    def fake_replay_night(case, observations, prompt_template=None, strategy_points=None):
        return targets[(case.player_id, current_arm["arm"])]

    monkeypatch.setattr(cr, "_retrieve_for_case", fake_retrieve)
    monkeypatch.setattr(cr, "_replay_night", fake_replay_night)
    monkeypatch.setattr(cr, "_replay_case_all_arms", tracking_replay_all_arms)

    per_case = cr.run_sweep(specs, arm_order, stores, max_workers=1)
    summary = cr.summarize(per_case, arm_order)

    # per-case verdict mapping: correct only on POSITIVE; value = -1/0/+1
    inv, vig = per_case
    assert inv[cr.EMPTY_ARM] == {"correct": False, "value": 0.0}    # miss -> neutral
    assert inv["gen1"] == {"correct": True, "value": 1.0}           # wolf hit -> positive
    assert vig[cr.EMPTY_ARM] == {"correct": False, "value": -1.0}   # friendly fire -> negative
    assert vig["gen1"] == {"correct": False, "value": 0.0}          # hold -> neutral

    # curve carries BOTH readouts: positive-rate accuracy AND the raw -1/0/+1 mean
    assert summary["curve"][cr.EMPTY_ARM] == {"n": 2, "accuracy": 0.0, "mean_value": -0.5}
    assert summary["curve"]["gen1"] == {"n": 2, "accuracy": 0.5, "mean_value": 0.5}

    # pairing: only the investigator flipped not-correct -> correct (helped=1, hurt=0)
    sec = summary["secondary_empty_vs_gen1"]
    assert (sec["helped"], sec["hurt"]) == (1, 0)


def test_night_replay_failure_excluded_from_pairing(monkeypatch):
    """_replay_night returning None (dropped LLM call) excludes the pair, never
    miscounts as a miss — mirrors the day-vote convention."""
    spec = _night_case("player_1", "investigator")

    monkeypatch.setattr(cr, "_replay_night", lambda *a, **k: None)
    out = cr._decide_and_score(spec, [], [])
    assert out is None


# ---------------------------------------------------------------------------
# healer night: scored through the loop's own _night_credit (healer promoted 2026-07-13)
# off the night_resolutions attack-join. Fixtures run the REAL _decide_and_score; only the
# LLM (_replay_night) is stubbed to a chosen protect target.
# ---------------------------------------------------------------------------

_HEALER_ROLES = {
    "player_1": "healer",
    "player_2": "villager",
    "player_3": "wolf",
    "player_4": "serial_killer",
    "player_5": "investigator",
}


def _healer_case(night_res: dict | None, day: int = 2) -> cr._CaseSpec:
    case = EvalCase(
        player_id="player_1",
        player_role="healer",
        day=day,
        round=1,
        action_phase="night_action",
        memory_enabled=True,
        situations=["night situation for the healer"],
    )
    game = {
        "game_id": "game-H",
        "roles": dict(_HEALER_ROLES),
        "day_resolutions": [],
        "night_resolutions": [night_res] if night_res else [],
    }
    return cr._CaseSpec(case=case, game=game, lens="night_credit")


def _score_healer(monkeypatch, protect: str, night_res: dict | None) -> dict | None:
    monkeypatch.setattr(cr, "_replay_night", lambda *a, **k: protect)
    return cr._decide_and_score(_healer_case(night_res), [], [])


def test_healer_credit_positive_on_predicted_town_save(monkeypatch):
    # wolves were about to kill the villager (player_2); healer protects exactly them.
    nr = {"day": 2, "wolves_target": "player_2", "serial_killer_target": None,
          "vigilante_target": None}
    assert _score_healer(monkeypatch, "player_2", nr) == {"correct": True, "value": 1.0}


def test_healer_credit_positive_on_self_save(monkeypatch):
    # the healer itself was the wolves' target and protected itself -> positive.
    nr = {"day": 2, "wolves_target": "player_1", "serial_killer_target": None,
          "vigilante_target": None}
    assert _score_healer(monkeypatch, "player_1", nr) == {"correct": True, "value": 1.0}


def test_healer_credit_neutral_on_unattacked(monkeypatch):
    # protected the investigator, but only the villager was attacked -> neutral.
    nr = {"day": 2, "wolves_target": "player_2", "serial_killer_target": None,
          "vigilante_target": None}
    assert _score_healer(monkeypatch, "player_5", nr) == {"correct": False, "value": 0.0}


def test_healer_credit_negative_on_shielding_threat(monkeypatch):
    # the SK targeted a wolf (player_3); healer shields that wolf -> negative.
    nr = {"day": 2, "wolves_target": None, "serial_killer_target": "player_3",
          "vigilante_target": None}
    assert _score_healer(monkeypatch, "player_3", nr) == {"correct": False, "value": -1.0}


def test_healer_credit_negative_on_shielding_vig_shot_threat(monkeypatch):
    # a heal blocks vig shots too (verified), so shielding a vig-shot wolf is negative.
    nr = {"day": 2, "wolves_target": None, "serial_killer_target": None,
          "vigilante_target": "player_3"}
    assert _score_healer(monkeypatch, "player_3", nr) == {"correct": False, "value": -1.0}


def test_healer_credit_neutral_on_quiet_night(monkeypatch):
    # no attacks at all this night -> protecting anyone is neutral.
    nr = {"day": 2, "wolves_target": None, "serial_killer_target": None,
          "vigilante_target": None}
    assert _score_healer(monkeypatch, "player_2", nr) == {"correct": False, "value": 0.0}


def test_healer_credit_neutral_on_missing_night_res(monkeypatch):
    # no night_resolutions entry for this day -> degrade to neutral, never crash.
    assert _score_healer(monkeypatch, "player_2", None) == {"correct": False, "value": 0.0}
