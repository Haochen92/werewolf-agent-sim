"""An evil seat's covers (slice 14, Agents/deduction/comparisons/covers.py; ruling R11): per town role the
seat can claim, the night story that fits its real nights and every claim so far.

- On constructed games through the real engine: the exact line where it fires (a reported sighting, the
  counter-claimed role, the packmate's claim, held nights, two nights), and where it must not (the seat
  already said its night; a role claimed narrows the list; the Chanteuse's two visits; town, neutral and
  Necromancer seats).
- The leak boundary: hidden roles swapped and hidden state planted change nothing.
- On random games: every story names only the seat's real visits of that night, and a held night is one
  with no visit a watch or a follow could show; the brute-force role oracle finds a deal the public
  record allows in which the story is true (the seat holds the role and could have made each visit).
"""

from __future__ import annotations

import random

from Agents.deduction import seat_view_from_payload
from Agents.deduction.comparisons import comparison_items
from Agents.schemas.deduction import RoleIn, VisitAsClaimed
from Agents.schemas.roles import ROLE_SPECS
from tests.engine.deduction.test_candidates import Table, _ne_sp
from tests.engine.deduction.test_comparisons import _continuing, _night_one, _role, _said, _two_nights, _view
from tests.engine.deduction.test_evil_seat import _payload
from tests.factories.random_claims import _every_visit, random_comparison_claims
from tests.factories.role_assignments import add_premise, oracle_of

ROW = "F7+S14"


def _covers(table: Table, seat: str, day: int, *lines) -> list[str]:
    return [item.text for item in comparison_items(_view(table, seat, day, *lines), day) if item.row == ROW]


# SK+SP: player_1 Investigator, player_2 Sentinel, player_3 Trailseer, player_4 Vigilante, player_5 Sigilist,
# player_6 Healer, player_7 Chanteuse, player_8 Illusionist, player_9 Serial Killer, player_10 Speculator.
# Night 1 (_night_one): the Serial Killer kills player_10, the Chanteuse carries the kill on player_4 and blocks
# player_3; the Vigilante (player_4) is revealed dead.

FOLLOWED = _said(2, "player_3", (1, "follow", "player_9", "not_said", ["player_10"]), claim="trailseer")


def test_a_reported_sighting_and_the_stories_that_explain_it():
    assert _covers(_night_one(), "player_9", 2, FOLLOWED) == [
        "player_3 says it saw your visit on night 1. Stories that fit your nights and every claim so far: as the "
        "Investigator, you checked player_10 on night 1, who read Not suspicious; as the Sigilist, you set a sigil on "
        "player_10 on night 1. A Trailseer story fits too (you followed player_10 on night 1), but player_3 claims the "
        "Trailseer: claiming it starts a counter-claim. No other town role you can claim has a story that fits these nights."]
    # The check's reading is fixed: player_10 was revealed as the Speculator (in the screen, a fake Investigator
    # called the revealed Chanteuse Not suspicious). No Sentinel story: player_10 was attacked that night, so a
    # watch would have seen the attacker. The Healer is claimable, but player_10 died: no protection story.


def test_a_night_with_no_visit_is_held_by_the_roles_that_may_hold():
    # The Illusionist did not conceal on night 1: no visit. The Healer and the Trailseer must act each night.
    assert _covers(_night_one(), "player_8", 2) == [
        "Stories that fit your nights and every claim so far: as the Investigator, you kept your check on night 1; as "
        "the Sentinel, you kept your watch on night 1; as the Sigilist, you kept your sigil on night 1. No other town role you can claim has a story that fits these nights."]


def test_a_packmates_claim_is_named():
    assert _covers(_night_one(), "player_8", 2, _role(2, "player_7", "sentinel")) == [
        "Stories that fit your nights and every claim so far: as the Investigator, you kept your check on night 1; as "
        "the Sigilist, you kept your sigil on night 1. A Sentinel story fits too (you kept your watch on night 1), but "
        "your packmate player_7 claims the Sentinel: claiming it starts a counter-claim. No other town role you can claim has a story that fits these nights."]


def test_two_nights_make_one_story():
    # Day 3: only the Trailseer and the Healer are left to claim, and player_1 and player_10 died where it went.
    assert _covers(_two_nights(), "player_9", 3) == [
        "Stories that fit your nights and every claim so far: as the Trailseer, you followed player_10 on night 1 and "
        "followed player_1 on night 2. No other town role you can claim has a story that fits these nights."]


