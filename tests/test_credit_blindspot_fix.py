"""Blind-spot fix pair (evidence/credit/blindspot_fix/): the contextual abstain rule and the
find→lynch conversion channel — plus the freeze guards that keep every pre-registered instrument on
the legacy grading.

$0 / fully deterministic. The two properties that must never regress:
(a) FROZEN DEFAULT — _vote_credit/_decision_credit/compute_base_rates called WITHOUT the new keywords
    (measure.py, the instrument_validation runners) grade abstains neutral, byte-identical to the
    pre-knob behavior. The knob is ledger-only by construction.
(b) BASELINE COHERENCE — the deadlock_negative base rates are computed by the same rule as the ledger
    (credit_apply threads one value into both), and the conversion base rides the same construct as
    the conversion ledger.
"""

from __future__ import annotations

import json
from pathlib import Path

from evaluation.src.loop.config import LoopConfig
from evaluation.src.loop.consolidate import prune_and_evict
from evaluation.src.loop.conversion_credit import (
    CONVERSION_CHANNEL, conversion_apply, conversion_base, conversion_ledger, conversion_lift,
    find_outcomes,
)
from evaluation.src.loop.credit import credit_apply
from evaluation.src.loop.credit_backfill import (
    _decision_credit, _town_abstain_credit, _vote_credit, compute_base_rates,
)
from evaluation.src.loop.measure import game_score

ROLES = {"player_1": "villager", "player_2": "wolf", "player_3": "villager",
         "player_4": "investigator", "player_5": "serial_killer"}

NO_LYNCH = {"day": 2, "no_vote": True, "voted_player": None, "vote_counts": {}}
LYNCHED_TOWN = {"day": 2, "no_vote": False, "voted_player": "player_3",
                "voted_player_role": "villager", "vote_counts": {"player_3": 4}}
LYNCHED_THREAT = {"day": 2, "no_vote": False, "voted_player": "player_2",
                  "voted_player_role": "wolf", "vote_counts": {"player_2": 4}}


def _ec(case: dict) -> dict:
    return {"kind": "agent_action_eval", "output": {"eval_case": case}}


def _game(tmp: Path, name: str, cases: list, *, roles: dict, day_res=None, night_res=None) -> str:
    ecp = tmp / f"{name}_cases.jsonl"
    ecp.write_text("\n".join(json.dumps(_ec(c)) for c in cases))
    rec = {"roles": roles, "eval_cases_path": str(ecp), "game_id": f"gid_{name}"}
    if day_res is not None:
        rec["day_resolutions"] = day_res
    if night_res is not None:
        rec["night_resolutions"] = night_res
    gp = tmp / f"{name}.jsonl"
    gp.write_text(json.dumps(rec))
    return str(gp)


def _vote_case(role, pid, votee, key=None, day=2, mem=True):
    c = {"action_phase": "day_vote", "player_role": role, "player_id": pid, "day": day,
         "memory_enabled": mem, "agent_vote": {"votee": votee}}
    if key:
        c["strategy_index_to_key"] = {"0": key}
        c["strategy_verdicts"] = [{"verdict": "follow", "strategy_index": 0}]
    return c


def _sp(key, cell="villager/day_vote", **counts):
    v = {"action": key, "follow_count": 0, "positive_count": 0, "negative_count": 0,
         "neutral_count": 0, "retrieved_count": 0, "override_count": 0, "not_relevant_count": 0}
    v.update(counts)
    return {"key": key, "value": v, "namespace": ["strategy_points", *cell.split("/")]}


# --- (a) the frozen default: no keyword => legacy neutral, everywhere -------------------------------

def test_default_abstain_stays_neutral_regardless_of_day_outcome():
    for day_res in (NO_LYNCH, LYNCHED_TOWN, LYNCHED_THREAT, None):
        assert _vote_credit("villager", "abstain", ROLES) == "neutral"
        ec = _vote_case("villager", "player_1", "abstain")
        assert _decision_credit(ec, ROLES, None, None) == "neutral"  # measure.py's exact call shape
        del day_res  # the point: the default path never even sees the resolution row


def test_measure_is_pinned_to_the_legacy_rule(tmp_path):
    """game_score on an abstain-heavy record is identical whatever LoopConfig.abstain_credit says —
    the pre-registered proxy cannot move underneath a run that flips the knob."""
    cases = [_vote_case("villager", "player_1", "abstain"),
             _vote_case("villager", "player_3", "player_2")]
    gp = _game(tmp_path, "g", cases, roles=ROLES, day_res=[NO_LYNCH])
    record = json.loads(Path(gp).read_text())
    sums, ns = game_score(record, arm="on")
    assert ns["town"] == 2 and sums["town"] == 1.0  # abstain 0 + threat-hit +1, NOT -1 + 1


