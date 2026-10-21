"""Level 7 of the deduction engine (slice 12): possible explanations of a claim (F8) and the budgets the
public counts across nights (F9) (Agents/deduction/explanations/; catalogue Table F, §0 grade 3, of
evidence/reasoning_failures/deduction_catalogue.md); and AC2 line 3, a sighting of the known
Chanteuse read with the morning (Agents/deduction/comparisons/block_visits.py).

- Per form, on constructed nights through the real engine and constructed claims: the exact line, and
  the claims or nights where it must not fire or must fire with fewer branches (a shot the morning
  shows; a kill claimed; a shot said to have gone ahead; no one left to roleblock; no silent immune
  role that night; the seat itself the target; a claimant that cannot hold the role; a protected
  player who lived; a named sighting; the living conceal against a kill in the open).
- F9: the self-bets after two announced saves, by cast (who can still save it); the conceals after two
  hidden deaths, and not beside B6; not after one.
- Placement: F8 in the claimant's entry of the seat block; F9 in the public block.
- The leak boundary: hidden roles swapped and planted state change nothing.
- The oracles. Truth (random legal games, true and false claims of every kind): every F8 list holds
  (one branch true; which one is counted, the claim-false branch apart), every certain F8 line's
  claim is false, every F9 fact holds. Brute force (tests/factories/role_assignments.py): an F8 list
  leaves out no immune role any deal agreeing with the seat's view gives the target.
"""

from __future__ import annotations

import random

from Agents.deduction import deduction_blocks, own_result_lines, public_record, seat_view_from_payload
from Agents.deduction.comparisons import comparison_items
from Agents.deduction.explanations import budget_items
from Agents.deduction.night_state import roles_always_immune
from Agents.deduction.public import public_items
from Agents.schemas.deduction import AnyOf, NotAllTrue, NoUsesLeft, RoleIn
from tests.engine.deduction.test_candidates import Table, _ne_sp, _sk_sp
from tests.engine.deduction.test_comparisons import _continuing, _role, _said, _view
from tests.factories.random_claims import random_comparison_claims
from tests.factories.random_nights import public_fact_holds, random_game, _game_over
from tests.factories.role_assignments import oracle_of


def _f8(table: Table, seat: str, day: int, *lines) -> list[str]:
    return [item.text for item in comparison_items(_view(table, seat, day, *lines), day) if item.row == "F8"]


def _budgets(table: Table) -> list[str]:
    record = table.public()
    return [item.text for item in budget_items(record, public_items(record))]


# SK+SP, by seat: player_1 Investigator, player_2 Sentinel, player_3 Trailseer, player_4 Vigilante,
# player_5 Sigilist, player_6 Healer, player_7 Chanteuse, player_8 Illusionist, player_9 Serial Killer,
# player_10 Speculator. NE+SP: player_9 the Necromancer.

def _shot_at_the_serial_killer() -> Table:
    return Table(_sk_sp()).night(1, ("player_7", "kill", "player_1"), ("player_9", "kill", "player_10"),
                                 ("player_4", "kill", "player_9"))


def _chanteuse_voted_out() -> Table:
    """SK+SP: the Chanteuse is voted out on day 2, so no one can roleblock on night 2."""
    table = Table(_sk_sp()).night(1, ("player_7", "kill", "player_1"), ("player_7", "block", "player_3"),
                                  ("player_9", "kill", "player_10"))
    table.lynch("player_7", 2)
    return table.night(2, ("player_8", "kill", "player_2"), ("player_9", "kill", "player_3"))


# --- F8: a shot ------------------------------------------------------------------------------------

def test_f8_a_shot_no_shot_announced_lists_every_branch():
    """The catalogue's example (§0 grade 3), worded with the night and the role that cannot be killed."""
    shot = _said(2, "player_4", (1, "shoot", "player_9", "not_said", []))
    assert _f8(_shot_at_the_serial_killer(), "player_2", 2, shot) == [
        "player_4 says it shot at player_9 on night 1, but no shot at player_9 was announced that night: either "
        "player_4 was roleblocked, or player_9 is the Serial Killer, or player_4's claim is false."]
    # Said to have gone ahead: not roleblocked (L13).
    went = _said(2, "player_4", (1, "shoot", "player_9", "survived", []))
    assert _f8(_shot_at_the_serial_killer(), "player_2", 2, went) == [
        "player_4 says its shot at player_9 went ahead on night 1, but no shot at player_9 was announced that night: "
        "either player_9 is the Serial Killer, or player_4's claim is false."]