def test_a_night_already_told_and_a_role_already_claimed():
    told = _said(2, "player_9", (1, "no_action", "", "not_said", []))
    assert _covers(_night_one(), "player_9", 2, told) == []
    assert _covers(_night_one(), "player_9", 2, _role(2, "player_9", "sigilist")) == [
        "Stories that fit your nights and every claim so far: as the Sigilist, you set a sigil on player_10 on night 1."]


def test_the_chanteuses_two_visits_have_no_story():
    assert _covers(_night_one(), "player_7", 2) == []  # it went to player_3 and player_4: E2a+own says so


def test_never_for_a_town_or_neutral_seat_nor_the_necromancer():
    for seat in ("player_1", "player_3", "player_6", "player_10"):
        assert _covers(_night_one(), seat, 2) == []
    table = Table(_ne_sp()).night(1, ("player_7", "kill", "player_1"), ("player_7", "block", "player_3"))
    necromancer = next(p for p, role in table.roles.items() if role == "necromancer")
    assert _covers(table, necromancer, 2) == []


# --- the leak boundary ---------------------------------------------------------------------------------

def test_hidden_roles_and_planted_state_change_nothing():
    # Player_2 and player_3 swapped (both unrevealed): the Serial Killer's lines must not change.
    swapped = {**_night_one().roles, "player_2": "trailseer", "player_3": "sentinel"}
    a = _night_one()
    b = Table(swapped).night(1, ("player_7", "kill", "player_4"), ("player_7", "block", "player_2"),
                             ("player_9", "kill", "player_10"), ("player_1", "investigate", "player_5"),
                             ("player_3", "watch", "player_5"), ("player_6", "protect", "player_5"),
                             ("player_2", "follow", "player_6"))
    for seat in ("player_8", "player_9"):
        assert _covers(a, seat, 2, FOLLOWED) == _covers(b, seat, 2, FOLLOWED) != []
        payload = a.payload(seat)
        planted = {**payload, "roles": a.roles, "all_night_actions": a.records, "night_choices": ["anything"]}
        view = seat_view_from_payload({**planted, "day_channel": [FOLLOWED], "current_day": 2})
        assert [i.text for i in comparison_items(view, 2) if i.row == ROW] == _covers(a, seat, 2, FOLLOWED)


# --- random games ----------------------------------------------------------------------------------------

def test_random_games_stories_name_real_visits_and_a_deal_allows_them():
    rng = random.Random(20261050)
    checked = {"stories": 0, "visits": 0, "held": 0, "deals": 0}
    for game, snapshot in _continuing(rng, 160):
        lines, summaries, today = random_comparison_claims(rng, game, snapshot)
        for player in snapshot.living:
            if ROLE_SPECS[game.roles[player]].side not in ("wolves", "lone_killer"):
                continue
            view = seat_view_from_payload(_payload(game, player, snapshot, lines, summaries, today))
            items = [item for item in comparison_items(view, today) if item.row == ROW]
            if not items:
                continue
            (item,) = items
            stories: dict[str, list] = {}
            for claim in item.derivation:
                true_visits = {target for visitor, target in _every_visit(game.nights[claim.night]) if visitor == player}
                if claim.action == "no_action":
                    checked["held"] += 1
                else:
                    assert claim.target in true_visits, (item.text, claim, true_visits)
                    checked["visits"] += 1
                stories.setdefault(_role_of(claim), []).append(claim)
            for role, claims in stories.items():
                oracle = oracle_of(snapshot)
                for k, claim in enumerate(claims):
                    facts = [RoleIn(player, frozenset({role}))] if k == 0 else []
                    if claim.target:
                        facts.append(VisitAsClaimed(player, player, claim.target, shown=True))
                    add_premise(oracle, facts, claim.night, snapshot)
                _, deals = oracle.support()
                assert deals > 0, (item.text, role, claims)
                checked["deals"] += 1
            checked["stories"] += 1
    assert checked["stories"] >= 30 and checked["visits"] >= 20 and checked["held"] >= 20, checked


def _role_of(claim) -> str:
    from Agents.deduction.comparisons.covers import ACTION_OF, HOLD_OF

    if claim.action == "no_action":
        return next(role for role, held in HOLD_OF.items() if held == claim.result)
    return next(role for role, action in ACTION_OF.items() if action == claim.action)
