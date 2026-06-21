"""Regression tests for the compounding-loop fail-loud guards + the window-glob fix.

Covers the bug class that dead-credited a paid run: a multi-path window silently globbing to nothing, an
unresolved eval_cases_path silently skipping a game, an empty off-arm silently haloing lift, and an empty
slope point. Each must now RAISE, not return a plausible wrong number.
"""

import json

import pytest

from evaluation.src.experiments.credit_backfill import _expand_dumps
from evaluation.src.loop.invariants import (
    _iter_eval_cases, assert_base_rates, assert_credit_engaged, assert_score,
    count_follow_verdicts, expand_window)


def _write(p, rows):
    p.write_text("\n".join(json.dumps(r) for r in rows))
    return str(p)


def _game_with_cases(tmp_path, name, verdicts_per_case, *, creditable=True):
    """A (game record file, eval-cases file) pair. verdicts_per_case = list of lists of verdict strings.
    creditable=True => mem-ON day_vote cases with a populated strategy_index_to_key (follows count);
    creditable=False => the cold-start shape (mem-OFF, empty index) whose 'follow's the ledger ignores."""
    ec_path = tmp_path / f"{name}_cases.jsonl"
    cases = []
    for vs in verdicts_per_case:
        idx = {str(i): f"key-{name}-{i}" for i in range(len(vs))} if creditable else {}
        cases.append({"output": {"eval_case": {
            "memory_enabled": creditable, "player_role": "villager", "action_phase": "day_vote",
            "strategy_index_to_key": idx,
            "strategy_verdicts": [{"verdict": v, "strategy_index": i} for i, v in enumerate(vs)]}}})
    _write(ec_path, cases)
    game_path = tmp_path / f"{name}.jsonl"
    _write(game_path, [{"roles": {"player_1": "villager"}, "eval_cases_path": str(ec_path)}])
    return str(game_path)


# --- the glob fix: single pattern AND space-joined list both resolve -------------------------------
def test_expand_dumps_single_and_joined(tmp_path):
    a = tmp_path / "gen1_on.jsonl"; a.write_text("{}")
    b = tmp_path / "gen2_on.jsonl"; b.write_text("{}")
    assert _expand_dumps(str(a)) == [str(a)]                      # single pattern
    assert set(_expand_dumps(f"{a} {b}")) == {str(a), str(b)}     # space-joined (the broken case)
    assert _expand_dumps(str(tmp_path / "nope_*.jsonl")) == []    # no match -> empty (caller must guard)


# --- expand_window: explicit, every file asserted present ------------------------------------------
def test_expand_window_missing_raises(tmp_path):
    (tmp_path / "gen1_on.jsonl").write_text("{}")
    assert expand_window(tmp_path, [1], "on") == [str(tmp_path / "gen1_on.jsonl")]
    with pytest.raises(AssertionError, match="window file missing"):
        expand_window(tmp_path, [1, 2], "on")  # gen2 absent


# --- credit-engaged: the exact guard for the dead-credit bug ---------------------------------------
def test_assert_credit_engaged_dead_raises(tmp_path):
    win = [_game_with_cases(tmp_path, "g", [["follow", "not_relevant"], ["follow"]])]
    assert count_follow_verdicts(win) == 2                  # 1 follow in each of the 2 cases
    with pytest.raises(AssertionError, match="credit DEAD"):
        assert_credit_engaged(win, ledger_keys=0)          # follows exist, ledger empty -> bug
    assert assert_credit_engaged(win, ledger_keys=2) == 2  # engaged -> ok, returns follow count


def test_assert_credit_engaged_cold_start_ok(tmp_path):
    win = [_game_with_cases(tmp_path, "g", [["not_relevant"], []])]  # no follows yet (cold)
    assert assert_credit_engaged(win, ledger_keys=0) == 0            # 0 follows -> no claim, no raise


def test_count_ignores_noncreditable_follows(tmp_path):
    # the exact cold-start false-positive: mem-OFF 'follow' verdicts (e.g. wolf night, no SP) must NOT
    # count, so the guard does not fire when the ledger is correctly empty.
    win = [_game_with_cases(tmp_path, "g", [["follow"], ["follow", "follow"]], creditable=False)]
    assert count_follow_verdicts(win) == 0
    assert assert_credit_engaged(win, ledger_keys=0) == 0  # correctly empty ledger -> no raise


# --- strict eval_cases_path resolution -------------------------------------------------------------
def test_iter_eval_cases_unresolved_path_raises(tmp_path):
    game = tmp_path / "g.jsonl"
    _write(game, [{"roles": {"p1": "villager"}, "eval_cases_path": str(tmp_path / "gone.jsonl")}])
    with pytest.raises(AssertionError, match="does not resolve"):
        list(_iter_eval_cases([str(game)]))


# --- base_rates + score --------------------------------------------------------------------------
def test_assert_base_rates():
    with pytest.raises(AssertionError, match="0 base-rate channels"):
        assert_base_rates({}, off_ran=True)
    assert_base_rates({}, off_ran=False)              # off didn't run -> empty is fine
    assert_base_rates({"villager/day_vote": (0.3, 9)}, off_ran=True)


def test_assert_score():
    with pytest.raises(AssertionError, match="0 decisions"):
        assert_score({}, label="gen2")
    assert_score({"on/town": 0.3, "n_on/town": 12}, label="gen2")  # has scored decisions
