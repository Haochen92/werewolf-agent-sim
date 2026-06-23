"""Regression tests for generation_score's ARM bucketing (the #1 measurement fix).

The bug: bucketing by the per-decision `memory_enabled` flag mislabels a memoryless decision INSIDE an ON
game — a day-1 retrieval skip, or a memory-disabled role under town_only — as 'off', so the OFF baseline
gets polluted with ON-arm games (and those decisions vanish from the ON arm). These pin the fix: bucket by
ARM (which dump), drop day-1, count only memory-active ON decisions — with toggles to recover the raw view.
"""

import json

from evaluation.src.loop.measure import generation_score

ROLES = {"p_town": "villager", "p_wolf": "wolf"}


def _case(day, role, votee, memory_enabled):
    return {"kind": "agent_action_eval", "output": {"eval_case": {
        "day": day, "player_role": role, "action_phase": "day_vote",
        "memory_enabled": memory_enabled, "agent_vote": {"votee": votee}}}}


def _dump(tmp_path, name, cases):
    """A 1-game dump jsonl + its eval-cases jsonl. villager->wolf vote = +1, villager->town = -1."""
    ec = tmp_path / f"{name}_cases.jsonl"
    ec.write_text("\n".join(json.dumps(c) for c in cases))
    dump = tmp_path / f"{name}.jsonl"
    dump.write_text(json.dumps({"roles": ROLES, "eval_cases_path": str(ec)}))
    return str(dump)


def test_generation_score_buckets_by_arm_not_flag(tmp_path):
    # The ON game carries TWO memoryless decisions (day-1 town, day-2 wolf under town_only). The old
    # flag-bucketing dumped both into off/* (off/town +1, off/wolf +1), corrupting the baseline. They must
    # not leak: off/* sees ONLY the OFF arm; on/town sees only the day-2 memory-active town vote.
    on = _dump(tmp_path, "gen1_on", [
        _case(1, "villager", "p_wolf", False),   # day-1: memoryless in ON -> DROPPED (skip_day1)
        _case(2, "villager", "p_wolf", True),    # day-2 memory-active town -> on/town +1
        _case(2, "wolf", "p_town", False),       # town_only: wolf memoryless -> DROPPED (on_memory_active_only)
    ])
    off = _dump(tmp_path, "gen1_off", [
        _case(2, "villager", "p_town", False),   # OFF arm town -> off/town -1
    ])
    s = generation_score(on, off)
    assert s["on/town"] == 1.0 and s["n_on/town"] == 1     # only the day-2 memory-active town vote
    assert s["off/town"] == -1.0 and s["n_off/town"] == 1  # ONLY the OFF arm — no ON-arm leakage
    assert "on/wolf" not in s                               # wolf had no memory this arm -> empty, not misleading
    assert "off/wolf" not in s                              # the ON wolf decision did NOT leak into off/*


def test_generation_score_toggles_recover_raw_view(tmp_path):
    on = _dump(tmp_path, "gen1_on", [
        _case(1, "villager", "p_wolf", False),   # day-1
        _case(2, "villager", "p_wolf", True),    # day-2 memory town
        _case(2, "wolf", "p_town", False),       # day-2 wolf (memoryless)
    ])
    s = generation_score(on, None, skip_day1=False, on_memory_active_only=False)
    assert s["n_on/town"] == 2 and s["on/town"] == 1.0     # day-1 + day-2 villager, both +1
    assert s["n_on/wolf"] == 1 and s["on/wolf"] == 1.0     # wolf vote stays in on/wolf, NOT off/wolf
    assert not any(k.startswith("off/") for k in s)        # off_glob=None -> no off arm at all