def test_f8_a_shot_at_a_player_who_cannot_be_immune_or_on_a_night_no_one_could_block():
    table = _chanteuse_voted_out()
    # player_3 died to the Serial Killer on night 2: not immune, and no one could roleblock.
    at_the_dead = _said(3, "player_4", (2, "shoot", "player_3", "not_said", []))
    assert _f8(table, "player_6", 3, at_the_dead) == [
        "player_4 says it shot at player_3 on night 2, but no shot at player_3 was announced that night. No one could "
        "roleblock that night, and player_3 cannot be the Serial Killer, the only role a shot fails on without an "
        "announcement, so that claim is false."]
    # player_5 could be the Serial Killer, for the Healer: one branch left.
    assert _f8(table, "player_6", 3, _said(3, "player_4", (2, "shoot", "player_5", "not_said", []))) == [
        "player_4 says it shot at player_5 on night 2, but no shot at player_5 was announced that night: either "
        "player_5 is the Serial Killer, or player_4's claim is false."]
    # The Serial Killer's own seat knows player_5 is not it.
    assert _f8(table, "player_9", 3, _said(3, "player_4", (2, "shoot", "player_5", "not_said", []))) == [
        "player_4 says it shot at player_5 on night 2, but no shot at player_5 was announced that night. No one could "
        "roleblock that night, and player_5 cannot be the Serial Killer, the only role a shot fails on without an "
        "announcement, so that claim is false."]


def test_f8_the_necromancer_is_immune_on_nights_1_and_2_and_its_block_through_the_body_is_a_branch():
    ne = Table(_ne_sp()).night(1, ("player_7", "kill", "player_1"), ("player_7", "block", "player_3"),
                               ("player_4", "kill", "player_9"))
    assert _f8(ne, "player_2", 2, _said(2, "player_4", (1, "shoot", "player_9", "not_said", []))) == [
        "player_4 says it shot at player_9 on night 1, but no shot at player_9 was announced that night: either "
        "player_4 was roleblocked, or player_9 is the Necromancer, or player_4's claim is false."]
    ne.lynch("player_7", 2)
    ne.night(2, ("player_8", "kill", "player_2"))
    # Night 2: the Necromancer is still immune in silence, and it can block through the Chanteuse's body.
    assert _f8(ne, "player_3", 3, _said(3, "player_4", (2, "shoot", "player_5", "not_said", []))) == [
        "player_4 says it shot at player_5 on night 2, but no shot at player_5 was announced that night: either "
        "player_4 was roleblocked, or player_5 is the Necromancer, or player_4's claim is false."]
    ne.night(3, ("player_8", "kill", "player_6"))
    # Night 3: no one is immune in silence; the block through the body is the one branch left.
    assert _f8(ne, "player_3", 4, _said(4, "player_4", (3, "shoot", "player_5", "not_said", []))) == [
        "player_4 says it shot at player_5 on night 3, but no shot at player_5 was announced that night: either "
        "player_4 was roleblocked, or player_4's claim is false."]


def test_f8_no_line_when_the_morning_shows_the_shot_or_the_claim_is_table_es():
    table = _shot_at_the_serial_killer()
    hit = Table(_sk_sp()).night(1, ("player_7", "kill", "player_1"), ("player_9", "kill", "player_10"),
                                ("player_4", "kill", "player_5"))
    assert _f8(hit, "player_2", 2, _said(2, "player_4", (1, "shoot", "player_5", "not_said", []))) == []
    # A kill claimed (E8b says it is false), a roleblock said, the seat itself the immune target.
    assert _f8(table, "player_2", 2, _said(2, "player_4", (1, "shoot", "player_5", "died", []))) == []
    assert _f8(table, "player_2", 2, _said(2, "player_4", (1, "shoot", "player_5", "roleblocked", []))) == []
    assert _f8(table, "player_9", 2, _said(2, "player_4", (1, "shoot", "player_9", "not_said", []))) == []
    # A shot on the Fortune Teller's self-bet is announced with the shot's type: the claim fits.
    ft = Table({**_sk_sp(), "player_10": "fortune_teller"}).night(
        1, ("player_7", "kill", "player_1"), ("player_9", "kill", "player_2"), ("player_4", "kill", "player_10"),
        ("player_10", "bet", "player_10"))
    assert _f8(ft, "player_6", 2, _said(2, "player_4", (1, "shoot", "player_10", "not_said", []))) == []


def test_f8_a_claimant_who_cannot_hold_the_role_made_a_false_claim():
    table = _shot_at_the_serial_killer()
    assert _f8(table, "player_4", 2, _said(2, "player_2", (1, "shoot", "player_9", "not_said", []))) == [
        "player_2 says it shot at player_9 on night 1, but no shot at player_9 was announced that night. Only the "
        "Vigilante shoots, and you are the Vigilante, so that claim is false."]


