"""Regression tests for the compounding-loop fail-loud guards + the window-glob fix.

Covers the bug class that dead-credited a paid run: a multi-path window silently globbing to nothing, an
unresolved eval_cases_path silently skipping a game, an empty off-arm silently haloing lift, and an empty
slope point. Each must now RAISE, not return a plausible wrong number.
"""

import json

import pytest

from evaluation.src.loop.credit_backfill import _expand_dumps
from evaluation.src.loop.invariants import (
    _iter_eval_cases, arm_fingerprint, arm_memory_factions, assert_arm_declared, assert_arm_factions,
    assert_base_rates, assert_credit_engaged, assert_discussion_credit_engaged,
    assert_fingerprint_consistent, assert_observations_retired, assert_score,
    count_discussion_follow_verdicts, count_follow_verdicts, expand_window, resolve_expected_factions)


def _write(p, rows):
    p.write_text("\n".join(json.dumps(r) for r in rows))
    return str(p)


def _game_with_cases(tmp_path, name, verdicts_per_case, *, creditable=True, phase="day_vote"):
    """A (game record file, eval-cases file) pair. verdicts_per_case = list of lists of verdict strings.
    creditable=True => mem-ON cases with a populated strategy_index_to_key (follows count);
    creditable=False => the cold-start shape (mem-OFF, empty index) whose 'follow's the ledger ignores.
    phase = the action_phase (day_vote credits via build_ledger; day_discussion via the disc guard only)."""
    ec_path = tmp_path / f"{name}_cases.jsonl"
    cases = []
    for vs in verdicts_per_case:
        idx = {str(i): f"key-{name}-{i}" for i in range(len(vs))} if creditable else {}
        cases.append({"output": {"eval_case": {
            "memory_enabled": creditable, "player_role": "villager", "action_phase": phase,
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


# --- arm-factions guard: THE v2 trap (ran all_enabled when town_only was intended) ----------------
def _on_arm(tmp_path, memory_config):
    p = tmp_path / "gen1_on.jsonl"
    _write(p, [{"roles": {"p1": "villager"}, "memory_config": memory_config, "eval_cases_path": "x"}])
    return str(p)


def test_arm_memory_factions_reads_enabled_set(tmp_path):
    on = _on_arm(tmp_path, {"villager": True, "healer": True, "wolf": False, "serial_killer": False})
    assert arm_memory_factions(on) == frozenset({"villager", "healer"})


def test_assert_arm_factions_catches_v2_trap(tmp_path):
    # all_enabled ran, town_only declared -> must crash (the $60 bug)
    on = _on_arm(tmp_path, {r: True for r in
                            ("villager", "healer", "investigator", "vigilante", "wolf", "serial_killer")})
    with pytest.raises(AssertionError, match="ARM MISMATCH"):
        assert_arm_factions(on, "town_only")


def test_assert_arm_factions_match_passes(tmp_path):
    town = {"villager": True, "healer": True, "investigator": True, "vigilante": True,
            "wolf": False, "serial_killer": False}
    on = _on_arm(tmp_path, town)
    assert assert_arm_factions(on, "town_only") == frozenset({"villager", "healer", "investigator", "vigilante"})


def test_assert_arm_factions_intent_none_surfaces_without_asserting(tmp_path):
    on = _on_arm(tmp_path, {"villager": True, "wolf": True})
    assert assert_arm_factions(on, None) == frozenset({"villager", "wolf"})  # returns set, no raise


def test_resolve_all_matches_actual_cast(tmp_path):
    actual = frozenset({"villager", "wolf", "serial_killer"})
    assert resolve_expected_factions("all", actual) == actual          # 'all' = whatever the cast exposes
    assert resolve_expected_factions("wolf,villager", actual) == frozenset({"wolf", "villager"})


# --- arm-declaration gate (#5): fail-closed unless declared OR explicitly waived -------------------
def test_assert_arm_declared_requires_intent_or_waiver():
    with pytest.raises(AssertionError, match="arm UNDECLARED"):
        assert_arm_declared(None, False)          # forgot to declare -> refuse to start (the v2 hole)
    assert_arm_declared("town_only", False)       # declared -> no raise
    assert_arm_declared(None, True)               # explicitly waived -> no raise


# --- discussion-credit guard (#3/#7): the channel build_ledger / assert_credit_engaged are blind to -
def test_count_discussion_follow_verdicts(tmp_path):
    disc = [_game_with_cases(tmp_path, "d", [["follow", "not_relevant"], ["follow"]], phase="day_discussion")]
    assert count_discussion_follow_verdicts(disc) == 2   # 2 day_discussion follows
    assert count_follow_verdicts(disc) == 0              # ...which the vote/night counter correctly ignores


def test_assert_discussion_credit_engaged_dead_raises(tmp_path):
    win = [_game_with_cases(tmp_path, "d", [["follow"], ["follow"]], phase="day_discussion")]
    with pytest.raises(AssertionError, match="discussion credit DEAD"):
        assert_discussion_credit_engaged(win, disc_credited=0, enabled=True)         # tagger whiffed silently
    assert assert_discussion_credit_engaged(win, disc_credited=3, enabled=True) == 2  # engaged -> ok


def test_assert_discussion_credit_engaged_disabled_or_cold(tmp_path):
    win = [_game_with_cases(tmp_path, "d", [["follow"]], phase="day_discussion")]
    assert assert_discussion_credit_engaged(win, disc_credited=0, enabled=False) == 0  # off -> no claim
    cold = [_game_with_cases(tmp_path, "c", [["not_relevant"]], phase="day_discussion")]
    assert assert_discussion_credit_engaged(cold, disc_credited=0, enabled=True) == 0  # no follows -> no claim


# --- §6.8 obs-retirement guard: the loop must not inject observations under the v7 SP-only default ---
def _on_arm_rtc(tmp_path, rtc, cases=None):
    """ON game record carrying retrieval_types_config `rtc` + an eval-cases sidecar (`cases` = list of
    {'output': {'eval_case': {...}}} rows, default empty)."""
    ec_path = tmp_path / "rtc_cases.jsonl"
    _write(ec_path, cases or [])
    p = tmp_path / "gen1_on.jsonl"
    _write(p, [{"roles": {"p1": "villager"}, "retrieval_types_config": rtc,
                "eval_cases_path": str(ec_path)}])
    return str(p)


def test_assert_observations_retired_config_trips(tmp_path):
    # obs retrieval ON but the loop declared SP-only -> the flag never reached run_batch (the wrong arm).
    on = _on_arm_rtc(tmp_path, {"observations": True, "strategy_points": True})
    with pytest.raises(AssertionError, match="OBS INJECTED"):
        assert_observations_retired(on, "strategy_points_only")


def test_assert_observations_retired_config_passes(tmp_path):
    on = _on_arm_rtc(tmp_path, {"observations": False, "strategy_points": True})
    assert_observations_retired(on, "strategy_points_only")   # obs off -> no raise


def test_assert_observations_retired_noop_for_both(tmp_path):
    # 'both' legitimately injects obs (the v5/v6 comparison arm) -> the guard must not fire.
    on = _on_arm_rtc(tmp_path, {"observations": True, "strategy_points": True})
    assert_observations_retired(on, "both")


def test_assert_observations_retired_prompt_input_trips(tmp_path):
    # config surface passes (obs off) but a sampled memory-enabled decision carries a retrieved-obs slot.
    case = {"output": {"eval_case": {"memory_enabled": True,
                                     "retrieved_observations": [{"key": "o1"}]}}}
    on = _on_arm_rtc(tmp_path, {"observations": False, "strategy_points": True}, cases=[case])
    with pytest.raises(AssertionError, match="OBS IN PROMPT"):
        assert_observations_retired(on, "strategy_points_only")


# --- runtime-fingerprint drift guard (#16): never splice across backends/models/prompts ------------
def _game_with_fp(tmp_path, name, fp):
    p = tmp_path / f"{name}.jsonl"
    _write(p, [{"roles": {"p1": "villager"}, "runtime_fingerprint": fp, "eval_cases_path": "x"}])
    return str(p)


def test_arm_fingerprint_reads_first_stamp(tmp_path):
    fp = {"llm_backend": "google", "game_model": "gemini-3.1-flash-lite"}
    assert arm_fingerprint(_game_with_fp(tmp_path, "g", fp)) == fp


def test_arm_fingerprint_missing_raises(tmp_path):
    p = tmp_path / "g.jsonl"
    _write(p, [{"roles": {"p1": "villager"}}])           # no fingerprint stamped
    with pytest.raises(AssertionError, match="no runtime_fingerprint"):
        arm_fingerprint(str(p))


def test_assert_fingerprint_consistent_detects_backend_flip(tmp_path):
    ref = {"llm_backend": "vertex", "game_model": "gemini-3.1-flash-lite", "git_commit": "abc"}
    assert_fingerprint_consistent(_game_with_fp(tmp_path, "same", dict(ref)), ref)   # identical -> ok
    flipped = _game_with_fp(tmp_path, "flip", {**ref, "llm_backend": "google"})
    with pytest.raises(AssertionError, match="runtime DRIFT"):
        assert_fingerprint_consistent(flipped, ref)      # backend flipped mid-run -> crash


def test_assert_fingerprint_consistent_skips_unstamped_records(tmp_path):
    ref = {"llm_backend": "google", "game_model": "gemini-3.1-flash-lite"}
    p = tmp_path / "mixed.jsonl"
    _write(p, [{"roles": {"p1": "villager"}, "runtime_fingerprint": dict(ref)},
               {"roles": {"p2": "wolf"}}])               # second record has no fingerprint -> skipped
    assert_fingerprint_consistent(str(p), ref)           # no raise
