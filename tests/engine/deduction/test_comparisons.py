"""Level 6 of the deduction engine (slice 11): the claims against the record and against each other
(Agents/deduction/comparisons/; catalogue Table E, F3's claim status, F7's note for an evil seat, of
evidence/reasoning_failures/deduction_catalogue.md).

- Per comparison, on constructed nights through the real engine and constructed claims: the exact
  line where it fires, and the claims or nights where it must not (a true and a false claim, a whole
  and a partial sighting, a chosen and a completed action, a withdrawn and a corrected claim, a will
  before and after its reveal, the watcher's own visit, a claim said before today that the ledger
  already checks).
- The acceptance cases on their frozen payloads: AC3 line 3 and AC4 lines 3 and 5, exactly, and AC3's
  "must not say" (AC3's same-day claims filled by hand, as in test_joins.py).
- Placement: the status and an evil seat's line shared, after the census and the role claims'
  conditional; the rest in the entry of the player it is about; nothing in the public block.
- The leak boundary: hidden roles swapped and hidden state planted change nothing.
- The oracles. The truth oracle (random legal games, random true and false claims of every kind,
  tests/factories/random_claims.py `random_comparison_claims`): every certain line's facts hold
  (a "cannot both be true" has one of its claims false, a claim called false is false), every
  conditional's conclusion holds whenever its premises do, every "agree" or "do not conflict" line
  is counted where both claims held; no line that sets two claims against each other calls either
  one false. The brute-force oracle (tests/factories/role_assignments.py): the roles a role-claim
  line rules out are ruled out in every deal the view allows, and an evil seat's claimable roles are
  exactly the town and neutral roles some deal agreeing with the public record gives it.
"""

from __future__ import annotations

import random
import re

from Agents.deduction import deduction_blocks, own_result_lines, seat_view_from_payload
from Agents.deduction.comparisons import comparison_items
from Agents.schemas.deduction import AnyOf, Compatible, NotAllTrue, OpenRoles, RoleIn
from Agents.schemas.game_events import DayChannel, DaySummary
from Agents.schemas.roles import NEUTRAL, ROLE_SPECS, TOWN
from tests.engine.deduction.test_candidates import Table, _ne_sp, _sk_sp
from tests.engine.deduction.test_joins import _ac3_case, _case, _payload, _seat_lines
from tests.factories.random_claims import random_comparison_claims
from tests.factories.random_nights import _game_over, public_fact_holds, random_game
from tests.factories.role_assignments import oracle_of


def _said(day: int, player: str, *actions: tuple, claim: str = "none", seq: int = 0) -> DayChannel:
    return DayChannel(day=day, seq=seq, player=player, message="(a claim)", claim=claim,
                      claimed_night_actions=[dict(zip(("night", "action", "target", "result", "seen"), a))
                                             for a in actions])


def _role(day: int, player: str, role: str, seq: int = 0) -> DayChannel:
    return DayChannel(day=day, seq=seq, player=player, message="(a role)", claim=role)


def _view(table: Table, seat: str, day: int, *lines: DayChannel, summaries=()):
    return seat_view_from_payload({**table.payload(seat), "day_channel": list(lines), "day_summaries": list(summaries),
                                   "current_day": day})


def _lines(table: Table, seat: str, day: int, *lines: DayChannel, rows=None, summaries=()) -> list[str]:
    """The comparison lines, the shared ones (the status, an evil seat's roles) left out unless asked."""
    items = comparison_items(_view(table, seat, day, *lines, summaries=summaries), day)
    return [item.text for item in items if (rows is None and item.subject is not None) or (rows and item.row in rows)]


# SK+SP, by seat: player_1 Investigator, player_2 Sentinel, player_3 Trailseer, player_4 Vigilante,
# player_5 Sigilist, player_6 Healer, player_7 Chanteuse, player_8 Illusionist, player_9 Serial Killer,
# player_10 Speculator.

def _night_one() -> Table:
    """The Investigator checks player_5, the Sentinel watches player_5, the Healer protects player_5,
    the Trailseer follows the Healer; the Chanteuse carries the kill on player_4 and blocks player_3;
    the Serial Killer kills player_10."""
    return Table(_sk_sp()).night(1, ("player_7", "kill", "player_4"), ("player_7", "block", "player_3"),
                                 ("player_9", "kill", "player_10"), ("player_1", "investigate", "player_5"),
                                 ("player_2", "watch", "player_5"), ("player_6", "protect", "player_5"),
                                 ("player_3", "follow", "player_6"))


def _two_nights() -> Table:
    """_night_one, the Sigilist voted out on day 2, then night 2: the pack kills player_2, the Serial
    Killer player_1."""
    table = _night_one()
    table.lynch("player_5", 2)
    return table.night(2, ("player_8", "kill", "player_2"), ("player_9", "kill", "player_1"))


DENIAL = _said(2, "player_6", (1, "no_action", "", "not_said", []))
SEEN_AT_5 = _said(2, "player_2", (1, "watch", "player_5", "not_said", ["player_6"]))


# --- E17: the two directions of a visit ------------------------------------------------------------------

