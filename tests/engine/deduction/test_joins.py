"""Level 2 of the deduction engine (slice 9b): the seat's own results joined with the players' claims
(Agents/deduction/joins/; catalogue Table F, F1 and F2, of
evidence/reasoning_failures/deduction_catalogue.md).

- Per family, on constructed nights through the real engine and constructed claims: the exact line
  where it fires, and the claims or nights where it must not (a truthful and a false claim; a second
  visitor; a claim that says it was roleblocked; a partial against a whole sighting; a visit the
  living conceal hid; a claim about a night the seat has no record of; an unsaid night; a tried
  action).
- The acceptance cases on their own frozen payloads: AC1 line 2 (F2), AC2, AC3 and AC4 line 2 (F1),
  exactly, and their "must not say". AC2's and AC4's claims are in the frozen day summaries. AC1's
  and AC3's were made the same day, before the speaker field existed, and no summary has them: the
  fixture fills the speaker field on the frozen messages by hand, from their own words.
- Placement: every join in the seat block, never the cached public block; a claim spoken today raises
  its night's working steps (fold rule 5, source a).
- The leak boundary: hidden roles swapped and hidden state planted change nothing; a claimed action a
  line does not name never reaches the record (the 9a guard), so it joins nothing.
- The oracles. The truth oracle: random legal games with truthful and false claims, every certain
  line holds, and every conditional line's conclusion holds whenever its premise does (the true
  branch is in the list). The brute-force role oracle (tests/factories/role_assignments.py) checks
  only the role facts the lines state, in every deal that agrees with the seat's view: a claim about
  a night choice is not a role, so the truth oracle is the check for the visits.
"""

from __future__ import annotations

import copy
import json
import random
import re
from pathlib import Path

from Agents.deduction import deduction_blocks, own_result_lines, seat_view_from_payload
from Agents.deduction.joins import join_items
from Agents.deduction.raised import raised_today
from Agents.prompts.prompt_inputs import build_agent_prompt_input
from Agents.schemas.deduction import AnyOf, RoleIn, SeatView
from Agents.schemas.game_events import DayChannel
from tests.engine.deduction.test_candidates import Table, _ac2, _ac4, _continuing_snapshots, _ne_sp, _sk_sp
from tests.factories.random_claims import random_claims
from tests.factories.random_nights import public_fact_holds, random_game
from tests.factories.role_assignments import oracle_of


def _said(day: int, player: str, *actions: tuple, message: str = "(a claim)") -> DayChannel:
    return DayChannel(day=day, seq=0, player=player, message=message,
                      claimed_night_actions=[dict(zip(("night", "action", "target", "result", "seen"), a))
                                             for a in actions])


def _view(table: Table, seat: str, day: int, *lines: DayChannel) -> SeatView:
    return seat_view_from_payload({**table.payload(seat), "day_channel": list(lines), "current_day": day})


def _joins(table: Table, seat: str, day: int, *lines: DayChannel) -> list[str]:
    return [item.text for item in join_items(_view(table, seat, day, *lines))]


# SK+SP, by seat: player_1 Investigator, player_2 Sentinel, player_3 Trailseer, player_4 Vigilante,
# player_5 Sigilist, player_6 Healer, player_7 Chanteuse, player_8 Illusionist, player_9 Serial Killer,
# player_10 Speculator.

def _night_one() -> Table:
    """The Investigator checks player_5, the Sentinel watches player_5, the Healer protects player_5,
    the Trailseer follows the Healer; the Chanteuse carries the kill on player_4 and blocks player_3."""
    return Table(_sk_sp()).night(1, ("player_7", "kill", "player_4"), ("player_7", "block", "player_3"),
                                 ("player_9", "kill", "player_10"), ("player_1", "investigate", "player_5"),
                                 ("player_2", "watch", "player_5"), ("player_6", "protect", "player_5"),
                                 ("player_3", "follow", "player_6"))


# --- F1: the seat's own action, seen by someone's watch or follow ----------------------------------------

def test_a_sighting_of_the_seats_own_visit_is_confirmed_and_only_that():
    """The Sentinel's true watch on player_5 saw the Investigator (AC3's form)."""
    seen = _said(2, "player_2", (1, "watch", "player_5", "not_said", ["player_1", "player_6"]))
    assert _joins(_night_one(), "player_1", 2, seen) == [
        "player_2 says you came to player_5 on night 1. You did: you checked player_5 that night. This confirms "
        "that part of player_2's report, not that player_2 is the Sentinel."]


def test_a_false_sighting_that_happens_to_name_the_seats_visit_confirms_only_the_visit():
    """player_8, the Illusionist, made the watch up; the visit it names is still true, and the line
    still does not make player_8 the Sentinel (it names the role its report stands on)."""
    lie = _said(2, "player_8", (1, "watch", "player_5", "not_said", ["player_1"]))
    assert _joins(_night_one(), "player_1", 2, lie) == [
        "player_8 says you came to player_5 on night 1. You did: you checked player_5 that night. This confirms "
        "that part of player_8's report, not that player_8 is the Sentinel."]