# --- F8: a protection --------------------------------------------------------------------------------

def test_f8_a_protection_of_a_player_who_died():
    night = Table(_sk_sp()).night(1, ("player_7", "kill", "player_4"), ("player_7", "block", "player_3"),
                                  ("player_9", "kill", "player_10"), ("player_6", "protect", "player_5"))
    assert _f8(night, "player_1", 2, _said(2, "player_6", (1, "protect", "player_4", "not_said", []))) == [
        "player_6 says it protected player_4 on night 1, but player_4 died that night, and a protection that goes "
        "ahead stops every attack: either player_6 was roleblocked, or player_6's claim is false."]
    # A player who lived, and a protection said to have gone ahead (E4b's), give no F8 line.
    assert _f8(night, "player_1", 2, _said(2, "player_6", (1, "protect", "player_5", "not_said", []))) == []
    assert _f8(night, "player_1", 2, _said(2, "player_6", (1, "protect", "player_4", "no_attack", []))) == []
    assert _f8(_chanteuse_voted_out(), "player_6", 3, _said(3, "player_5", (2, "protect", "player_2", "not_said", []))) == [
        "player_5 says it protected player_2 on night 2, but player_2 died that night, and a protection that goes "
        "ahead stops every attack. No one could roleblock that night, so that claim is false."]


# --- F8: a watch that saw no one ---------------------------------------------------------------------

def test_f8_a_watch_that_saw_no_one_against_a_visit_the_morning_shows():
    night = Table(_sk_sp()).night(1, ("player_7", "kill", "player_4"), ("player_9", "kill", "player_10"),
                                  ("player_6", "protect", "player_5"))
    assert _f8(night, "player_1", 2, _said(2, "player_2", (1, "watch", "player_10", "no_visitors", []))) == [
        "player_2 says no one came to player_10 on night 1, but the Serial Killer attacked player_10 that night, and a "
        "watch shows that visit: that report is false."]
    # The pack's kill with no conceal: its killer's visit shows (L4), so no branch is left.
    assert _f8(night, "player_1", 2, _said(2, "player_2", (1, "watch", "player_4", "no_visitors", []))) == [
        "player_2 says no one came to player_4 on night 1, but a wolf attacked player_4 that night, and a watch shows "
        "that visit: that report is false."]
    # A named list is partial (L12); a player no one was announced on: E17's, not F8's.
    assert _f8(night, "player_1", 2, _said(2, "player_2", (1, "watch", "player_10", "not_said", ["player_3"]))) == []
    assert _f8(night, "player_1", 2, _said(2, "player_2", (1, "watch", "player_5", "no_visitors", []))) == []
    saved = Table(_sk_sp()).night(1, ("player_7", "kill", "player_1"), ("player_9", "kill", "player_5"),
                                  ("player_6", "protect", "player_5"))
    assert _f8(saved, "player_3", 2, _said(2, "player_2", (1, "watch", "player_5", "no_visitors", []))) == [
        "player_2 says no one came to player_5 on night 1, but the Serial Killer attacked player_5 that night, and a "
        "watch shows that visit: that report is false."]


def test_f8_the_living_conceal_hides_the_killer_and_the_illusionists_visit_only_when_it_killed():
    hidden = Table(_sk_sp()).night(1, ("player_7", "kill", "player_4"), ("player_8", "conceal", None),
                                   ("player_9", "kill", "player_10"))
    assert _f8(hidden, "player_1", 2, _said(2, "player_2", (1, "watch", "player_4", "no_visitors", []))) == [
        "player_2 says no one came to player_4 on night 1, but the living Illusionist went to player_4 that night to "
        "hide their role, a visit a watch shows unless the Illusionist made the kill itself: either the Illusionist "
        "carried the pack's kill, or player_2's report is false."]


def test_f8_the_necromancers_visit_shows_the_bodys_name():
    table = Table(_ne_sp()).night(1, ("player_7", "kill", "player_1"), ("player_7", "block", "player_3"))
    table.lynch("player_4", 2)
    table.night(2, ("player_7", "kill", "player_2"), ("player_9", "kill", "player_5", "player_4"))
    assert _f8(table, "player_6", 3, _said(3, "player_3", (2, "watch", "player_5", "no_visitors", []))) == [
        "player_3 says no one came to player_5 on night 2, but the Necromancer went to player_5 that night under "
        "player_4's name, and a watch shows that visit: that report is false."]


# --- F9 ----------------------------------------------------------------------------------------------