def test_e17_where_a_player_went_and_who_came_to_it_do_not_conflict():
    watch = _said(2, "player_2", (1, "watch", "player_6", "not_said", ["player_9"]))
    assert _lines(_night_one(), "player_1", 2, DENIAL, watch) == [
        "player_6 says it visited no one on night 1. That is about where player_6 went. player_2's watch is about who "
        "came to player_6. The two do not conflict."]
    # Only where a careless reader could see a conflict (coordinator, 2026-10-17): a claimed action beside a
    # watch on its claimant is no such pair, nor is a denial beside a watch that saw no one.
    protect = _said(2, "player_6", (1, "protect", "player_5", "no_attack", []))
    assert _lines(_night_one(), "player_1", 2, protect, watch, rows={"E17"}) == []
    no_one = _said(2, "player_2", (1, "watch", "player_6", "no_visitors", []))
    assert _lines(_night_one(), "player_1", 2, DENIAL, no_one, rows={"E17"}) == []


def test_e17_names_the_night_when_one_watcher_watched_the_player_twice():
    table = _night_one().night(2, ("player_8", "kill", "player_1"), ("player_9", "kill", "player_5"))
    denials = _said(3, "player_6", (1, "no_action", "", "not_said", []), (2, "no_action", "", "not_said", []))
    watches = _said(3, "player_2", (1, "watch", "player_6", "not_said", ["player_9"]),
                    (2, "watch", "player_6", "not_said", ["player_9"]))
    assert _lines(table, "player_3", 3, denials, watches) == [
        f"player_6 says it visited no one on night {n}. That is about where player_6 went. player_2's watch on night {n} "
        f"is about who came to player_6. The two do not conflict." for n in (1, 2)]


def test_e17_a_watch_that_saw_no_one_says_nothing_of_whether_the_player_acted():
    watch = _said(2, "player_2", (1, "watch", "player_6", "no_visitors", []))
    assert _lines(_night_one(), "player_1", 2, watch) == [
        "player_2 says no one came to player_6 on night 1. That is about who came to player_6, not about whether "
        "player_6 acted."]
    # Not about the seat itself (it knows what it did), nor a dead player.
    assert _lines(_night_one(), "player_6", 2, watch) == []
    dead = _said(2, "player_2", (1, "watch", "player_4", "no_visitors", []))
    assert _lines(_night_one(), "player_1", 2, dead, rows={"E17"}) == []
    # The wolves' kill on player_4 was a visit no conceal hid: the report is false (F8, slice 12).
    assert _lines(_night_one(), "player_1", 2, dead) == [
        "player_2 says no one came to player_4 on night 1, but a wolf attacked player_4 that night, and a watch shows "
        "that visit: that report is false."]


# --- E2b, E2c: a sighting against a denial ------------------------------------------------------------------

def test_e2c_an_engine_sighting_makes_a_denial_false_and_a_claimed_one_cannot_both_be_true():
    assert _lines(_night_one(), "player_2", 2, DENIAL) == [
        "player_6 says it visited no one on night 1, but your watch saw player_6 come to player_5 that night: that "
        "statement is false."]
    assert _lines(_night_one(), "player_8", 2, SEEN_AT_5, DENIAL) == [
        "player_2 says player_6 came to player_5 on night 1, and player_6 says it visited no one that night. The two "
        "cannot both be true."]


def test_e2b_a_sighting_against_i_did_not_go_there_and_not_against_another_place():
    not_there = _said(2, "player_6", (1, "no_action", "player_5", "not_said", []))
    assert _lines(_night_one(), "player_8", 2, SEEN_AT_5, not_there) == [
        "player_2 says player_6 came to player_5 on night 1, and player_6 says it did not go to player_5 that night. "
        "The two cannot both be true."]
    elsewhere = _said(2, "player_6", (1, "no_action", "player_3", "not_said", []))
    assert _lines(_night_one(), "player_8", 2, SEEN_AT_5, elsewhere) == []


def test_a_roleblocked_player_goes_nowhere():
    blocked = _said(2, "player_6", (1, "protect", "player_5", "roleblocked", []))
    assert _lines(_night_one(), "player_8", 2, SEEN_AT_5, blocked) == [
        "player_2 says player_6 came to player_5 on night 1, and player_6 says it was roleblocked that night. A "
        "roleblocked player's action does not go ahead. The two cannot both be true."]


# --- E3a, E3b, E12: a whole list leaves the visit out ---------------------------------------------------------

def test_e3a_a_whole_watch_against_a_sighting_and_the_watchers_own_visit():
    no_one = _said(2, "player_2", (1, "watch", "player_5", "no_visitors", []))
    follow = _said(2, "player_3", (1, "follow", "player_6", "not_said", ["player_5"]))
    assert _lines(_night_one(), "player_8", 2, no_one, follow, rows={"E3a"}) == [
        "player_3 says player_6 went to player_5 on night 1, and player_2 says no one came to player_5 that night. The "
        "two cannot both be true."]
    # The watcher's own visit is never on its list.
    watcher = _said(2, "player_3", (1, "follow", "player_2", "not_said", ["player_5"]))
    assert _lines(_night_one(), "player_8", 2, no_one, watcher, rows={"E3a", "E3b"}) == []


def test_e3a_a_named_sighting_is_partial_and_rules_nothing_out():
    partial = _said(2, "player_2", (1, "watch", "player_5", "not_said", ["player_1"]))
    follow = _said(2, "player_3", (1, "follow", "player_6", "not_said", ["player_5"]))
    assert _lines(_night_one(), "player_8", 2, partial, follow) == []