def test_a_follow_of_the_seat_is_confirmed_and_the_claimants_own_role_claim_is_the_one_hedged():
    claim = DayChannel(day=2, seq=0, player="player_4", message="(a claim)", claim="trailseer",
                       claimed_night_actions=[{"night": 1, "action": "follow", "target": "player_1", "result": "not_said",
                                               "seen": ["player_5"]}])
    assert _joins(_night_one(), "player_1", 2, claim) == [
        "player_4 says you went to player_5 on night 1. You did: you checked player_5 that night. This confirms "
        "that part of player_4's report, not that player_4 is the Trailseer."]


def test_a_follow_that_saw_the_seats_watch_reach_the_follower_is_confirmed_as_a_visit():
    """2b29bfe8: the Trailseer followed the Sentinel to its own door; the Sentinel's own result
    ("No one visited") never lists the Sentinel, and it denied going anywhere."""
    table = Table(_sk_sp()).night(1, ("player_7", "kill", "player_4"), ("player_9", "kill", "player_10"),
                                  ("player_2", "watch", "player_3"), ("player_3", "follow", "player_2"))
    follow = _said(2, "player_3", (1, "follow", "player_2", "not_said", ["player_3"]))
    assert _joins(table, "player_2", 2, follow) == [
        "player_3 says you went to player_3 on night 1. You did: you watched player_3 that night, and a watch is "
        "itself a visit. This confirms that part of player_3's report, not that player_3 is the Trailseer."]


def test_no_confirmation_of_a_visit_the_block_cancelled():
    """The Trailseer was roleblocked: its follow never went ahead, so a sighting of it is not confirmed."""
    lie = _said(2, "player_2", (1, "watch", "player_6", "not_said", ["player_3"]))
    assert _joins(_night_one(), "player_3", 2, lie) == []


def test_no_confirmation_on_another_night_an_unsaid_night_or_the_seats_own_claim():
    table = _night_one().night(2, ("player_8", "kill", "player_2"), ("player_9", "kill", "player_6"),
                               ("player_7", "block", "player_5"))  # the Investigator makes no choice on night 2
    other_night = _said(3, "player_2", (2, "watch", "player_5", "not_said", ["player_1"]))
    unsaid = _said(3, "player_2", (0, "watch", "player_5", "not_said", ["player_1"]))
    own = _said(3, "player_1", (1, "watch", "player_5", "not_said", ["player_1"]))
    for line in (other_night, unsaid, own):
        assert _joins(table, "player_1", 3, line) == []


def test_a_wolfs_visit_the_living_conceal_hid_is_never_confirmed_as_seen():
    """The Chanteuse carried the kill on player_4 and also blocked it, and the Illusionist concealed the
    body: both her visits there were hidden, so no watch saw her. Her block on another player was seen."""
    hidden = Table(_sk_sp()).night(1, ("player_7", "kill", "player_4"), ("player_7", "block", "player_4"),
                                   ("player_8", "conceal", None), ("player_9", "kill", "player_10"))
    lie = _said(2, "player_2", (1, "watch", "player_4", "not_said", ["player_7"]))
    assert _joins(hidden, "player_7", 2, lie) == []
    shown = Table(_sk_sp()).night(1, ("player_7", "kill", "player_4"), ("player_7", "block", "player_3"),
                                  ("player_8", "conceal", None), ("player_9", "kill", "player_10"))
    seen = _said(2, "player_2", (1, "watch", "player_3", "not_said", ["player_7"]))
    assert _joins(shown, "player_7", 2, seen) == [
        "player_2 says you came to player_3 on night 1. You did: you blocked player_3 that night. This confirms "
        "that part of player_2's report, not that player_2 is the Sentinel."]


# --- F1: a visitor the seat's own watch or follow saw ---------------------------------------------------

def test_the_seats_watch_confirms_a_visitors_own_claim_and_another_players_sighting():
    """E13: the Healer's claimed protection and the Trailseer's follow, both true."""
    protect = _said(2, "player_6", (1, "protect", "player_5", "not_said", []))
    follow = _said(2, "player_3", (1, "follow", "player_6", "not_said", ["player_5"]))
    assert _joins(_night_one(), "player_2", 2, protect, follow) == [
        "player_6 says it protected player_5 on night 1. Your watch saw player_6 come to player_5 that night. This "
        "confirms that player_6 went to player_5, not that player_6 is the Healer or that the visit was a "
        "protection.",
        "player_3 says player_6 went to player_5 on night 1. Your watch saw player_6 come to player_5 that night. "
        "This confirms that part of player_3's report, not that player_3 is the Trailseer."]