def _self_bets(roles: dict[str, str], healer_out: bool = False) -> Table:
    """The Fortune Teller (player_10) bets on itself on nights 1 and 2, and the wolves attack it both
    times (the Serial Killer, in its cast, kills someone else)."""
    killer = [("player_9", "kill", "player_1")] if roles["player_9"] == "serial_killer" else []
    table = Table(roles).night(1, ("player_7", "kill", "player_10"), *killer, ("player_10", "bet", "player_10"))
    if healer_out:
        table.lynch("player_6", 2)
    killer = [("player_9", "kill", "player_2")] if roles["player_9"] == "serial_killer" else []
    return table.night(2, ("player_8", "kill", "player_10"), *killer, ("player_10", "bet", "player_10"))


def test_f9_two_announced_self_bet_saves_use_the_budget_up():
    sk_ft = {**_sk_sp(), "player_10": "fortune_teller"}
    assert _budgets(_self_bets(sk_ft)) == [
        "player_10's self-bet has saved it twice, so it has none left: an attack on player_10 from now on kills it "
        "unless the Healer saves it."]
    assert _budgets(_self_bets(sk_ft, healer_out=True)) == [
        "player_10's self-bet has saved it twice, so it has none left: an attack on player_10 from now on kills it."]
    ne_ft = {**_ne_sp(), "player_10": "fortune_teller"}
    assert _budgets(_self_bets(ne_ft)) == [
        "player_10's self-bet has saved it twice, so it has none left: an attack on player_10 from now on kills it "
        "unless the Healer, or the Necromancer through the Healer's body, saves it."]
    once = Table(sk_ft).night(1, ("player_7", "kill", "player_10"), ("player_9", "kill", "player_1"),
                              ("player_10", "bet", "player_10"))
    assert _budgets(once) == []


def test_f9_two_hidden_deaths_use_the_conceals_up_unless_b6_says_it():
    table = Table(_sk_sp()).night(1, ("player_7", "kill", "player_1"), ("player_8", "conceal", None),
                                  ("player_9", "kill", "player_10"))
    assert _budgets(table) == []
    table.night(2, ("player_8", "kill", "player_2"), ("player_8", "conceal", None), ("player_9", "kill", "player_3"))
    assert _budgets(table) == [
        "Two deaths have been hidden (player_1's on night 1 and player_2's on night 2), so the Illusionist's conceals "
        "are used up: no death will be hidden again."]


def test_f9_is_in_the_public_block_and_f8_in_the_claimants_entry():
    sk_ft = {**_sk_sp(), "player_10": "fortune_teller"}
    table = _self_bets(sk_ft)
    lines = [_role(3, "player_4", "vigilante"), _said(3, "player_4", (2, "shoot", "player_3", "not_said", []), seq=1)]
    view = _view(table, "player_5", 3, *lines)
    blocks = deduction_blocks(view, own_result_lines(view), lines, 3)
    assert [item.row for item in blocks.public.shown if item.row == "F9"] == ["F9"]
    (f8,) = [item for item in blocks.seat.shown if item.row == "F8"]
    assert f8.subject == "player_4" and f8.grade == "possible"
    assert not [item for item in blocks.seat.shown if item.row == "F9"]


# --- the leak boundary ---------------------------------------------------------------------------------

def test_hidden_roles_and_planted_state_change_nothing():
    """The Sigilist and the Speculator swapped (both silent that night): the same morning, the same lines."""
    lines = (_said(2, "player_4", (1, "shoot", "player_9", "not_said", [])),
             _said(2, "player_2", (1, "watch", "player_6", "no_visitors", [])),
             _said(2, "player_5", (1, "protect", "player_1", "not_said", [])))
    choices = (("player_7", "kill", "player_1"), ("player_9", "kill", "player_6"), ("player_4", "kill", "player_9"))
    a = Table(_sk_sp()).night(1, *choices)
    b = Table({**_sk_sp(), "player_5": "speculator", "player_10": "sigilist"}).night(1, *choices)
    texts = [[item.text for item in comparison_items(_view(t, "player_3", 2, *lines), 2) if item.row == "F8"]
             for t in (a, b)]
    assert len(texts[0]) == 3 and texts[0] == texts[1]
    payload = {**a.payload("player_3"), "day_channel": list(lines), "current_day": 2}
    planted = {**payload, "roles": a.roles, "all_night_actions": a.records, "night_choices": ["anything"]}
    assert comparison_items(seat_view_from_payload(planted), 2) == comparison_items(seat_view_from_payload(payload), 2)


