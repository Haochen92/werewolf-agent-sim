"""An evil seat's own lines (owner, 2026-10-17: evil seats build no fake claims; they get certain facts,
never advice): a hidden body's role the seat's own record shows (Agents/deduction/evil/claimable.py,
catalogue L8), and its own visits of the last two nights against the claims it might make about them
(Agents/deduction/evil/own_visits.py: E4b, E14 and E2a's rule run on the seat's true night).

- Per line, on constructed games through the real engine: the exact sentence where it fires and the
  games that differ in one respect where it must not (a concealed body and a revealed one, the living
  and the reanimated conceal, a role dealt twice, a role no claim is about; a protection claim on a
  survivor, the Chanteuse's second visit hidden by the living conceal, the Chanteuse who did not
  carry, a carrier the seat cannot know, the two-night cap).
- Never for a town or neutral seat, nor the Necromancer's own visits; never for a human seat.
- The leak boundary: hidden roles swapped and hidden state planted change nothing.
- The truth oracle on random games (every stated fact holds in the real game) and the brute-force role
  oracle for the hidden-role line (in every deal the seat's view allows, the body holds the role and no
  living player does; some deal the public record allows gives the seat the role, and the body another).
"""

from __future__ import annotations

import random

from Agents.deduction import seat_view_from_payload
from Agents.deduction.comparisons import comparison_items
from Agents.prompts.prompt_inputs import build_agent_prompt_input
from Agents.schemas.deduction import HeldBy, OpenRoles
from Agents.schemas.roles import ROLE_SPECS
from tests.engine.deduction.test_candidates import Table, _deal, _ne_sp, _sk_sp
from tests.engine.deduction.test_comparisons import _continuing, _role
from tests.factories.random_claims import random_comparison_claims
from tests.factories.random_nights import _game_over, public_fact_holds, random_game
from tests.factories.role_assignments import oracle_of

ROWS = ("F7+L8", "E4b+own", "E14+own", "E2a+own")
"""The rows of these lines."""


def _items(table: Table, seat: str, day: int, *lines, payload: dict | None = None):
    view = seat_view_from_payload({**(payload or table.payload(seat)), "day_channel": list(lines), "current_day": day})
    return [item for item in comparison_items(view, day) if item.row in ROWS]


def _lines(table: Table, seat: str, day: int, *lines, rows=ROWS) -> list[str]:
    return [item.text for item in _items(table, seat, day, *lines) if item.row in rows]


# SK+SP: player_1 Investigator, player_2 Sentinel, player_3 Trailseer, player_4 Vigilante, player_5 Sigilist,
# player_6 Healer, player_7 Chanteuse, player_8 Illusionist, player_9 Serial Killer, player_10 Speculator.
# The carrier: night 1 player_7, night 2 player_8 (seat order, while both wolves live).

HIDDEN_P1 = ("player_1's hidden role was the Investigator: your pack's kill record of night 1 shows it, and the public "
             "record does not. No living player holds the Investigator, so if you claim it, no one can counter-claim "
             "you truthfully.")


def _concealed_night() -> Table:
    """The pack (player_7) kills player_1, the Illusionist conceals it; the Serial Killer kills player_5."""
    return Table(_sk_sp()).night(1, ("player_7", "kill", "player_1"), ("player_7", "block", "player_3"),
                                 ("player_8", "conceal", None), ("player_9", "kill", "player_5"))


# --- the hidden-role claim ------------------------------------------------------------------------------

def test_a_wolf_is_told_the_hidden_role_it_can_claim_with_no_true_counter_claim():
    table = _concealed_night()
    for wolf in ("player_7", "player_8"):
        assert _lines(table, wolf, 2, rows={"F7+L8"}) == [HIDDEN_P1]
    # Not a seat that does not know it: the Serial Killer, a town seat, the neutral.
    for seat in ("player_9", "player_2", "player_10"):
        assert _lines(table, seat, 2, rows={"F7+L8"}) == []
    # A counter-claim already made changes no fact of the line.
    assert _lines(table, "player_7", 2, _role(2, "player_2", "investigator"), rows={"F7+L8"}) == [HIDDEN_P1]