def test_a_false_claim_of_an_action_confirms_the_visit_never_the_action():
    """The Serial Killer attacked player_5 and claims to have protected it: the watch shows the visit."""
    table = Table(_sk_sp()).night(1, ("player_7", "kill", "player_4"), ("player_9", "kill", "player_5"),
                                  ("player_2", "watch", "player_5"), ("player_6", "protect", "player_5"))
    lie = _said(2, "player_9", (1, "protect", "player_5", "not_said", []))
    assert _joins(table, "player_2", 2, lie) == [
        "player_9 says it protected player_5 on night 1. Your watch saw player_9 come to player_5 that night. This "
        "confirms that player_9 went to player_5, not that player_9 is the Healer or that the visit was a "
        "protection."]


def test_a_follow_confirms_a_bare_visit_and_says_it_does_not_show_the_action():
    visit = _said(2, "player_6", (1, "visit", "player_5", "not_said", []))
    assert _joins(_night_one(), "player_3", 2, visit) == []  # the Trailseer was roleblocked: no follow to read
    table = Table(_sk_sp()).night(1, ("player_7", "kill", "player_4"), ("player_9", "kill", "player_10"),
                                  ("player_6", "protect", "player_5"), ("player_3", "follow", "player_6"))
    assert _joins(table, "player_3", 2, visit) == [
        "player_6 says it went to player_5 on night 1. Your follow saw player_6 go to player_5 that night. This "
        "confirms that player_6 went to player_5, not which action player_6 took."]


def test_no_confirmation_of_a_claim_that_says_it_was_roleblocked_or_names_another_target():
    blocked = _said(2, "player_6", (1, "protect", "player_5", "roleblocked", []))
    elsewhere = _said(2, "player_6", (1, "protect", "player_1", "not_said", []))
    for line in (blocked, elsewhere):
        assert _joins(_night_one(), "player_2", 2, line) == []


# --- F1 and F2: a roleblock and who came to the door ------------------------------------------------------

def _second_visitor() -> Table:
    """The Chanteuse blocks the Trailseer, and the Healer protects it: two visitors at its door."""
    return Table(_sk_sp()).night(1, ("player_7", "kill", "player_4"), ("player_7", "block", "player_3"),
                                 ("player_9", "kill", "player_10"), ("player_6", "protect", "player_3"),
                                 ("player_3", "follow", "player_6"))


def test_f2_a_claimed_visitor_is_the_chanteuse_or_came_beside_her():
    """Truthful claims of both visitors: the Healer's line is true on its second branch. Never "player_6
    is the Chanteuse": a second visitor is possible."""
    watch = _said(2, "player_2", (1, "watch", "player_3", "not_said", ["player_6", "player_7"]))
    visit = _said(2, "player_6", (1, "visit", "player_3", "not_said", []))
    assert _joins(_second_visitor(), "player_3", 2, watch, visit) == [
        "player_2 says player_6 came to you on night 1, and player_6 agrees. If that is true, either player_6 is the "
        "Chanteuse, or player_6 and the Chanteuse both came to you.",
        "player_2 says player_7 came to you on night 1. If that is true, either player_7 is the Chanteuse, or "
        "player_7 and the Chanteuse both came to you."]


def test_f2_on_the_visitors_word_alone_and_on_two_sightings():
    visit = _said(2, "player_7", (1, "visit", "player_3", "not_said", []))
    assert _joins(_second_visitor(), "player_3", 2, visit) == [
        "player_7 says it came to you on night 1. If that is true, either player_7 is the Chanteuse, or player_7 and "
        "the Chanteuse both came to you."]
    watch = _said(2, "player_2", (1, "watch", "player_3", "not_said", ["player_7"]))
    follow = _said(2, "player_5", (1, "follow", "player_7", "not_said", ["player_3"]))
    assert _joins(_second_visitor(), "player_3", 2, watch, follow) == [
        "player_2 and player_5 say player_7 came to you on night 1. If that is true, either player_7 is the "
        "Chanteuse, or player_7 and the Chanteuse both came to you."]


def test_no_f2_from_a_whole_list_of_no_one_a_blocked_sighting_a_tried_action_or_another_action():
    """"No one came" names no visitor (and is only whole because it says so, L12); a sighting the
    claimant says was roleblocked saw nothing; a protection claimed with no outcome is only tried
    (L13); a claimed action, as a premise, would also claim a role (the conditionals, F5)."""
    for line in (_said(2, "player_2", (1, "watch", "player_3", "no_visitors", [])),
                 _said(2, "player_2", (1, "watch", "player_3", "roleblocked", ["player_7"])),
                 _said(2, "player_6", (1, "protect", "player_3", "not_said", [])),
                 _said(2, "player_6", (1, "protect", "player_3", "no_attack", []))):
        assert _joins(_second_visitor(), "player_3", 2, line) == []


