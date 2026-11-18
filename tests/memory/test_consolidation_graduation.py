"""The graduated production pipeline (Agents/memory/consolidation/) — the properties that gate go-live.

(a) FIXED RULE, HARD-CODED — production grades town abstains deadlock-negative with NO keyword,
    flag, or config anywhere on the call path (owner ruling 2026-07-21: the knobbed variants are
    eval-only). The conversion channel was dropped with the ten-seat port (plan §9.6 item 3), and with
    it the parity test against the eval grader, which stays nine-seat for the frozen runs; the
    ten-seat table is tested in test_ten_seat_grading.py.
(c) POISONING GUARD — a game record with a human seat teaches nothing (ledger, base).
(d) DB IS THE RECORD — on a real database: tests/memory/integration/test_consolidation_db.py.
"""

from __future__ import annotations

import json
from pathlib import Path

from Agents.memory.consolidation.config import TickConfig
from Agents.memory.consolidation.credit import credit_apply as prod_credit_apply
from Agents.memory.consolidation.credit_rules import compute_base_rates as prod_base_rates
from Agents.memory.consolidation.grading import GameView
from tests.factories.builders import (CREDIT_ROLES as ROLES,
                                      NO_LYNCH,
                                      credit_game_record as _game,
                                      day_vote_case as _vote_case,
                                      strategy_point as _sp)

LYNCHED_THREAT = {"day": 2, "no_vote": False, "voted_player": "player_2",
                  "voted_player_role": "chanteuse", "vote_counts": {"player_2": 4}}


def _sp_store(tmp: Path, name: str, sps: dict) -> Path:
    p = tmp / name
    p.write_text(json.dumps({"namespaces": sps}))
    return p


# --- (a) the fixed rule is the ONLY rule ------------------------------------------------------------

def test_production_abstain_rule_needs_no_switch():
    view = GameView({"roles": ROLES})
    assert view.vote_grade("player_1", "sentinel", 2, "abstain", day_res=NO_LYNCH) == "negative"
    assert view.vote_grade("player_1", "sentinel", 2, "abstain", day_res=LYNCHED_THREAT) == "neutral"
    assert view.vote_grade("player_1", "sentinel", 2, "abstain") == "neutral"  # missing row: degrade
    # evil seats keep their own abstain semantics under the town rule
    assert view.vote_grade("player_5", "serial_killer", 2, "abstain", day_res=NO_LYNCH) == "neutral"
    assert view.vote_grade("player_2", "chanteuse", 2, "abstain", majority="abstain", day_res=NO_LYNCH) == "positive"
    import inspect
    assert "abstain_rule" not in inspect.signature(view.vote_grade).parameters
    assert "abstain_rule" not in inspect.signature(prod_credit_apply).parameters
    assert not hasattr(TickConfig(), "conversion_window_days")


# --- (c) the poisoning guard ------------------------------------------------------------------------

def test_human_seat_decisions_teach_nothing(tmp_path):
    # player_1 is the human: its own decisions are dropped from both the base and the ledger.
    cases_on = [_vote_case("trailseer", "player_1", "player_2", key="k_push")]
    cases_off = [_vote_case("sentinel", "player_1", "abstain", mem=False)]
    human_on = _game(tmp_path, "hon", cases_on, day_res=[NO_LYNCH], human_player="player_1")
    human_off = _game(tmp_path, "hoff", cases_off, day_res=[NO_LYNCH], human_player="player_1")
    sp = _sp_store(tmp_path, "strategy_points.json", {
        "strategy_points/trailseer/day_vote": [_sp("k_push", cell="trailseer/day_vote")]})
    assert prod_base_rates(human_off) == {}
    stats = prod_credit_apply(sp, human_on, base_rates={}, off_window=None)
    assert stats["ledger_keys"] == 0 and stats["credited"] == 0


def test_ai_seats_in_a_human_game_still_teach(tmp_path):
    # Owner, 2026-10-26: a game with a human seat is read; its AI seats' decisions are graded.
    cases_on = [_vote_case("trailseer", "player_3", "player_2", key="k_push")]
    cases_off = [_vote_case("trailseer", "player_3", "abstain", mem=False)]
    human_on = _game(tmp_path, "hon", cases_on, day_res=[NO_LYNCH], human_player="player_1")
    human_off = _game(tmp_path, "hoff", cases_off, day_res=[NO_LYNCH], human_player="player_1")
    sp = _sp_store(tmp_path, "strategy_points.json", {
        "strategy_points/trailseer/day_vote": [_sp("k_push", cell="trailseer/day_vote")]})
    assert prod_base_rates(human_off) != {}
    stats = prod_credit_apply(sp, human_on, base_rates={}, off_window=None)
    assert stats["ledger_keys"] == 1


def test_a_human_game_whose_seats_are_not_named_teaches_nothing(tmp_path):
    cases_on = [_vote_case("trailseer", "player_3", "player_2", key="k_push")]
    flagged = _game(tmp_path, "flag", cases_on, day_res=[NO_LYNCH], human_player=True)
    sp = _sp_store(tmp_path, "strategy_points.json", {
        "strategy_points/trailseer/day_vote": [_sp("k_push", cell="trailseer/day_vote")]})
    stats = prod_credit_apply(sp, flagged, base_rates={}, off_window=None)
    assert stats["ledger_keys"] == 0