def test_a_revealed_body_gives_no_hidden_role_line():
    table = Table(_sk_sp()).night(1, ("player_7", "kill", "player_1"), ("player_7", "block", "player_3"),
                                  ("player_9", "kill", "player_5"))
    assert _lines(table, "player_7", 2, rows={"F7+L8"}) == []


def test_the_reanimated_conceal_tells_the_necromancer_only():
    # NE+SP: player_9 the Necromancer. The Illusionist voted out on day 2; on night 2 the Necromancer kills
    # the Sentinel through its body, which hides the role while a conceal is left.
    table = Table(_ne_sp()).night(1, ("player_7", "kill", "player_1"), ("player_7", "block", "player_3"))
    table.lynch("player_8", 2)
    table.night(2, ("player_7", "kill", "player_4"), ("player_9", "kill", "player_2", "player_8"))
    assert _lines(table, "player_9", 3, rows={"F7+L8"}) == [
        "player_2's hidden role was the Sentinel: your record of night 2 shows it, and the public record does not. "
        "No living player holds the Sentinel, so if you claim it, no one can counter-claim you truthfully."]
    assert _lines(table, "player_7", 3, rows={"F7+L8"}) == []  # the pack does not learn it


def test_the_living_conceal_does_not_tell_the_necromancer():
    table = Table(_ne_sp()).night(1, ("player_7", "kill", "player_2"), ("player_7", "block", "player_3"),
                                  ("player_8", "conceal", None))
    assert _lines(table, "player_9", 2, rows={"F7+L8"}) == []
    assert len(_lines(table, "player_8", 2, rows={"F7+L8"})) == 1


def test_a_role_no_claim_is_about_gives_no_line():
    # NE+SP: from night 3 the living conceal can hide the Necromancer, a lone killer: no claim is about it.
    table = Table(_ne_sp()).night(1, ("player_7", "kill", "player_1"), ("player_7", "block", "player_3"))
    table.night(2, ("player_8", "kill", "player_2"))
    table.night(3, ("player_8", "kill", "player_9"), ("player_8", "conceal", None))
    assert [d.concealed for d in table.dead if d.player == "player_9"] == [True]
    assert _lines(table, "player_7", 4, rows={"F7+L8"}) == []


def test_a_role_dealt_twice_gives_no_line():
    """No standard cast deals a role twice; the guard holds if one ever does."""
    roles = _deal("investigator", "investigator", "trailseer", "vigilante", "sigilist", "healer", "chanteuse",
                  "illusionist", "serial_killer", "speculator")
    table = Table(roles).night(1, ("player_7", "kill", "player_1"), ("player_7", "block", "player_3"),
                               ("player_8", "conceal", None))
    assert [d.concealed for d in table.dead if d.player == "player_1"] == [True]
    view = seat_view_from_payload(table.payload("player_7"))
    assert view.cast_role_counts["investigator"] == 2
    assert _lines(table, "player_7", 2, rows={"F7+L8"}) == []


# --- the seat's own visits ------------------------------------------------------------------------------

def test_a_protection_claim_on_a_player_the_seat_visited_who_died():
    table = _concealed_night()
    assert _lines(table, "player_9", 2, rows={"E4b+own"}) == [
        "On night 1 you went to player_5, and player_5 died that night: a claim that you protected player_5 then "
        "would be false, since a protection that goes ahead stops every attack."]
    # The carrier's visit to the victim the living conceal hid is still a visit: the claim is still false.
    assert _lines(table, "player_7", 2, rows={"E4b+own"}) == [
        "On night 1 you went to player_1, and player_1 died that night: a claim that you protected player_1 then "
        "would be false, since a protection that goes ahead stops every attack."]
    # The Illusionist's conceal is a visit to the pack's victim.
    assert len(_lines(table, "player_8", 2, rows={"E4b+own"})) == 1