def test_f1_with_the_chanteuse_known_a_sighting_of_her_is_true_and_of_anyone_else_says_nothing():
    """AC2 constructed: the Investigator was roleblocked on night 2 by player_7, struck down that night
    and revealed the Chanteuse."""
    watch = _said(3, "player_2", (2, "watch", "player_5", "not_said", ["player_7", "player_8"]))
    assert _joins(_ac2(), "player_5", 3, watch) == [
        "You were roleblocked on night 2, so the Chanteuse came to you, and player_7 was the Chanteuse. player_2's "
        "report that player_7 came to you that night is true. This does not show that player_2 is the Sentinel."]
    protect = _said(3, "player_8", (2, "protect", "player_5", "no_attack", []))
    assert _joins(_ac2(), "player_5", 3, protect) == []


def test_ac1_constructed_and_the_same_night_once_the_chanteuse_is_known():
    """AC1 constructed: the Healer on day 2 (the Chanteuse unknown) gets F2. By day 3 the sigil has
    revealed her and player_3's will has been read out: the same claims are now certain (F1), never F2."""
    follow = _said(2, "player_3", (1, "follow", "player_7", "not_said", ["player_8"]))
    visit = _said(2, "player_7", (1, "visit", "player_8", "not_said", []))
    day_two = Table(_ac2().roles)
    day_two.night(1, ("player_7", "kill", "player_1"), ("player_7", "block", "player_8"), ("player_9", "conceal", None),
                  ("player_6", "kill", "player_1"), ("player_3", "follow", "player_7"),
                  ("player_5", "investigate", "player_9"), ("player_8", "protect", "player_5"),
                  ("player_2", "watch", "player_4"))
    assert _joins(day_two, "player_8", 2, follow, visit) == [AC1_LINE_2]
    later = [DayChannel(**{**line.model_dump(), "day": 3}) for line in (follow, visit)]
    assert _joins(_ac2(), "player_8", 3, *later) == [
        "player_7 says it went to player_8 on night 1. player_3's will shows player_3's follow saw player_7 go to "
        "player_8 that night. This confirms that player_7 went to player_8, not which action player_7 took.",
        "You were roleblocked on night 1, so the Chanteuse came to you, and player_7 was the Chanteuse. player_3's "
        "report that player_7 came to you that night is true. This does not show that player_3 is the Trailseer."]


def test_f1_through_the_dead_chanteuses_body_is_true_in_name():
    """NE+SP: the Chanteuse lynched on day 2, the Necromancer blocks the Investigator through her body."""
    table = Table(_ne_sp()).night(1, ("player_7", "kill", "player_4"), ("player_3", "follow", "player_1"))
    table.lynch("player_7", 2)
    table.night(2, ("player_8", "kill", "player_5"), ("player_9", "block", "player_1", "player_7"),
                ("player_1", "investigate", "player_6"), ("player_2", "watch", "player_1"))
    watch = _said(3, "player_2", (2, "watch", "player_1", "not_said", ["player_7"]))
    assert _joins(table, "player_1", 3, watch) == [
        "You were roleblocked on night 2 through the dead Chanteuse's body, so a watch on you would have shown "
        "player_7. player_2's report that player_7 came to you that night is true in name: the Necromancer, not "
        "player_7, made that visit. This does not show that player_2 is the Sentinel."]
    living = _said(3, "player_2", (2, "watch", "player_1", "not_said", ["player_9"]))
    assert _joins(table, "player_1", 3, living) == []  # the blocker was not a living player: no F2 either


# --- F1 and F2 through a will ------------------------------------------------------------------------------

def test_a_will_confirms_a_sighting_of_its_holders_visit_ac4_constructed():
    watch = _said(5, "player_9", (2, "watch", "player_6", "not_said", ["player_4", "player_8"]))
    assert _joins(_ac4(), "player_2", 5, watch) == [AC4_LINE_2]
    assert _joins(_ac4(), "player_3", 5, watch) == [AC4_LINE_2]  # public facts and a public claim
    assert _joins(_ac4(), "player_9", 5, watch) == []  # the claimant's own report


def test_a_wills_watch_confirms_a_claimed_protection_and_a_sighting():
    table = Table(_sk_sp()).night(1, ("player_7", "kill", "player_4"), ("player_9", "kill", "player_10"),
                                  ("player_2", "watch", "player_5"), ("player_6", "protect", "player_5"))
    table.lynch("player_2", 2)
    protect = _said(2, "player_6", (1, "protect", "player_5", "not_said", []))
    sighting = _said(2, "player_8", (1, "watch", "player_5", "not_said", ["player_6"]))
    assert _joins(table, "player_3", 2, protect, sighting) == [
        "player_6 says it protected player_5 on night 1. player_2's will shows player_2's watch saw player_6 come to "
        "player_5 that night. This confirms that player_6 went to player_5, not that player_6 is the Healer or that "
        "the visit was a protection.",
        "player_8 says player_6 came to player_5 on night 1. player_2's will shows player_2's watch saw player_6 "
        "come to player_5 that night. This confirms that part of player_8's report, not that player_8 is the "
        "Sentinel."]


