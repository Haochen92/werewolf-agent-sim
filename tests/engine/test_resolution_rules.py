"""The shared resolution rules: the night layer (Agents.rules.night) and the day vote
(Agents.rules.resolution).

These rules are consumed by BOTH the engine nodes and the wire translator — the whole point
is that there is exactly one implementation of night precedence and day-vote classification.
The tests pin the rules themselves; node-level behavior (announcements, roster edits) stays
covered by the resolution/orchestrator test files.
"""
from __future__ import annotations

from Agents.rules.night import resolve_night
from Agents.schemas.night import NightChoice
from Agents.rules.resolution import tally_day_vote

ROLES = {"w0": "wolf", "sk": "serial_killer", "v": "vigilante", "h": "healer",
         "t0": "villager", "t1": "villager"}


def _attacker_types(outcome) -> dict[str, list[str]]:
    return {t: [a.attacker_type for a in attacks] for t, attacks in outcome.attacks_on.items()}


def _kill(actor: str, target: str) -> NightChoice:
    return NightChoice(actor, ROLES[actor], "kill", target)


# ---- attacks are collected per target ------------------------------------------------------

def test_collects_each_killer_and_skips_absent_ones():
    outcome = resolve_night([_kill("w0", "t0"), _kill("v", "t1")], ROLES, 1)
    assert _attacker_types(outcome) == {"t0": ["wolves"], "t1": ["vigilante"]}


def test_multiple_killers_on_one_target_stack():
    outcome = resolve_night([_kill("w0", "t0"), _kill("sk", "t0"), _kill("v", "t0")], ROLES, 1)
    assert _attacker_types(outcome) == {"t0": ["wolves", "serial_killer", "vigilante"]}


def test_no_killers_no_attacks():
    assert resolve_night([], ROLES, 1).attacks_on == {}


# ---- verdicts: precedence = immune > saved > killed ------------------------------------------

def test_plain_attack_kills():
    outcome = resolve_night([_kill("w0", "t0")], ROLES, 1)
    assert outcome.verdicts == {"t0": "killed"}
    assert outcome.deaths == ["t0"]


def test_heal_saves_the_target():
    outcome = resolve_night([_kill("w0", "t0"), NightChoice("h", "healer", "protect", "t0")], ROLES, 1)
    assert outcome.verdicts == {"t0": "saved"}
    assert outcome.deaths == []


def test_sk_is_immune_even_when_healed():
    # The gate is the role, not heal state: immunity outranks the heal (matches the node's
    # defensive test — a healed SK is still "immune", so the whiff note still fires).
    outcome = resolve_night([_kill("w0", "sk"), NightChoice("h", "healer", "protect", "sk")], ROLES, 1)
    assert outcome.verdicts == {"sk": "immune"}


def test_multi_killer_target_resolves_exactly_once():
    outcome = resolve_night([_kill("w0", "t0"), _kill("v", "t0")], ROLES, 1)
    assert outcome.verdicts == {"t0": "killed"}
    assert outcome.deaths == ["t0"]


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