# --- (a') the deadlock_negative rule itself ---------------------------------------------------------

def test_deadlock_negative_grades_by_day_resolution():
    assert _town_abstain_credit(NO_LYNCH) == "negative"
    assert _town_abstain_credit(LYNCHED_TOWN) == "neutral"    # abstained from a mislynch: defensible
    assert _town_abstain_credit(LYNCHED_THREAT) == "neutral"  # room converged without them: no harm
    assert _town_abstain_credit(None) == "neutral"            # missing row: degrade, never guess
    kw = dict(abstain_rule="deadlock_negative", day_res=NO_LYNCH)
    assert _vote_credit("villager", "abstain", ROLES, **kw) == "negative"
    assert _vote_credit("investigator", "abstain", ROLES, **kw) == "negative"
    # deceivers keep their own abstain semantics under the town rule
    assert _vote_credit("serial_killer", "abstain", ROLES, **kw) == "neutral"
    assert _vote_credit("wolf", "abstain", ROLES, majority="abstain", **kw) == "positive"  # blend


def test_base_rates_follow_the_rule(tmp_path):
    """Baseline coherence: the OFF base under deadlock_negative prices abstains negative too."""
    cases = [_vote_case("villager", "player_1", "abstain", mem=False),
             _vote_case("villager", "player_3", "player_2", mem=False)]
    gp = _game(tmp_path, "off", cases, roles=ROLES, day_res=[NO_LYNCH])
    legacy = compute_base_rates(gp)
    new = compute_base_rates(gp, abstain_rule="deadlock_negative")
    assert legacy["villager/day_vote"] == (0.5, 2)   # (0 + 1) / 2
    assert new["villager/day_vote"] == (0.0, 2)      # (-1 + 1) / 2


def test_credit_apply_threads_the_rule_to_the_ledger(tmp_path):
    sp = tmp_path / "strategy_points.json"
    sp.write_text(json.dumps({"namespaces": {"strategy_points/villager/day_vote": [_sp("k_abstain")]}}))
    cases = [_vote_case("villager", "player_1", "abstain", key="k_abstain")]
    gp = _game(tmp_path, "on", cases, roles=ROLES, day_res=[NO_LYNCH])
    credit_apply(sp, gp, base_rates={}, discussion=False, abstain_rule="deadlock_negative")
    v = json.loads(sp.read_text())["namespaces"]["strategy_points/villager/day_vote"][0]["value"]
    assert v["negative_count"] == 1 and v["neutral_count"] == 0
    credit_apply(sp, gp, base_rates={}, discussion=False)  # default: the legacy neutral bucket
    v = json.loads(sp.read_text())["namespaces"]["strategy_points/villager/day_vote"][0]["value"]
    assert v["neutral_count"] == 1 and v["negative_count"] == 0


# --- (b) conversion channel -------------------------------------------------------------------------

def _conv_game(tmp, name, *, day_res, night_res, cases=(), roles=ROLES):
    return _game(tmp, name, list(cases), roles=roles, day_res=day_res, night_res=night_res)


def _night_find(day, target="player_2", deaths=()):
    return {"day": day, "investigator_target": target, "deaths": list(deaths)}