def test_e3a_the_seats_own_watch_is_whole():
    made_up = _said(2, "player_8", (1, "watch", "player_5", "not_said", ["player_4"]))
    assert _lines(_night_one(), "player_2", 2, made_up) == [
        # A watch, with no role named, is a claim to be the Sentinel (owner, 2026-10-18), and the seat is it.
        "player_8's claimed night actions are the Sentinel's, but you are the Sentinel: that claim is false.",
        "player_8 says player_4 came to player_5 on night 1, but your watch on player_5 saw everyone who came to "
        "player_5 that night but you, and player_4 was not among them: that report is false."]
    # A watch on player_5 is itself a visit to player_5, which the seat's watch did not see either.
    other_watch = _said(2, "player_8", (1, "watch", "player_5", "not_said", ["player_6"]))
    assert _lines(_night_one(), "player_2", 2, other_watch, rows={"E3a"}) == [
        "player_8 says it watched player_5 on night 1, but your watch on player_5 saw everyone who came to player_5 that "
        "night but you, and player_8 was not among them: that claim is false."]
    true = _said(2, "player_6", (1, "protect", "player_5", "no_attack", []))
    assert _lines(_night_one(), "player_2", 2, true, rows={"E3a", "E3b", "E12"}) == []


def test_the_seat_knows_every_visit_it_made():
    """A town seat's own records show every visit in its name: a sighting of it elsewhere is false."""
    lie = _said(2, "player_8", (1, "watch", "player_3", "not_said", ["player_1"]))
    assert _lines(_night_one(), "player_1", 2, lie) == [
        "player_8 says you came to player_3 on night 1, but you did not go to player_3 that night: that report is "
        "false."]
    # A wolf's own records do not show the pack's visits: nothing.
    lie_about_wolf = _said(2, "player_2", (1, "watch", "player_3", "not_said", ["player_8"]))
    assert _lines(_night_one(), "player_8", 2, lie_about_wolf) == []


def test_e12_a_will_counts_only_from_its_reveal():
    """The Sentinel watched player_5 on night 1 and died on night 2: its will is read the morning after."""
    lie = _said(2, "player_8", (1, "watch", "player_5", "not_said", ["player_4"]))
    before = _night_one()
    assert _lines(before, "player_3", 2, lie) == []
    after = _two_nights()
    lie_today = DayChannel(**{**lie.model_dump(), "day": 3})
    assert _lines(after, "player_3", 3, lie_today, rows={"E12"}) == [
        "player_8 says player_4 came to player_5 on night 1, but player_2's will shows player_2's watch on player_5 saw "
        "everyone who came to player_5 that night but player_2, and player_4 was not among them: that report is false."]


def test_only_the_latest_version_of_a_corrected_claim_is_compared():
    def first(seq):
        return _said(2, "player_8", (1, "watch", "player_3", "not_said", ["player_1"]), seq=seq)

    def corrected(seq):
        return _said(2, "player_8", (1, "watch", "player_5", "not_said", ["player_1"]), seq=seq)

    assert _lines(_night_one(), "player_1", 2, first(0), corrected(1), rows={"E3b"}) == []
    assert _lines(_night_one(), "player_1", 2, corrected(0), first(1), rows={"E3b"}) == [
        "player_8 says you came to player_3 on night 1, but you did not go to player_3 that night: that report is "
        "false."]


def test_e6b_a_roleblock_is_a_visit_to_the_blocked_player():
    """AC2's world: the Investigator, roleblocked on night 2 by player_7 (revealed the Chanteuse), hears
    that no one came to it."""
    from tests.engine.deduction.test_candidates import _ac2

    no_one = _said(3, "player_2", (2, "watch", "player_5", "no_visitors", []))
    assert _lines(_ac2(), "player_5", 3, no_one, rows={"E6b"}) == [
        "player_2 says no one came to you on night 2, but you were roleblocked that night, and a block is a visit to "
        "you: that report is false."]


# --- E2a and E1: two places, or the same place -------------------------------------------------------------

def test_e2a_a_role_that_acts_once_goes_nowhere_else():
    elsewhere = _said(2, "player_2", (1, "watch", "player_4", "not_said", ["player_6"]))
    protect = _said(2, "player_6", (1, "protect", "player_5", "not_said", []))
    assert _lines(_night_one(), "player_1", 2, elsewhere, protect, rows={"E2a"}) == [
        "player_2 says player_6 came to player_4 on night 1, and player_6 says it protected player_5 that night. A "
        "player who protects a player goes nowhere else that night. The two cannot both be true."]
    seen = Table(_sk_sp()).night(1, ("player_7", "kill", "player_4"), ("player_9", "kill", "player_10"),
                                 ("player_6", "protect", "player_5"), ("player_3", "follow", "player_6"))
    check = _said(2, "player_6", (1, "investigate", "player_2", "not_said", []))
    assert _lines(seen, "player_3", 2, check, rows={"E2a"}) == [
        "Your follow saw player_6 go to player_5 on night 1, and player_6 says it checked player_2 that night. A player "
        "who checks a player goes nowhere else that night. So that claim is false."]


def test_e2a_two_places_only_for_the_chanteuse_carrying_the_kill():
    """True: the Chanteuse carried the kill to player_4 and blocked player_3."""
    seen = _said(2, "player_9", (1, "watch", "player_4", "not_said", ["player_7"]))
    went = _said(2, "player_7", (1, "visit", "player_3", "not_said", []))
    (item,) = [i for i in comparison_items(_view(_night_one(), "player_1", 2, seen, went), 2) if i.row == "E2a"]
    assert (item.grade, item.subject, item.text) == (
        "follows_if_claims", "player_7",
        "player_9 says player_7 came to player_4 on night 1, and player_7 says it went to player_3 that night. These "
        "can both be true only if player_7 visited two players that night, which only the Chanteuse does when she "
        "carries the pack's kill.")
    # The Chanteuse's own seat knows player_6 is not her.
    other = (_said(2, "player_2", (1, "watch", "player_4", "not_said", ["player_6"])),
             _said(2, "player_6", (1, "visit", "player_5", "not_said", [])))
    assert _lines(_night_one(), "player_7", 2, *other, rows={"E2a"}) == [
        "player_2 says player_6 came to player_4 on night 1, and player_6 says it went to player_5 that night. Only the "
        "Chanteuse visits two players in one night, and player_6 cannot be the Chanteuse. The two cannot both be true."]