def test_a_protection_claim_on_a_survivor_gives_no_line():
    table = Table(_sk_sp()).night(1, ("player_7", "kill", "player_1"), ("player_7", "block", "player_3"),
                                  ("player_9", "kill", "player_5"), ("player_6", "protect", "player_5"))
    assert _lines(table, "player_9", 2, rows={"E4b+own"}) == []
    assert _lines(table, "player_7", 2, rows={"E4b+own"}) == [
        "On night 1 you went to player_1, and player_1 died that night: a claim that you protected player_1 then "
        "would be false, since a protection that goes ahead stops every attack."]


def test_a_claim_on_a_player_already_dead_when_the_night_began():
    table = Table(_sk_sp()).night(1, ("player_7", "kill", "player_1"), ("player_7", "block", "player_3"),
                                  ("player_9", "kill", "player_6"))
    table.lynch("player_4", 2)
    table.night(2, ("player_8", "kill", "player_2"), ("player_7", "block", "player_5"), ("player_9", "kill", "player_10"))
    assert _lines(table, "player_9", 3, rows={"E14+own"}) == [
        "player_1, player_4 and player_6 were already dead when night 2 began (player_1 killed on night 1, player_4 "
        "voted out on day 2, player_6 killed on night 1): a claim that you checked, watched, followed or protected "
        "any of them on night 2 would be false."]
    table = Table(_sk_sp()).night(1, ("player_7", "kill", "player_1"), ("player_7", "block", "player_3"),
                                  ("player_9", "kill", "player_6"), ("player_6", "protect", "player_1"))
    table.night(2, ("player_8", "kill", "player_2"), ("player_7", "block", "player_5"), ("player_9", "kill", "player_10"))
    assert _lines(table, "player_7", 3, rows={"E14+own"}) == [
        "player_6 was already dead when night 2 began (killed on night 1): a claim that you checked, watched, followed "
        "or protected player_6 on night 2 would be false."]
    # Night 1 has no one dead before it.
    assert _lines(_concealed_night(), "player_9", 2, rows={"E14+own"}) == []


def test_the_chanteuse_who_carried_the_kill_and_blocked_elsewhere_made_two_visits():
    table = Table(_sk_sp()).night(1, ("player_7", "kill", "player_1"), ("player_7", "block", "player_3"),
                                  ("player_9", "kill", "player_5"))
    assert _lines(table, "player_7", 2, rows={"E2a+own"}) == [
        "On night 1 you went to player_1 and player_3, and neither visit was hidden: a follow of you that night, or a "
        "watch on each of them, shows two visits, and only the Chanteuse visits two players in a night."]
    # The living conceal hid the carrier's visit to the victim: only one visit shows.
    assert _lines(_concealed_night(), "player_7", 2, rows={"E2a+own"}) == []
    # Her block on the pack's own victim: one place.
    same = Table(_sk_sp()).night(1, ("player_7", "kill", "player_1"), ("player_7", "block", "player_1"))
    assert _lines(same, "player_7", 2, rows={"E2a+own"}) == []
    # Night 2: the Illusionist carried, and the Chanteuse visited one player.
    table.night(2, ("player_8", "kill", "player_2"), ("player_7", "block", "player_6"))
    assert _lines(table, "player_7", 3, rows={"E2a+own"}) == [
        "On night 1 you went to player_1 and player_3, and neither visit was hidden: a follow of you that night, or a "
        "watch on each of them, shows two visits, and only the Chanteuse visits two players in a night."]