def test_a_wills_roleblock_and_a_claimed_visitor():
    table = Table(_sk_sp()).night(1, ("player_7", "kill", "player_4"), ("player_9", "kill", "player_10"),
                                  ("player_7", "block", "player_1"), ("player_1", "investigate", "player_5"))
    table.lynch("player_1", 2)
    follow = _said(2, "player_3", (1, "follow", "player_7", "not_said", ["player_1"]))
    assert _joins(table, "player_6", 2, follow) == [
        "player_3 says player_7 came to player_1 on night 1. If that is true, either player_7 is the Chanteuse, or "
        "player_7 and the Chanteuse both came to player_1."]


# --- the acceptance cases, on their frozen payloads ---------------------------------------------------------

FROZEN = Path("evidence/reasoning_failures/data")

AC1_LINE_2 = ("player_3 says player_7 came to you on night 1, and player_7 agrees. If that is true, either player_7 is "
              "the Chanteuse, or player_7 and the Chanteuse both came to you.")
AC2_LINE_2 = ("You were roleblocked on night 2, so the Chanteuse came to you, and player_7 was the Chanteuse. player_2's "
              "report that player_7 came to you that night is true. This does not show that player_2 is the Sentinel.")
AC3_LINE_2 = ("player_9 says you came to player_6 on night 2. You did: you checked player_6 that night. This confirms "
              "that part of player_9's report, not that player_9 is the Sentinel.")
AC4_LINE_2 = ("player_4's will shows player_4 checked player_6 on night 2, so player_4 went to player_6 that night, as "
              "player_9's watch reported. This confirms that part of the report, not that player_9 is the Sentinel.")


def _case(name: str, case_id: str) -> dict:
    for line in (FROZEN / name).read_text().splitlines():
        case = json.loads(line)
        if case["case_id"] == case_id:
            return case
    raise KeyError(case_id)


def _with_speaker_fields(case: dict, fields: dict[tuple[int, int], list[tuple]]) -> dict:
    """The frozen messages, with the speaker field filled by hand from each line's own words."""
    case = copy.deepcopy(case)
    for message in case["state"]["day_channel"]:
        actions = fields.get((message["day"], message["seq"]))
        if actions is not None:
            message["claimed_night_actions"] = [dict(zip(("night", "action", "target", "result", "seen"), a))
                                                for a in actions]
    return case


def _ac1_case() -> dict:
    """AC1 (2f19d908, day 2, the Healer, after player_7's admission). Day 2's lines, filled from their
    words: player_5 "Last night I checked player_9 and they read Suspicious"; player_3 "Night 1 I
    followed player_7 and they went to player_8" (twice); player_7 "yes, I went to player_8 last night"."""
    return _with_speaker_fields(_case("deduction_injection/cases.jsonl", "9b3219e5dc1eb831"), {
        (2, 3): [(1, "investigate", "player_9", "suspicious", [])],
        (2, 10): [(1, "follow", "player_7", "not_said", ["player_8"])],
        (2, 12): [(1, "follow", "player_7", "not_said", ["player_8"])],
        (2, 15): [(1, "visit", "player_8", "not_said", [])],
    })


def _ac3_case() -> dict:
    """AC3 (403f4dbc, day 3, the Investigator, the visit-direction turn). Day 3's lines, filled from
    their words: player_4 "Night 2 I checked player_6 and got Suspicious"; player_9 "Night 2 I watched
    player_6, and the visitors were player_4 and player_8"; player_6 "I didn't visit anyone on night 2"."""
    return _with_speaker_fields(_case("haiku_effort_replay/turn_cases.jsonl", "c52500274ffeccf0"), {
        (3, 3): [(2, "investigate", "player_6", "suspicious", [])],
        (3, 7): [(2, "watch", "player_6", "not_said", ["player_4", "player_8"])],
        (3, 9): [(2, "no_action", "", "not_said", [])],
    })


def _payload(case: dict) -> dict:
    from evaluation.src.replay.hallucination_bench import turn_payload

    return turn_payload(case)


def _seat_lines(payload: dict) -> list[str]:
    block = build_agent_prompt_input(payload)["deduction_seat_before_note"].strip()
    return [line.removeprefix("- ") for line in block.splitlines()[2:]]