def test_find_outcomes_positive_negative_voided(tmp_path):
    lynch_d2 = {"day": 2, "voted_player": "player_2"}
    quiet = lambda d: {"day": d, "voted_player": None}  # noqa: E731
    # converted on day 2 (night-1 find, window 2)
    g = json.loads(Path(_conv_game(tmp_path, "pos", day_res=[{"day": 1, "voted_player": None}, lynch_d2],
                                   night_res=[_night_find(1)])).read_text())
    assert find_outcomes(g, 2) == [("player_4", "player_2", 2, 2, "positive")]
    # full window played, never lynched -> negative
    g = json.loads(Path(_conv_game(tmp_path, "neg", day_res=[quiet(1), quiet(2), quiet(3)],
                                   night_res=[_night_find(1)])).read_text())
    assert find_outcomes(g, 2) == [("player_4", "player_2", 2, 3, "negative")]
    # target night-killed inside the window -> voided (moot, not negative)
    g = json.loads(Path(_conv_game(tmp_path, "void", day_res=[quiet(1), quiet(2), quiet(3)],
                                   night_res=[_night_find(1, deaths=["player_2"])])).read_text())
    assert find_outcomes(g, 2) == []
    # game ends mid-window AFTER a played day -> negative on the played days (early-end deadlock);
    # voided only when the window never opened (no day of it was ever played)
    g = json.loads(Path(_conv_game(tmp_path, "end", day_res=[quiet(1), quiet(2)],
                                   night_res=[_night_find(1)])).read_text())
    assert find_outcomes(g, 2) == [("player_4", "player_2", 2, 2, "negative")]
    g = json.loads(Path(_conv_game(tmp_path, "never", day_res=[quiet(1), quiet(2)],
                                   night_res=[_night_find(2)])).read_text())
    assert find_outcomes(g, 2) == []
    g = json.loads(Path(_conv_game(tmp_path, "inno", day_res=[quiet(1), quiet(2), quiet(3)],
                                   night_res=[_night_find(1, target="player_3")])).read_text())
    assert find_outcomes(g, 2) == []


def test_conversion_ledger_credits_window_retrievals_only(tmp_path):
    day_res = [{"day": 1, "voted_player": None}, {"day": 2, "voted_player": None},
               {"day": 3, "voted_player": None}]
    cases = [
        _vote_case("investigator", "player_4", "abstain", key="k_in_window", day=2),
        _vote_case("investigator", "player_4", "abstain", key="k_before", day=1),   # pre-find
        _vote_case("villager", "player_1", "abstain", key="k_other_player", day=2),  # not the finder
    ]
    gp = _conv_game(tmp_path, "led", day_res=day_res, night_res=[_night_find(1)], cases=cases)
    ledger = conversion_ledger(gp, 2)
    assert ledger == {"k_in_window": {"pos": 0, "neg": 1}}
    assert conversion_base(gp, 2) == (-1.0, 1)  # same construct on the same game


def test_conversion_apply_and_prune_term(tmp_path):
    sp = tmp_path / "strategy_points.json"
    silent = _sp("k_silence", cell="investigator/day_vote")
    proven = _sp("k_proven", cell="investigator/day_vote", follow_count=8, positive_count=8)
    sp.write_text(json.dumps({"namespaces": {"strategy_points/investigator/day_vote": [silent, proven]}}))
    day_res = [{"day": d, "voted_player": None} for d in (1, 2, 3, 4, 5, 6, 7)]
    night_res = [_night_find(d) for d in (1, 2, 3, 4, 5)]  # 5 finds, none ever converts
    cases = [_vote_case("investigator", "player_4", "abstain", key=k, day=d)
             for d in (2, 3, 4, 5, 6) for k in ("k_silence", "k_proven")]
    gp = _conv_game(tmp_path, "app", day_res=day_res, night_res=night_res, cases=cases)
    (tmp_path / "base_rates.json").write_text(json.dumps({"investigator/day_vote": [0.0, 4]}))
    stats = conversion_apply(sp, gp, off_window=None, window_days=2)
    assert stats["conversion_credited"] == 2
    store = json.loads(sp.read_text())
    ns = store["namespaces"]
    assert ns["strategy_points/investigator/day_vote"][0]["value"]["conversion_neg_count"] == 5
    base_rates = json.loads((tmp_path / "base_rates.json").read_text())
    assert base_rates["investigator/day_vote"] == [0.0, 4]        # upsert preserved the sidecar
    assert base_rates[CONVERSION_CHANNEL] == [0.0, 0]
    assert conversion_lift(ns["strategy_points/investigator/day_vote"][0]["value"]) == -0.5  # -1 * 5/10
    # prune: the follow ledger can't touch k_silence (follow=0); the conversion term can — and the
    # proven exemption still shields the vote-proven SP from the diffuse channel.
    cfg = LoopConfig(conversion_credit=True, conversion_min_n=5)
    stats = prune_and_evict(store["namespaces"], base_rates, cfg)
    assert stats["pruned"] == 1
    keys = [r["key"] for r in store["namespaces"]["strategy_points/investigator/day_vote"]]
    assert keys == ["k_proven"]
    # knob off: nothing prunable (regression pin for every existing run config)
    store2 = {"namespaces": {"strategy_points/investigator/day_vote": [
        _sp("k_silence", cell="investigator/day_vote", conversion_neg_count=5)]}}
    assert prune_and_evict(store2["namespaces"], base_rates, LoopConfig())["pruned"] == 0