def test_e1_a_sighting_and_the_visitors_own_word_agree_and_show_no_action():
    protect = _said(2, "player_6", (1, "protect", "player_5", "not_said", []))
    assert _lines(_night_one(), "player_1", 2, SEEN_AT_5, protect, rows={"E1"}) == [
        "player_2 says player_6 came to player_5 on night 1, and player_6 says it protected player_5 that night. These "
        "agree; the sighting does not show which action player_6 took."]
    # Against the seat's own watch, the join says it (F1), not E1.
    assert _lines(_night_one(), "player_2", 2, protect, rows={"E1"}) == []


# --- claims against the record ------------------------------------------------------------------------------

def test_e4_a_protection_of_a_player_who_died_that_night():
    went_ahead = _said(2, "player_6", (1, "protect", "player_4", "no_attack", []))
    assert _lines(_night_one(), "player_1", 2, went_ahead) == [
        "player_6 says its protection of player_4 went ahead on night 1, but player_4 died that night, and a "
        "protection that goes ahead stops every attack: that claim is false."]
    # Only chosen: the possible explanations (F8, slice 12), which replaced E4a's conditional.
    chosen = _said(2, "player_6", (1, "protect", "player_4", "not_said", []))
    assert _lines(_night_one(), "player_1", 2, chosen) == [
        "player_6 says it protected player_4 on night 1, but player_4 died that night, and a protection that goes "
        "ahead stops every attack: either player_6 was roleblocked, or player_6's claim is false."]
    for line in (_said(2, "player_6", (1, "protect", "player_5", "no_attack", [])),
                 _said(2, "player_6", (1, "protect", "player_4", "roleblocked", []))):
        assert _lines(_night_one(), "player_1", 2, line, rows={"E4b", "F8"}) == []


def test_e6_a_role_that_cannot_be_roleblocked_needs_no_night():
    for night, said in ((1, " on night 1"), (0, "")):
        line = _said(2, "player_8", (night, "pick", "", "roleblocked", []), claim="fortune_teller")
        table = Table({**_sk_sp(), "player_10": "fortune_teller"}).night(
            1, ("player_7", "kill", "player_4"), ("player_9", "kill", "player_1"))
        assert _lines(table, "player_2", 2, line, rows={"E6"}) == [
            f"player_8 claims the Fortune Teller and says it was roleblocked{said}, but the Fortune Teller cannot be "
            f"roleblocked: the two claims cannot both be true."]
    healer = _said(2, "player_8", (1, "protect", "player_3", "roleblocked", []), claim="healer")
    assert _lines(_night_one(), "player_2", 2, healer, rows={"E6"}) == []


def test_e7_a_check_against_a_known_role_and_the_ledgers_share():
    table = _two_nights()
    today = _said(3, "player_3", (1, "investigate", "player_9", "suspicious", []))
    assert _lines(table, "player_6", 3, today, rows={"E7"}) == []  # player_9 can still be a wolf, for player_6
    assert _lines(table, "player_9", 3, today, rows={"E7"}) == [
        "player_3 says you read Suspicious on night 1, but you are the Serial Killer, who reads Not suspicious: that "
        "claim is false."]
    revealed = _said(3, "player_3", (1, "investigate", "player_5", "suspicious", []))
    assert _lines(table, "player_6", 3, revealed, rows={"E7"}) == [
        "player_3 says player_5 read Suspicious on night 1, but player_5 was revealed as the Sigilist, who reads Not "
        "suspicious: that claim is false."]
    # Said yesterday, the claim ledger checks it against the revealed role: no line here.
    yesterday = DayChannel(**{**revealed.model_dump(), "day": 2})
    assert _lines(table, "player_6", 3, yesterday, rows={"E7"}) == []


# --- E18: the morning places a role's one visit -----------------------------------------------------------

def _placed_night() -> Table:
    """The pack kills player_5 and the Healer saves it; the Vigilante shoots player_8 dead."""
    return Table(_sk_sp()).night(1, ("player_7", "kill", "player_5"), ("player_6", "protect", "player_5"),
                                 ("player_4", "kill", "player_8"))


def test_e18_a_claimed_action_where_the_morning_placed_the_roles_visit_elsewhere():
    healer = _said(2, "player_3", (1, "protect", "player_2", "no_attack", []), claim="healer")
    assert _lines(_placed_night(), "player_1", 2, healer, rows={"E18"}) == [
        "player_3 says it protected player_2 on night 1, but the Healer's protection saved player_5 that night, and "
        "it protects one player a night: that claim is false."]
    vigilante = _said(2, "player_9", (1, "shoot", "player_2", "survived", []), claim="vigilante")
    assert _lines(_placed_night(), "player_1", 2, vigilante) == [  # no "either…or" (F8) beside it
        "player_9 says it shot at player_2 on night 1, but the Vigilante shot player_8 that night, and it fires at one "
        "player a night: that claim is false."]
    struck = Table(_sk_sp()).night(1, ("player_7", "kill", "player_4"), ("player_5", "sigil", "player_7"),
                                   ("player_9", "kill", "player_10"))
    sigil = _said(2, "player_8", (1, "sigil", "player_2", "no_effect", []), claim="sigilist")
    assert _lines(struck, "player_1", 2, sigil, rows={"E18"}) == [
        "player_8 says it set a sigil on player_2 on night 1, but the Sigilist's sigil struck player_7 that night, and "
        "it sets one sigil a night: that claim is false."]