AC1_SEAT = [
    "Both wolves are alive and are two of player_2, player_3, player_4, player_5, player_6, player_7, player_9 and "
    "player_10. The Serial Killer is alive and is one of player_2, player_3, player_4, player_5, player_6, player_7, "
    "player_9 and player_10.",
    # Slice 11: the role claims' status (F3, E15), shared, after the census.
    "No one else claims the Investigator or the Trailseer.",  # six without a claim: not named
    AC1_LINE_2,
    "If player_5's check is true, player_9 is a wolf.",  # slice 10: player_5's claimed check, as a premise
]
AC3_SEAT = [
    "Both wolves are alive and are two of player_1, player_2, player_3, player_5, player_6, player_7, player_9 and "
    "player_10. The Necromancer is alive and is one of player_1, player_2, player_3, player_5, player_7, player_9 and "
    "player_10.",
    "The Speculator is one of player_1, player_2, player_3, player_5, player_7, player_9 and player_10, or is "
    "player_8's hidden body.",
    # Slice 11: the role claims' status, and AC3's line 3 (E17) in player_6's entry.
    "No one else claims the Investigator or the Sentinel.",  # seven without a claim: not named
    "player_6 says it visited no one on night 2. That is about where player_6 went. player_9's watch is about who came "
    "to player_6. The two do not conflict.",
    AC3_LINE_2,
    # Slice 10: under player_9's watch player_8 came to player_6, a wolf (line 1): no wolf, no unannounced shot.
    "If player_9's watch is true, player_8's hidden role can only be the Trailseer, the Sigilist or the Healer. The wolf "
    "who killed player_8 on night 2 went to player_8 unseen: the living Illusionist's conceal hides that visit from "
    "every watch and follow. player_8's role was hidden by the living Illusionist, so the Illusionist was alive at the "
    "start of night 2 and went to player_8 that night.",
    "No protection went ahead on player_8 on night 2: one would have saved player_8.",
]


def test_acceptance_case_1_line_2_exactly_and_never_player_7_is_the_chanteuse():
    payload = _payload(_ac1_case())
    assert _seat_lines(payload) == AC1_SEAT
    inputs = build_agent_prompt_input(payload)
    everything = inputs["deduction_public_block"] + inputs["deduction_seat_before_note"] + inputs["night_actions"]
    for sentence in re.split(r"(?<=\.) ", everything):
        if "player_7 is the Chanteuse" in sentence:
            assert sentence.startswith("If that is true, either player_7 is the Chanteuse, or player_7 and the "
                                       "Chanteuse both came to you."), sentence


def test_acceptance_case_1_without_the_hand_filled_fields_says_nothing_of_player_7():
    """The frozen messages as they are: no summary of day 2, no speaker field, so no claim to join."""
    payload = _payload(_case("deduction_injection/cases.jsonl", "9b3219e5dc1eb831"))
    assert AC1_LINE_2 not in _seat_lines(payload)


def test_acceptance_case_2_line_2_exactly_from_the_summary():
    lines = _seat_lines(_payload(_case("haiku_effort_replay/vote_cases.jsonl", "9b827b695a61ece9")))
    assert lines[3] == AC2_LINE_2  # after the census, the role claims' line (slice 10) and their status (slice 11)
    assert not any("player_8 is the Healer" in line for line in lines)


def test_acceptance_case_3_line_2_exactly_and_no_conflict_with_player_6():
    lines = _seat_lines(_payload(_ac3_case()))
    assert lines == AC3_SEAT
    # AC3's must-not-say: that player_6's statement and the watch conflict (line 3 says they do not).
    assert not any(re.search(r"conflict|cannot both be true|contradict|is false", line.replace("do not conflict", ""))
                   for line in lines)


def test_acceptance_case_4_line_2_exactly_from_the_summary():
    lines = _seat_lines(_payload(_case("haiku_effort_replay/vote_cases.jsonl", "5b11c9fd2f6b9b0e")))
    assert lines[5] == AC4_LINE_2  # after the census, AC4's line 4 (slice 10), its lines 3 and 5 (slice 11)


# --- placement and "raised today" -----------------------------------------------------------------------------

def test_every_join_is_in_the_seat_block_never_the_public_block():
    for payload in (_payload(_ac1_case()), _payload(_ac3_case()),
                    _payload(_case("haiku_effort_replay/vote_cases.jsonl", "5b11c9fd2f6b9b0e"))):
        view = seat_view_from_payload(payload)
        blocks = deduction_blocks(view, own_result_lines(view), payload["day_channel"], payload["current_day"])
        assert not [item for item in blocks.public.shown if item.row in ("F1", "F2")]
        assert [item for item in blocks.seat.shown if item.row in ("F1", "F2")]


def test_a_claim_spoken_today_raises_its_target_and_its_sighting_on_its_night():
    lines = [
        _said(3, "player_2", (2, "watch", "player_5", "not_said", ["player_7", "player_8"]), message="I watched."),
        _said(3, "player_4", (0, "sigil", "player_7", "died", []), message="My sigil struck."),  # night not said
        _said(3, "player_6", (3, "visit", "player_1", "not_said", []), message="Tonight."),  # not yet happened
        _said(2, "player_9", (1, "visit", "player_3", "not_said", []), message="Yesterday."),
    ]
    assert raised_today(lines, 3) == {("player_5", 2), ("player_7", 2), ("player_8", 2)}