def test_the_carrier_is_known_only_when_the_seat_knows_every_wolf():
    table = Table(_sk_sp()).night(1, ("player_7", "kill", "player_1"), ("player_7", "block", "player_3"))
    payload = {**table.payload("player_7"), "pack_roles": {}}  # a payload with no pack on it
    assert _items(table, "player_7", 2, payload=payload) == []
    # Once the other wolf is revealed dead, the seat knows every wolf: alone, it carries.
    table.lynch("player_8", 2)
    table.night(2, ("player_7", "kill", "player_2"), ("player_7", "block", "player_6"))
    texts = [item.text for item in _items(table, "player_7", 3, payload={**table.payload("player_7"), "pack_roles": {}})]
    assert ("On night 2 you went to player_2 and player_6, and neither visit was hidden: a follow of you that night, "
            "or a watch on each of them, shows two visits, and only the Chanteuse visits two players in a night.") in texts


def test_only_the_two_most_recent_nights():
    table = Table(_sk_sp()).night(1, ("player_7", "kill", "player_1"), ("player_7", "block", "player_3"),
                                  ("player_9", "kill", "player_5"))
    table.night(2, ("player_8", "kill", "player_2"), ("player_7", "block", "player_6"), ("player_9", "kill", "player_10"))
    table.night(3, ("player_7", "kill", "player_4"), ("player_7", "block", "player_6"), ("player_9", "kill", "player_3"))
    nights = {item.night for item in _items(table, "player_9", 4) if item.row != "F7+L8"}
    assert nights == {2, 3}
    assert [item.night for item in _items(table, "player_9", 4) if item.row == "E4b+own"] == [2, 3]
    assert [item.night for item in _items(table, "player_9", 4) if item.row == "E14+own"] == [3]  # last night only


def test_never_for_a_town_or_neutral_seat_nor_the_necromancers_own_visits():
    table = Table(_ne_sp()).night(1, ("player_7", "kill", "player_1"), ("player_7", "block", "player_3"))
    table.lynch("player_5", 2)
    table.night(2, ("player_7", "kill", "player_4"), ("player_9", "sigil", "player_2", "player_5"))
    for seat in ("player_3", "player_6", "player_10"):
        assert _items(table, seat, 3) == []
    assert [item.row for item in _items(table, "player_9", 3)] == []  # player_5 the Sigilist: no conceal, no own visit


def test_never_for_a_human_seat():
    from tests.fixtures.day_discuss_prompt_golden import speaker_payload

    for role in ("chanteuse", "illusionist", "serial_killer"):
        payload = speaker_payload(role)
        ai = build_agent_prompt_input(payload)
        human = build_agent_prompt_input({**payload, "human_player": True})
        assert "would be false" in ai["deduction_seat_before_note"] or "You can claim" in ai["deduction_seat_before_note"]
        assert human["deduction_seat_before_note"] == ""


# --- the leak boundary ---------------------------------------------------------------------------------

def test_hidden_roles_and_planted_state_change_nothing():
    swapped = {**_sk_sp(), "player_2": "trailseer", "player_3": "sentinel", "player_9": "speculator",
               "player_10": "serial_killer"}
    a = Table(_sk_sp()).night(1, ("player_7", "kill", "player_1"), ("player_7", "block", "player_5"),
                              ("player_8", "conceal", None), ("player_9", "kill", "player_6"))
    b = Table(swapped).night(1, ("player_7", "kill", "player_1"), ("player_7", "block", "player_5"),
                             ("player_8", "conceal", None), ("player_10", "kill", "player_6"))
    for wolf in ("player_7", "player_8"):
        assert [i.text for i in _items(a, wolf, 2)] == [i.text for i in _items(b, wolf, 2)] != []
        payload = a.payload(wolf)
        planted = {**payload, "roles": a.roles, "all_night_actions": a.records, "night_choices": ["anything"]}
        assert _items(a, wolf, 2, payload=planted) == _items(a, wolf, 2, payload=payload)


def _payload(game, player, snapshot, lines, summaries, today) -> dict:
    """A random game's payload with the wolf's pack on it (the real payload builders put it there)."""
    pack = {p: game.roles[p] for p in snapshot.living if ROLE_SPECS[game.roles[p]].pack}
    return {**game.payload_of(player, snapshot), "pack_roles": pack if player in pack else {},
            "day_channel": lines, "day_summaries": summaries, "current_day": today}