def test_e18_not_for_the_true_claim_nor_where_another_row_says_it():
    true = _said(2, "player_6", (1, "protect", "player_5", "saved_from_attack", []), claim="healer")
    assert _lines(_placed_night(), "player_1", 2, true, rows={"E18"}) == []
    # A protection of a player who died that night: E4b says it, not E18.
    dead = _said(2, "player_3", (1, "protect", "player_8", "no_attack", []), claim="healer")
    assert [i.row for i in comparison_items(_view(_placed_night(), "player_1", 2, dead), 2)
            if i.subject == "player_3"] == ["E4b"]


def _shot_at_the_serial_killer() -> Table:
    return Table(_sk_sp()).night(1, ("player_7", "kill", "player_1"), ("player_9", "kill", "player_10"),
                                 ("player_4", "kill", "player_9"))


def test_e8_a_shot_no_morning_announced():
    table = _shot_at_the_serial_killer()
    # A branch left: the possible explanations (F8, slice 12), which replaced E8a and E8b's conditional.
    assert _lines(table, "player_2", 2, _said(2, "player_4", (1, "shoot", "player_9", "not_said", []))) == [
        "player_4 says it shot at player_9 on night 1, but no shot at player_9 was announced that night: either "
        "player_4 was roleblocked, or player_9 is the Serial Killer, or player_4's claim is false."]
    assert _lines(table, "player_2", 2, _said(2, "player_4", (1, "shoot", "player_9", "survived", []))) == [
        "player_4 says its shot at player_9 went ahead on night 1, but no shot at player_9 was announced that night: "
        "either player_9 is the Serial Killer, or player_4's claim is false."]
    # The Serial Killer's own seat knows player_5 is not it.
    assert _lines(table, "player_9", 2, _said(2, "player_4", (1, "shoot", "player_5", "survived", []))) == [
        "player_4 says its shot at player_5 went ahead on night 1, but no shot at player_5 was announced that night, and "
        "player_5 cannot be the Serial Killer, the only role a shot fails on without an announcement: that claim is "
        "false."]
    assert _lines(table, "player_2", 2, _said(2, "player_4", (1, "shoot", "player_5", "died", []))) == [
        "player_4 says its shot killed player_5 on night 1, but no shot at player_5 was announced that night: that "
        "claim is false."]
    hit = Table(_sk_sp()).night(1, ("player_7", "kill", "player_1"), ("player_9", "kill", "player_10"),
                                ("player_4", "kill", "player_5"))
    assert _lines(hit, "player_2", 2, _said(2, "player_4", (1, "shoot", "player_5", "died", []))) == []


def test_e9_a_sigil_said_to_strike_with_no_sigil_death():
    table = _shot_at_the_serial_killer()
    assert _lines(table, "player_2", 2, _said(2, "player_5", (1, "sigil", "player_8", "died", []))) == [
        "player_5 says its sigil struck player_8 down on night 1, but no sigil killed player_8 that night: that claim is "
        "false."]
    struck = Table(_sk_sp()).night(1, ("player_7", "kill", "player_1"), ("player_9", "kill", "player_10"),
                                   ("player_5", "sigil", "player_7"))
    assert _lines(struck, "player_2", 2, _said(2, "player_5", (1, "sigil", "player_7", "died", []))) == []


def test_e11_more_watches_than_the_sentinel_has():
    table = Table(_sk_sp()).night(1, ("player_7", "kill", "player_4"), ("player_9", "kill", "player_10"))
    table.night(2, ("player_8", "kill", "player_1"), ("player_9", "kill", "player_5"))
    table.night(3, ("player_7", "kill", "player_3"), ("player_9", "kill", "player_6"))
    three = _said(4, "player_2", (1, "watch", "player_7", "not_said", ["player_9"]), (2, "watch", "player_8", "no_visitors", []),
                  (3, "watch", "player_9", "not_said", ["player_8"]))
    assert _lines(table, "player_7", 4, three, rows={"E11"}) == [
        "player_2 says it watched a player on nights 1, 2 and 3, but the Sentinel has 2 watches for the whole game: "
        "player_2 cannot have made them all as the Sentinel."]
    two = _said(4, "player_2", (1, "watch", "player_7", "not_said", ["player_9"]), (2, "watch", "player_8", "no_visitors", []),
                (3, "watch", "player_9", "not_said", []))  # night 3: no outcome said, only chosen
    assert _lines(table, "player_7", 4, two, rows={"E11"}) == []