def test_a_join_goes_in_its_claimants_entry_and_f2_in_its_visitors():
    payload = _payload(_ac1_case())
    view = seat_view_from_payload(payload)
    (f2,) = [item for item in join_items(view)]
    assert (f2.row, f2.subject, f2.grade) == ("F2", "player_7", "follows_if_claims")
    (f1,) = join_items(seat_view_from_payload(_payload(_ac3_case())))
    assert (f1.row, f1.subject, f1.grade, f1.premises) == ("F1", "player_9", "certain", ())


# --- the leak boundary --------------------------------------------------------------------------------------

def test_hidden_roles_and_planted_state_change_nothing():
    watch = _said(3, "player_2", (2, "watch", "player_5", "not_said", ["player_7", "player_8"]))
    swapped = _ac2(serial_killer="player_10", speculator="player_6")
    assert join_items(_view(swapped, "player_5", 3, watch)) == join_items(_view(_ac2(), "player_5", 3, watch))
    table = _ac2()
    payload = {**table.payload("player_5"), "day_channel": [watch], "current_day": 3}
    planted = {**payload, "roles": table.roles, "all_night_actions": table.records, "night_choices": ["anything"]}
    assert join_items(seat_view_from_payload(planted)) == join_items(seat_view_from_payload(payload))


def test_a_claimed_action_the_line_does_not_name_never_reaches_the_record_so_joins_nothing():
    """The 9a guard: the Chanteuse fills in her true block on player_8 but says only "I went somewhere";
    the entry is dropped, so the Healer's roleblock joins nothing."""
    from Agents.schemas import day_discuss_output
    from Agents.schemas.roles import lineup
    from Agents.turn.resolve import resolve_decision

    model = day_discuss_output(lineup("serial_killer", "speculator"))
    claim = model.model_fields["claimed_night_actions"].annotation.__args__[0]
    unsaid = claim(night=1, action="block", target="player_8", result="not_said", seen=[])
    reply = model(reads=[], updated_strategy="", pass_turn=False, claim="none", message="I went somewhere last night.",
                  claimed_night_actions=[unsaid], addressed_targets=[])
    payload = {"player_id": "player_7", "current_day": 2, "day_channel": [], "day_round": "discussion"}
    turn = resolve_decision(reply, {"strategy": None, "strategy_verdicts": [], "memory_verdicts": [], "reads": []},
                            "day_channel", payload, [])
    assert turn.entry.claimed_night_actions == []
    table = Table(_ac2().roles).night(1, ("player_7", "kill", "player_1"), ("player_7", "block", "player_8"),
                                      ("player_6", "kill", "player_1"), ("player_8", "protect", "player_5"))
    assert _joins(table, "player_8", 2, turn.entry) == []


# --- the oracles -----------------------------------------------------------------------------------------------

def _roles_hold_in_every_deal(fact, support: dict[str, set[str]]) -> bool:
    """The role part of a line, in every deal the view allows: a RoleIn, or for a list of branches, the
    union of the roles its branches give each player (one of the branches must be the deal's)."""
    if isinstance(fact, RoleIn):
        return support[fact.player] <= fact.roles
    if isinstance(fact, AnyOf):
        given: dict[str, set[str]] = {}
        for branch in fact.branches:
            for part in branch:
                if isinstance(part, RoleIn):
                    given.setdefault(part.player, set()).update(part.roles)
        return all(support[player] <= roles for player, roles in given.items())
    return True  # a visit: a night choice, which no deal of roles decides


def test_the_brute_force_oracle_on_the_constructed_joins():
    """Every role fact an F1 or F2 line states holds in every deal of the cast that agrees with the
    seat's view (the true deal among them)."""
    watch = _said(3, "player_2", (2, "watch", "player_5", "not_said", ["player_7", "player_8"]))
    two = (_said(2, "player_2", (1, "watch", "player_3", "not_said", ["player_6", "player_7"])),
           _said(2, "player_6", (1, "visit", "player_3", "not_said", [])))
    for table, seat, day, lines in ((_ac2(), "player_5", 3, [watch]), (_second_visitor(), "player_3", 2, two)):
        view = _view(table, seat, day, *lines)
        oracle = oracle_of(table.public(), view)
        assert oracle.allows(table.roles)
        support, deals = oracle.support()
        items = join_items(view)
        assert items and deals >= 1
        for item in items:
            for fact in item.conclusion:
                assert _roles_hold_in_every_deal(fact, support), (item.text, fact)


