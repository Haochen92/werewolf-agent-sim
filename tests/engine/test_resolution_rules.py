"""The shared resolution kernel (Agents.rules.resolution).

These rules are consumed by BOTH the engine nodes and the wire translator — the whole point
of the module is that there is exactly one implementation of night precedence and day-vote
classification. The tests pin the rules themselves; node-level behavior (announcements,
roster edits) stays covered by the resolution/orchestrator test files.
"""
from __future__ import annotations

from Agents.rules.resolution import collect_attacks, resolve_attacks, tally_day_vote


# ---- collect_attacks -------------------------------------------------------------------

def test_collects_each_killer_and_skips_absent_ones():
    attacks = collect_attacks("t0", None, "t1")
    assert attacks == {"t0": ["wolves"], "t1": ["vigilante"]}


def test_multiple_killers_on_one_target_stack():
    attacks = collect_attacks("t0", "t0", "t0")
    assert attacks == {"t0": ["wolves", "serial_killer", "vigilante"]}


def test_no_killers_no_attacks():
    assert collect_attacks(None, None, None) == {}


# ---- resolve_attacks: precedence = immune > saved > killed -----------------------------

def test_plain_attack_kills():
    verdicts = resolve_attacks({"t0": ["wolves"]}, healer_target=None, serial_killer_player="sk")
    assert verdicts == {"t0": "killed"}


def test_heal_saves_the_target():
    verdicts = resolve_attacks({"t0": ["wolves"]}, healer_target="t0", serial_killer_player="sk")
    assert verdicts == {"t0": "saved"}


def test_sk_is_immune_even_when_healed():
    # The gate is identity, not heal state: immunity outranks the heal (matches the node's
    # defensive test — a healed SK is still "immune", so the whiff note still fires).
    verdicts = resolve_attacks({"sk": ["wolves"]}, healer_target="sk", serial_killer_player="sk")
    assert verdicts == {"sk": "immune"}


def test_multi_killer_target_resolves_exactly_once():
    verdicts = resolve_attacks(
        {"t0": ["wolves", "vigilante"]}, healer_target=None, serial_killer_player=None
    )
    assert verdicts == {"t0": "killed"}


# ---- tally_day_vote --------------------------------------------------------------------

def test_unique_plurality_lynches():
    tally = tally_day_vote(["a", "a", "b"])
    assert tally.lynched == "a"
    assert tally.outcome == "lynched"
    assert tally.vote_counts == {"a": 2, "b": 1}


def test_tie_is_a_no_lynch_with_both_candidates():
    tally = tally_day_vote(["a", "b"])
    assert tally.lynched is None
    assert tally.outcome == "tie"
    assert sorted(tally.candidates) == ["a", "b"]


def test_abstain_plurality_is_a_no_lynch():
    tally = tally_day_vote(["abstain", "abstain", "b"])
    assert tally.lynched is None
    assert tally.outcome == "abstain"


def test_abstain_votes_count_but_do_not_shield_a_real_plurality():
    tally = tally_day_vote(["a", "a", "abstain"])
    assert tally.lynched == "a"
    assert tally.vote_counts["abstain"] == 1


def test_no_ballots_is_no_vote():
    tally = tally_day_vote([])
    assert tally.outcome == "no_vote"
    assert tally.lynched is None
    assert tally.candidates == []


def test_abstain_tied_with_player_is_a_tie_not_abstain():
    tally = tally_day_vote(["a", "abstain"])
    assert tally.outcome == "tie"
    assert tally.lynched is None