def test_e14_actions_that_could_not_happen():
    table = _night_one()
    table.lynch("player_7", 2)
    table.night(2, ("player_8", "kill", "player_1"), ("player_9", "kill", "player_5"))
    assert _lines(table, "player_9", 3, _said(3, "player_6", (2, "protect", "player_4", "no_attack", []))) == [
        "player_6 says it protected player_4 on night 2, but player_4 was already dead by then (killed on night 1): "
        "that claim is false."]
    seen_dead = _said(3, "player_3", (2, "watch", "player_8", "not_said", ["player_7"]))
    assert _lines(table, "player_9", 3, seen_dead, rows={"E14"}) == [
        "player_3 says player_7 came to player_8 on night 2, but player_7 was already dead by then (voted out on day 2), "
        "and no one visits in a dead player's name in this game: that report is false."]
    blocked = _said(3, "player_6", (2, "protect", "player_2", "roleblocked", []))
    assert _lines(table, "player_9", 3, blocked, rows={"E14"}) == [
        "player_6 says it was roleblocked on night 2, but the Chanteuse, player_7, was already dead by then (voted out "
        "on day 2), and no one else can roleblock in this game: that claim is false."]
    assert _lines(_night_one(), "player_1", 2, _said(2, "player_6", (1, "protect", "player_6", "no_attack", []))) == [
        "player_6 says it protected itself on night 1, but the Healer cannot protect itself: that claim is false."]


def test_e14_the_necromancer_may_use_the_dead_chanteuses_name():
    table = Table(_ne_sp()).night(1, ("player_7", "kill", "player_4"), ("player_3", "follow", "player_1"))
    table.lynch("player_7", 2)
    table.night(2, ("player_8", "kill", "player_5"), ("player_9", "block", "player_1", "player_7"),
                ("player_1", "investigate", "player_6"), ("player_2", "watch", "player_1"))
    seen = _said(3, "player_2", (2, "watch", "player_1", "not_said", ["player_7"]))
    blocked = _said(3, "player_1", (2, "investigate", "player_6", "roleblocked", []))
    assert _lines(table, "player_3", 3, seen, blocked, rows={"E14"}) == []


# --- the role claims' status and the role claims (E15, F3, F7's note) ---------------------------------------

def test_the_status_line_counter_claims_today_and_no_claims():
    lines = (_role(2, "player_3", "healer"), _role(2, "player_8", "healer"), _role(2, "player_2", "sentinel"))
    assert _lines(_night_one(), "player_1", 2, *lines, rows={"F3+E15"}) == [
        "No one else claims the Sentinel. player_3 and player_8 both claim the Healer; at most one holds it."]
    # A protection with no role named reads as a Healer claim (owner, 2026-10-18), so the status begins.
    # Four players with no role claim: not named (three or fewer are).
    assert _lines(_night_one(), "player_1", 2, _said(2, "player_6", (1, "protect", "player_5", "no_attack", [])),
                  rows={"F3+E15"}) == [
        "player_6 names no role, but says it protected player_5 on night 1, which is the Healer's action: this "
        "reads as a claim to be the Healer. No one else claims the Healer."]
    # A plain denial names no role: still no status.
    assert _lines(_night_one(), "player_1", 2, _said(2, "player_6", (1, "no_action", "", "not_said", [])),
                  rows={"F3+E15"}) == []


def test_an_implied_claim_held_fire_is_the_vigilante():
    """voices-01 (silence calibration games, 2026-10-18): a vigilante that said it held fire both
    nights was read as unclaimed, and the conditional on the role claims named it the Serial Killer."""
    held = _said(3, "player_8", (1, "no_action", "", "held_fire", []), (2, "no_action", "", "held_fire", []))
    assert _lines(_two_nights(), "player_3", 3, _role(3, "player_6", "healer"), held, rows={"F3+E15"}) == [
        "player_8 names no role, but says it held fire on nights 1 and 2, which is the Vigilante's action: this reads "
        "as a claim to be the Vigilante. No one else claims the Healer. player_7 and player_9 have made no role "
        "claim."]
    # The Vigilante (player_4) was revealed on night 1, so the implied claim is checked like a named one.
    assert _lines(_two_nights(), "player_3", 3, _role(3, "player_6", "healer"), held) == [
        "player_8's claimed night actions are the Vigilante's, but player_4 was revealed as the Vigilante: that claim "
        "is false."]
    # Actions of two roles name no single role: no implied claim.
    mixed = _said(3, "player_8", (1, "no_action", "", "held_fire", []), (2, "protect", "player_6", "not_said", []))
    assert "reads as a claim" not in " ".join(_lines(_two_nights(), "player_3", 3, _role(3, "player_6", "healer"), mixed,
                                                     rows={"F3+E15"}))


def test_a_counter_claim_said_before_today_is_the_ledgers():
    both = (_role(2, "player_6", "healer"), _role(2, "player_8", "healer"))
    assert _lines(_two_nights(), "player_3", 3, *both, rows={"F3+E15"}) == [
        "player_7 and player_9 have made no role claim."]
    one_today = (_role(2, "player_6", "healer"), _role(3, "player_8", "healer"))
    assert _lines(_two_nights(), "player_3", 3, *one_today, rows={"F3+E15"}) == [
        "player_6 and player_8 both claim the Healer; at most one holds it. player_7 and player_9 have made no role "
        "claim."]


def test_a_withdrawal_today_and_a_withdrawn_claim_reserves_no_role():
    today = DaySummary(day=3, summary="(today)", structured={"role_claims": [
        {"player": "player_8", "claimed_role": "healer", "kind": "claimed"},
        {"player": "player_8", "claimed_role": "healer", "kind": "retracted"}]})
    assert _lines(_two_nights(), "player_3", 3, _role(2, "player_8", "healer"), _role(3, "player_6", "healer"),
                  rows={"F3+E15"}, summaries=[today]) == [
        "No one else claims the Healer. player_8 claimed the Healer on day 2 and withdrew it on day 3. player_7 and "
        "player_9 have made no role claim."]