def test_random_games_town_seats_never_and_planted_state_changes_nothing():
    rng = random.Random(20261040)
    seen = 0
    for game, snapshot in _continuing(rng, 60):
        lines, summaries, today = random_comparison_claims(rng, game, snapshot)
        for player in snapshot.living:
            payload = _payload(game, player, snapshot, lines, summaries, today)
            items = [i for i in comparison_items(seat_view_from_payload(payload), today) if i.row in ROWS]
            if ROLE_SPECS[game.roles[player]].side not in ("wolves", "lone_killer"):
                assert items == [], (game.roles[player], items)
                continue
            seen += bool(items)
            planted = {**payload, "roles": game.roles, "all_night_actions": game.records}
            assert [i for i in comparison_items(seat_view_from_payload(planted), today) if i.row in ROWS] == items
    assert seen >= 20, seen


# --- the oracles ---------------------------------------------------------------------------------------

def truth_oracle(nights: int, seed: int) -> dict[str, int]:
    """Every evil seat of random legal games with random claims: every fact of these lines holds in the
    real game. Returns how often each row fired."""
    rng = random.Random(seed)
    counts: dict[str, int] = {}
    played = 0
    while played < nights:
        game = random_game(rng)
        played += len(game.nights)
        for snapshot in game.snapshots:
            if not snapshot.announcements or _game_over(game.roles, snapshot.dead_roster):
                continue
            lines, summaries, today = random_comparison_claims(rng, game, snapshot)
            for player in snapshot.living:
                if ROLE_SPECS[game.roles[player]].side not in ("wolves", "lone_killer"):
                    continue
                view = seat_view_from_payload(_payload(game, player, snapshot, lines, summaries, today))
                for item in comparison_items(view, today):
                    if item.row not in ROWS:
                        continue
                    counts[item.row] = counts.get(item.row, 0) + 1
                    counts[f"{item.row} {game.roles[player]}"] = counts.get(f"{item.row} {game.roles[player]}", 0) + 1
                    for fact in item.conclusion:
                        assert public_fact_holds(fact, item.night, game), (item.text, fact, game.roles)
    return counts


def test_the_truth_oracle_on_random_games():
    counts = truth_oracle(nights=4000, seed=20261041)
    assert set(ROWS) <= set(counts), counts
    assert {"F7+L8 necromancer", "F7+L8 chanteuse", "F7+L8 illusionist", "E4b+own serial_killer",
            "E4b+own chanteuse", "E4b+own illusionist", "E14+own serial_killer"} <= set(counts), counts


def test_the_brute_force_oracle_for_the_hidden_role_line():
    """In every deal the seat's view allows, the body holds the role and no living player does; some deal
    the public record allows gives the seat the role (so the body another one)."""
    rng = random.Random(20261042)
    checked = 0
    for game, snapshot in _continuing(rng, 400):
        for player in snapshot.living:
            if not (ROLE_SPECS[game.roles[player]].pack or game.roles[player] == "necromancer"):
                continue
            view = seat_view_from_payload(_payload(game, player, snapshot, [], [], 0))
            items = [i for i in comparison_items(view, max(a.night for a in snapshot.announcements) + 1)
                     if i.row == "F7+L8"]
            if not items:
                continue
            oracle = oracle_of(snapshot, view)
            assert oracle.allows(game.roles)
            support, _ = oracle.support()
            public, _ = oracle_of(snapshot).support()
            for item in items:
                held, open_ = item.conclusion
                assert isinstance(held, HeldBy) and isinstance(open_, OpenRoles)
                (body,) = held.players
                assert support[body] == {held.role}, (item.text, support[body])
                assert not any(held.role in support[p] for p in snapshot.living), item.text
                assert held.role in public[player] and public[body] - {held.role}, (item.text, public[body])
                checked += 1
    assert checked >= 30, checked