def test_random_games_do_not_change_with_planted_state():
    rng = random.Random(20261040)
    for game, snapshot in _continuing(rng, 30):
        lines, summaries, today = random_comparison_claims(rng, game, snapshot)
        for player in snapshot.living[:3]:
            payload = {**game.payload_of(player, snapshot), "day_channel": lines, "day_summaries": summaries,
                       "current_day": today}
            planted = {**payload, "roles": game.roles, "all_night_actions": game.records}
            assert comparison_items(seat_view_from_payload(planted), today) == \
                comparison_items(seat_view_from_payload(payload), today)
        # F9 reads the public record alone: every seat's payload gives the snapshot's lines.
        expected = budget_items(snapshot, public_items(snapshot))
        for player in snapshot.living:
            record = public_record(seat_view_from_payload(game.payload_of(player, snapshot)))
            assert budget_items(record, public_items(record)) == expected


# --- the oracles ---------------------------------------------------------------------------------------

def truth_oracle(nights: int, seed: int, seats: int = 3) -> dict[str, int]:
    """Random legal games with random claims of every kind: every F8 list holds and every certain F8
    line's claim is false; every F9 fact holds. Counts which branch held."""
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
            for item in budget_items(snapshot, public_items(snapshot)):
                count("F9 " + ("self-bets" if item.subject else "conceals"))
                for fact in item.conclusion:
                    assert public_fact_holds(fact, item.night, game), (item.text, fact)
            lines, summaries, today = random_comparison_claims(rng, game, snapshot)
            for player in rng.sample(snapshot.living, min(seats, len(snapshot.living))):
                payload = {**game.payload_of(player, snapshot), "day_channel": lines, "day_summaries": summaries,
                           "current_day": today}
                for item in comparison_items(seat_view_from_payload(payload), today):
                    if item.row != "F8":
                        continue
                    (fact,) = item.conclusion
                    assert public_fact_holds(fact, item.night, game), (item.text, fact, game.roles)
                    action = item.derivation[0].action
                    if item.grade == "certain":
                        assert isinstance(fact, NotAllTrue)
                        count(f"F8 {action} certain")
                        continue
                    assert item.grade == "possible" and isinstance(fact, AnyOf) and len(fact.branches) >= 2
                    *explained, _ = fact.branches
                    held = [i for i, branch in enumerate(explained)
                            if all(public_fact_holds(part, item.night, game) for part in branch)]
                    count(f"F8 {action} {len(fact.branches)} branches, " + ("explained" if held else "claim false"))
    return counts


def test_the_truth_oracle_on_random_games():
    counts = truth_oracle(nights=4000, seed=20261041)
    assert {"F9 conceals", "F8 shoot certain", "F8 protect certain", "F8 watch certain"} <= set(counts), counts
    assert any(name.startswith("F8 shoot 3 branches") for name in counts), counts
    assert any(name.startswith("F8 protect 2 branches, explained") for name in counts), counts


def test_the_brute_force_oracle_no_immune_role_is_left_out_of_a_shot_list():
    """Every role a deal agreeing with the seat's view gives the target, and that fails a shot in
    silence that night, is a branch of the list (or the line says the target cannot hold it)."""
    rng = random.Random(20261042)
    checked = 0
    for game, snapshot in _continuing(rng, 150):
        lines, summaries, today = random_comparison_claims(rng, game, snapshot)
        for player in snapshot.living:
            view = seat_view_from_payload({**game.payload_of(player, snapshot), "day_channel": lines,
                                           "day_summaries": summaries, "current_day": today})
            items = [item for item in comparison_items(view, today)
                     if item.row == "F8" and item.derivation[0].action == "shoot"]
            if not items:
                continue
            oracle = oracle_of(snapshot, view)
            assert oracle.allows(game.roles)
            support, _ = oracle.support()
            for item in items:
                target = item.derivation[0].target
                silent = roles_always_immune(item.night, snapshot.cast_role_counts) & support[target]
                (fact,) = item.conclusion
                if item.grade == "possible":
                    named = {role for branch in fact.branches for part in branch
                             if isinstance(part, RoleIn) and part.player == target for role in part.roles}
                    assert silent <= named, (item.text, silent)
                elif "fails on without an announcement" in item.text or "every shot that went ahead" in item.text:
                    assert not silent, (item.text, silent)  # the line says the target cannot be immune
                checked += 1
    assert checked >= 50, checked


def test_no_uses_left_is_checked_against_the_game():
    """The fact the F9 lines state is checked, not assumed: a game whose Fortune Teller still had a
    self-bet would fail it."""
    rng = random.Random(7)
    game = random_game(rng)
    night = max(game.nights)
    for role, left in (game.nights[night].uses_after or {}).items():
        assert public_fact_holds(NoUsesLeft(role), night, game) == (left == 0)