def test_a_role_claim_the_seat_knows_is_false():
    table = _two_nights()
    assert _lines(table, "player_3", 3, _role(3, "player_6", "trailseer")) == [
        "player_6 claims the Trailseer, but you are the Trailseer: that claim is false."]
    assert _lines(table, "player_3", 3, _role(3, "player_6", "sigilist")) == [
        "player_6 claims the Sigilist, but player_5 was revealed as the Sigilist: that claim is false."]
    assert _lines(table, "player_3", 3, _role(2, "player_6", "sigilist")) == []  # the ledger's, said yesterday
    assert _lines(table, "player_7", 3, _role(3, "player_6", "illusionist")) == [
        "player_6 claims the Illusionist, but your packmate player_8 is the Illusionist: that claim is false."]
    assert _lines(table, "player_3", 3, _role(3, "player_6", "healer")) == []  # the truth, and the seat cannot tell


def test_an_evil_seat_is_told_which_roles_it_can_claim():
    table = _two_nights()
    for seat in ("player_7", "player_8", "player_9"):
        assert _lines(table, seat, 3, rows={"F7+E15"}) == [
            "You can claim the Trailseer or the Healer without contradicting the public record; no one has claimed any "
            "of them yet."]
    assert _lines(table, "player_6", 3, rows={"F7+E15"}) == []  # a town seat
    # Which of them a living player claims now: claiming it starts a counter-claim (facts only).
    assert _lines(table, "player_9", 3, _role(3, "player_6", "healer"), rows={"F7+E15"}) == [
        "You can claim the Trailseer or the Healer without contradicting the public record; no one has claimed the "
        "Trailseer yet."]
    assert _lines(table, "player_9", 3, _role(3, "player_6", "healer"), _role(3, "player_3", "trailseer"),
                  rows={"F7+E15"}) == [
        "You can claim the Trailseer or the Healer without contradicting the public record; every one of them is "
        "already claimed."]
    early = _lines(_night_one(), "player_9", 2, _role(2, "player_2", "sentinel"), rows={"F7+E15"})
    assert early == ["You can claim the Investigator, the Sentinel, the Trailseer, the Sigilist or the Healer without "
                     "contradicting the public record; no one has claimed the Investigator, the Trailseer, the Sigilist "
                     "or the Healer yet."]


# --- the acceptance cases ------------------------------------------------------------------------------------

AC3_LINE_3 = ("player_6 says it visited no one on night 2. That is about where player_6 went. player_9's watch is about who "
              "came to player_6. The two do not conflict.")
AC4_LINE_3 = "No one else claims the Sentinel. player_3 and player_10 have made no role claim."
AC4_LINE_5 = ("player_9 says no one came to player_3 on night 4. That is about who came to player_3, not about whether "
              "player_3 acted.")


def test_acceptance_case_3_line_3_exactly_and_never_a_conflict():
    lines = _seat_lines(_payload(_ac3_case()))
    assert AC3_LINE_3 in lines
    for line in lines:
        assert not re.search(r"conflict|cannot both be true|contradict|is false", line.replace("do not conflict", ""))


def test_acceptance_case_4_lines_3_and_5_exactly():
    lines = _seat_lines(_payload(_case("haiku_effort_replay/vote_cases.jsonl", "5b11c9fd2f6b9b0e")))
    assert lines[3] == AC4_LINE_3 and lines[4] == AC4_LINE_5


# --- placement ------------------------------------------------------------------------------------------

def test_every_comparison_is_in_the_seat_block_the_shared_lines_after_the_census():
    table = _two_nights()
    lines = [_role(3, "player_6", "healer"), _role(3, "player_3", "healer"),
             _said(3, "player_6", (2, "protect", "player_4", "no_attack", []))]
    view = _view(table, "player_8", 3, *lines)
    blocks = deduction_blocks(view, own_result_lines(view), lines, 3)
    assert not [item for item in blocks.public.shown if item.row.startswith("E") or "E15" in item.row]
    seat = [item.row for item in blocks.seat.shown]
    assert seat.index("F3+E15") < seat.index("F7+E15") < seat.index("E14")
    assert all(row.startswith("F") for row in seat[:seat.index("F3+E15")])
    (e14,) = [item for item in blocks.seat.shown if item.row == "E14"]
    assert e14.subject == "player_6"


# --- the leak boundary ---------------------------------------------------------------------------------------

def test_hidden_roles_and_planted_state_change_nothing():
    lines = (SEEN_AT_5, DENIAL, _role(2, "player_3", "healer"), _said(2, "player_4", (1, "shoot", "player_9", "", [])))
    swapped = {**_sk_sp(), "player_9": "speculator", "player_10": "serial_killer"}
    a = Table(_sk_sp()).night(1, ("player_7", "kill", "player_4"), ("player_9", "kill", "player_8"),
                              ("player_2", "watch", "player_5"), ("player_6", "protect", "player_5"))
    b = Table(swapped).night(1, ("player_7", "kill", "player_4"), ("player_10", "kill", "player_8"),
                             ("player_2", "watch", "player_5"), ("player_6", "protect", "player_5"))
    assert [item.text for item in comparison_items(_view(a, "player_1", 2, *lines), 2)] == \
        [item.text for item in comparison_items(_view(b, "player_1", 2, *lines), 2)]
    payload = {**a.payload("player_1"), "day_channel": list(lines), "current_day": 2}
    planted = {**payload, "roles": a.roles, "all_night_actions": a.records, "night_choices": ["anything"]}
    assert comparison_items(seat_view_from_payload(planted), 2) == comparison_items(seat_view_from_payload(payload), 2)