FORMS = {
    "own action seen": r"^player_\d+ says you (came|went) to ",
    "a will's action seen": r"'s will shows player_\d+ \w+",
    "a visitor's claim seen": r"^player_\d+ says it .* (Your|will shows player_\d+'s) (watch|follow) saw",
    "a sighting seen": r"^player_\d+ says player_\d+ (came|went) to player_\d+ on night \d+\. (Your|player)",
    "the chanteuse known": r"roleblocked on night \d+, so the Chanteuse came to",
    "f2": r"If that is true, either",
}
"""The F1 and F2 forms the random games must reach."""


def truth_oracle(nights: int, seed: int, seats_per_point: int = 2) -> dict[str, int]:
    """Random legal games with truthful and false claims, until `nights` nights: every certain line's
    facts hold; every F2 line's conclusion holds whenever its premise does (the true branch is among
    its branches). Returns how often each form fired and how the premises fell."""
    rng = random.Random(seed)
    played = 0
    counts: dict[str, int] = {}
    while played < nights:
        game = random_game(rng)
        played += len(game.nights)
        for _, snapshot in _continuing_snapshots_of(game):
            if not snapshot.announcements:
                continue
            lines, today = random_claims(rng, game, snapshot)
            # A few seats, and every wolf: only a wolf's own visit can be one the living conceal hid.
            wolves = [p for p in snapshot.living if game.roles[p] in ("chanteuse", "illusionist")]
            seats = rng.sample(snapshot.living, min(seats_per_point, len(snapshot.living)))
            for player in seats + [wolf for wolf in wolves if wolf not in seats]:
                payload = {**game.payload_of(player, snapshot), "day_channel": lines, "current_day": today}
                for item in join_items(seat_view_from_payload(payload)):
                    _check(item, game, counts)
    return counts


def _continuing_snapshots_of(game):
    from tests.factories.random_nights import _game_over

    for snapshot in game.snapshots:
        if not _game_over(game.roles, snapshot.dead_roster):
            yield game, snapshot


def _check(item, game, counts: dict[str, int]) -> None:
    for name, pattern in FORMS.items():
        if re.search(pattern, item.text):
            counts[name] = counts.get(name, 0) + 1
    if item.grade == "certain":
        for fact in item.conclusion:
            assert public_fact_holds(fact, item.night, game), (item.text, fact, game.roles)
        return
    assert item.grade == "follows_if_claims" and item.premises
    if not all(public_fact_holds(fact, item.night, game) for fact in item.premises):
        counts["f2 premise false"] = counts.get("f2 premise false", 0) + 1
        return
    for fact in item.conclusion:
        assert public_fact_holds(fact, item.night, game), (item.text, fact, game.roles)
    for either in item.conclusion:
        if isinstance(either, AnyOf):
            true_branch = next(i for i, branch in enumerate(either.branches)
                               if all(public_fact_holds(part, item.night, game) for part in branch))
            name = f"f2 premise true, branch {true_branch + 1}"
            counts[name] = counts.get(name, 0) + 1


def test_the_truth_oracle_on_random_games_with_true_and_false_claims():
    counts = truth_oracle(nights=10000, seed=20261019)
    assert set(FORMS) <= set(counts), counts
    assert {"f2 premise true, branch 1", "f2 premise true, branch 2", "f2 premise false"} <= set(counts), counts


def test_a_seats_joins_on_random_games_do_not_change_with_planted_state():
    rng = random.Random(20261020)
    for game, snapshot in _continuing_snapshots(rng, 60):
        if not snapshot.announcements:
            continue
        lines, today = random_claims(rng, game, snapshot)
        for player in snapshot.living:
            payload = {**game.payload_of(player, snapshot), "day_channel": lines, "current_day": today}
            planted = {**payload, "roles": game.roles, "all_night_actions": game.records}
            assert join_items(seat_view_from_payload(planted)) == join_items(seat_view_from_payload(payload))


def test_the_brute_force_oracle_on_random_games_for_the_lines_that_state_a_role():
    """The F1 lines with the Chanteuse known and the F2 lines name roles: in every random game's view
    that has one, the roles hold in every deal the view allows."""
    rng = random.Random(20261021)
    checked = 0
    for game, snapshot in _continuing_snapshots(rng, 300):
        if not snapshot.announcements:
            continue
        lines, today = random_claims(rng, game, snapshot)
        for player in snapshot.living:
            view = seat_view_from_payload({**game.payload_of(player, snapshot), "day_channel": lines,
                                           "current_day": today})
            items = [item for item in join_items(view) if item.row == "F2" or len(item.conclusion) > 1]
            if not items:
                continue
            oracle = oracle_of(snapshot, view)
            assert oracle.allows(game.roles)
            support, _ = oracle.support()
            for item in items:
                for fact in item.conclusion:
                    assert _roles_hold_in_every_deal(fact, support), (item.text, fact, game.roles)
            checked += 1
    assert checked >= 100, checked