def test_random_games_do_not_change_with_planted_state():
    rng = random.Random(20261030)
    for game, snapshot in _continuing(rng, 40):
        lines, summaries, today = random_comparison_claims(rng, game, snapshot)
        for player in snapshot.living:
            payload = {**game.payload_of(player, snapshot), "day_channel": lines, "day_summaries": summaries,
                       "current_day": today}
            planted = {**payload, "roles": game.roles, "all_night_actions": game.records}
            assert comparison_items(seat_view_from_payload(planted), today) == \
                comparison_items(seat_view_from_payload(payload), today)


# --- the oracles ---------------------------------------------------------------------------------------------

def _continuing(rng: random.Random, games: int):
    for _ in range(games):
        game = random_game(rng)
        for snapshot in game.snapshots:
            if snapshot.announcements and not _game_over(game.roles, snapshot.dead_roster):
                yield game, snapshot


PAIRED = re.compile(r"cannot both be true|cannot all be true|do not conflict|These agree")


def truth_oracle(nights: int, seed: int, seats: int = 3) -> dict[str, int]:
    """Random legal games with random claims of every kind: every certain line's facts hold, every
    conditional's conclusion holds whenever its premises do. Returns how often each row fired, how the
    conditionals' premises fell, and how often both claims of an "agree" or "do not conflict" line held."""
    rng = random.Random(seed)
    counts: dict[str, int] = {}
    played = 0

    def count(name: str) -> None:
        counts[name] = counts.get(name, 0) + 1

    while played < nights:
        game = random_game(rng)
        played += len(game.nights)
        for snapshot in game.snapshots:
            if not snapshot.announcements or _game_over(game.roles, snapshot.dead_roster):
                continue
            lines, summaries, today = random_comparison_claims(rng, game, snapshot)
            for player in rng.sample(snapshot.living, min(seats, len(snapshot.living))):
                payload = {**game.payload_of(player, snapshot), "day_channel": lines, "day_summaries": summaries,
                           "current_day": today}
                for item in comparison_items(seat_view_from_payload(payload), today):
                    count(item.row)
                    if PAIRED.search(item.text):
                        assert "is false" not in item.text, item.text  # never which of two claims
                    if item.night == 0:
                        continue  # a claim with no night said (E6): no night to check it on
                    if item.grade in ("certain", "possible"):
                        for fact in item.conclusion:
                            assert public_fact_holds(fact, item.night, game), (item.text, fact, game.roles)
                            if isinstance(fact, Compatible) and all(
                                    public_fact_holds(part, item.night, game) for part in fact.first + fact.second):
                                count(f"{item.row} both true")
                            if isinstance(fact, AnyOf):  # F8: which branch held (the last: the claim is false)
                                *explained, (false,) = fact.branches
                                held = any(all(public_fact_holds(part, item.night, game) for part in branch)
                                           for branch in explained)
                                count(f"{item.row} {'explained' if held else 'claim false'}")
                        continue
                    assert item.grade == "follows_if_claims" and item.premises, item
                    if not all(public_fact_holds(fact, item.night, game) for fact in item.premises):
                        count(f"{item.row} premise false")
                        continue
                    count(f"{item.row} premise true")
                    for fact in item.conclusion:
                        assert public_fact_holds(fact, item.night, game), (item.text, fact, game.roles)
    return counts


def test_the_truth_oracle_on_random_games_with_claims_of_every_kind():
    counts = truth_oracle(nights=4000, seed=20261031)
    rows = {"E1", "E2a", "E2b", "E2c", "E3a", "E3b", "E4b", "E6", "E6b", "E7", "E8b", "E9", "E11", "E12",
            "E14", "E17", "E18", "E15+D", "F3+E15", "F7+E15", "F8"}
    assert rows <= set(counts), rows - set(counts)
    assert {"E1 both true", "E17 both true", "E2a premise true", "F8 explained", "F8 claim false"} <= set(counts), counts


def test_the_brute_force_oracle_for_role_claims_and_the_evil_seats_roles():
    """A role claim called false is ruled out in every deal the seat's view allows; an evil seat's
    claimable roles are exactly the town and neutral roles of the public record's support for it."""
    rng = random.Random(20261032)
    checked = {"role claim": 0, "evil": 0}
    for game, snapshot in _continuing(rng, 120):
        lines, summaries, today = random_comparison_claims(rng, game, snapshot)
        public_support, _ = oracle_of(snapshot).support()
        for player in snapshot.living:
            view = seat_view_from_payload({**game.payload_of(player, snapshot), "day_channel": lines,
                                           "day_summaries": summaries, "current_day": today})
            items = [item for item in comparison_items(view, today) if item.row in ("E15+D", "F7+E15")]
            if not items:
                continue
            support = None
            for item in items:
                for fact in item.conclusion:
                    if isinstance(fact, OpenRoles):
                        expected = {role for role in public_support[fact.player]
                                    if ROLE_SPECS[role].side in (TOWN, NEUTRAL)}
                        assert set(fact.roles) == expected, (item.text, expected)
                        checked["evil"] += 1
                    elif isinstance(fact, NotAllTrue):
                        if support is None:
                            oracle = oracle_of(snapshot, view)
                            assert oracle.allows(game.roles)
                            support, _ = oracle.support()
                        (claimed,) = fact.facts
                        assert isinstance(claimed, RoleIn)
                        assert not support[claimed.player] & claimed.roles, (item.text, support[claimed.player])
                        checked["role claim"] += 1
    assert checked["evil"] >= 100 and checked["role claim"] >= 100, checked
