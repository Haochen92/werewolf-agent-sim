"""Level 3 of the deduction engine, the core: the candidate roles of every player and hidden body, and
the census and per-player items they give (Agents/deduction/candidates/; catalogue Table C, F3, F7
of evidence/gameplay/deduction/deduction_catalogue.md).

Every game here runs through the real engine: each night through the resolution node, each lynch
through the day-resolution node. Per rule: a game where it narrows, with the exact sentence, and one
that differs in one respect where it must not. Then the two views (the public's is the same for every
seat), soundness against the true roles over random whole games (20,000 nights), and the brute-force
oracle: every certain item holds in every deal of the cast that agrees with what the view knows
(tests/factories/role_assignments.py).
"""

from __future__ import annotations

import random
import re

from Agents.config.game import GameConfig
from Agents.deduction import public_record, seat_view_from_payload
from Agents.deduction.candidates import (
    public_candidate_items,
    public_candidates,
    seat_candidate_items,
    seat_candidates,
)
from Agents.deduction.candidates.solver import solve
from Agents.rules.night_record import own_night_actions
from Agents.schemas.deduction import Candidates, HeldBy, OnlyRoles, PublicRecord, RoleIn, SeatView
from Agents.schemas.night import NightChoice
from Agents.schemas.roles import cast_role_counts
from tests.factories.random_nights import (
    _game_over,
    lynch_through_the_node,
    public_fact_holds,
    random_game,
    resolve_through_the_node,
)
from tests.factories.role_assignments import oracle_of

WOLVES = ("chanteuse", "illusionist")


class Table:
    """A constructed game with the roles dealt as given, each night and lynch through the real nodes."""

    def __init__(self, roles: dict[str, str]):
        self.roles = roles
        self.counts = cast_role_counts(roles)
        self.uses = {role: n for role, n in GameConfig().starting_uses().items() if role in self.counts}
        self.dead, self.records, self.mornings, self.wills = [], [], [], []

    def night(self, night: int, *choices: tuple) -> Table:
        """Each choice is (actor, kind, target) or, through a body, (actor, kind, target, body)."""
        made = [NightChoice(choice[0], self.roles[choice[0]], choice[1], choice[2],
                            via=choice[3] if len(choice) > 3 else None) for choice in choices]
        update = resolve_through_the_node(made, self.roles, night, self.living(), earlier_records=self.records,
                                          uses_left=self.uses)
        self.records += update["night_actions"]
        self.dead += update.get("dead_roster", [])
        self.mornings += update["night_announcements"]
        self.wills += update["read_out_wills"]
        self.uses = update["uses_left"]
        return self

    def lynch(self, player: str, day: int) -> Table:
        update = lynch_through_the_node(player, self.roles, day, self.dead, self.records)
        self.dead += update["dead_roster"]
        self.wills += update["read_out_wills"]
        return self

    def living(self) -> list[str]:
        return [p for p in self.roles if p not in {d.player for d in self.dead}]

    def public(self) -> PublicRecord:
        return PublicRecord(cast_role_counts=self.counts, dead_roster=list(self.dead),
                            announcements=list(self.mornings), wills=list(self.wills), living=self.living())

    def payload(self, player: str) -> dict:
        """The seat's payload as a night turn builds it: the others alive, and a wolf's pack."""
        role = self.roles[player]
        pack = {p: r for p, r in self.roles.items() if r in WOLVES and p in self.living()}
        return {"player_id": player, "player_role": role, "cast_role_counts": self.counts,
                "dead_roster": list(self.dead), "night_actions": own_night_actions(self.records, player, role),
                "night_announcements": list(self.mornings), "read_out_wills": list(self.wills),
                "surviving_players": [p for p in self.living() if p != player],
                "pack_roles": pack if role in WOLVES else {}}

    def seat(self, player: str) -> SeatView:
        return seat_view_from_payload(self.payload(player))

    def texts(self, row: str, player: str | None = None) -> list[str]:
        items = public_candidate_items(self.public()) if player is None else seat_candidate_items(self.seat(player))
        return [item.text for item in items if item.row == row]


def _deal(*roles: str) -> dict[str, str]:
    """player_1 holds the first role, player_2 the second, and so on."""
    return {f"player_{seat + 1}": role for seat, role in enumerate(roles)}


def _sk_sp() -> dict[str, str]:
    return _deal("investigator", "sentinel", "trailseer", "vigilante", "sigilist", "healer", "chanteuse",
                 "illusionist", "serial_killer", "speculator")


def _ne_sp() -> dict[str, str]:
    return _deal("investigator", "sentinel", "trailseer", "vigilante", "sigilist", "healer", "chanteuse",
                 "illusionist", "necromancer", "speculator")


# --- AC2 and AC4: the census lines --------------------------------------------------------------

def _ac2(serial_killer: str = "player_6", speculator: str = "player_10") -> Table:
    """AC2 (2f19d908), up to the day-3 vote: SK+SP, player_5 the Investigator."""
    roles = _deal("vigilante", "sentinel", "trailseer", "sigilist", "investigator", "serial_killer",
                  "chanteuse", "healer", "illusionist", "speculator")
    table = Table({**roles, serial_killer: "serial_killer", speculator: "speculator"})
    table.night(1, ("player_7", "kill", "player_1"), ("player_7", "block", "player_8"),
                ("player_9", "conceal", None), (serial_killer, "kill", "player_1"), ("player_3", "follow", "player_7"),
                ("player_5", "investigate", "player_9"), ("player_8", "protect", "player_5"),
                ("player_2", "watch", "player_4"))
    table.lynch("player_9", 2)
    table.night(2, ("player_7", "kill", "player_3"), ("player_7", "block", "player_5"),
                (serial_killer, "kill", "player_3"), ("player_4", "sigil", "player_7"),
                ("player_2", "watch", "player_5"), ("player_8", "protect", "player_5"),
                ("player_5", "investigate", "player_6"), ("player_3", "follow", "player_6"))
    return table


def test_acceptance_case_2_the_census_line():
    """AC2 line 1: the Serial Killer cannot die at night, no one revealed was it, and player_1's body
    was hidden by the living Illusionist, which never hides it (L8)."""
    table = _ac2()
    assert [d.player for d in table.dead] == ["player_1", "player_9", "player_3", "player_7"]
    assert table.texts("F3", "player_5") == [
        "Both wolves are dead: player_9 and player_7. The Serial Killer is alive and is one of player_2, "
        "player_4, player_6, player_8 and player_10.",
        "The Speculator is one of player_2, player_4, player_6, player_8 and player_10, or is player_1's "
        "hidden body.",
    ]
    # The public does not know that player_5 is the Investigator.
    assert table.texts("F3")[0] == (
        "Both wolves are dead: player_9 and player_7. The Serial Killer is alive and is one of player_2, "
        "player_4, player_5, player_6, player_8 and player_10.")
    # The Sigilist struck on night 2, after player_1 died: player_1's body is not it.
    assert table.texts("F7", "player_5") == [
        "player_1's hidden role can only be the Sentinel, the Vigilante, the Healer or the Speculator."]


def test_acceptance_case_2_does_not_say_that_player_8_is_the_healer():
    for item in seat_candidate_items(_ac2().seat("player_5")):
        assert "player_8 is" not in item.text
        assert item.subject != "player_8"


def _ac4() -> Table:
    """AC4 (403f4dbc), up to the day-5 vote: NE+SP, player_2 the Vigilante."""
    table = Table(_deal("chanteuse", "vigilante", "sigilist", "investigator", "speculator", "illusionist",
                        "healer", "trailseer", "sentinel", "necromancer"))
    table.night(1, ("player_1", "kill", "player_10"), ("player_1", "block", "player_3"),
                ("player_7", "protect", "player_9"), ("player_8", "follow", "player_2"))
    table.night(2, ("player_6", "kill", "player_8"), ("player_6", "conceal", None), ("player_1", "block", "player_2"),
                ("player_4", "investigate", "player_6"), ("player_9", "watch", "player_6"),
                ("player_7", "protect", "player_4"), ("player_8", "follow", "player_6"))
    table.lynch("player_6", 3)
    table.night(3, ("player_1", "kill", "player_4"), ("player_1", "block", "player_9"),
                ("player_10", "kill", "player_5", "player_6"), ("player_5", "pick", "town"),
                ("player_7", "protect", "player_9"))
    table.lynch("player_1", 4)
    table.night(4, ("player_10", "kill", "player_7", "player_6"), ("player_7", "protect", "player_2"),
                ("player_9", "watch", "player_3"))
    return table


def test_acceptance_case_4_the_census_line():
    """AC4 line 1: neither hidden body can be the Necromancer: player_8 died on night 2, when it
    cannot be killed, and player_5 was killed through a body, and it cannot act on itself."""
    table = _ac4()
    assert table.living() == ["player_2", "player_3", "player_9", "player_10"]
    assert table.texts("F3", "player_2") == [
        "Both wolves are dead: player_6 and player_1. The Necromancer is alive and is one of player_3, player_9 "
        "and player_10.",
        "The Speculator is one of player_3, player_9 and player_10, or is player_5's hidden body.",
    ]


def test_acceptance_case_4_singles_out_none_of_the_three():
    """AC4 must not say: nothing certain separates player_3, player_9 and player_10."""
    items = seat_candidate_items(_ac4().seat("player_2"))
    assert [item for item in items if item.subject in ("player_3", "player_9", "player_10")] == []
    assert [item.text for item in items if item.row == "F7"] == [
        "player_8's hidden role can only be the Sentinel, the Trailseer or the Sigilist.",
        "player_5's hidden role can only be the Sentinel, the Trailseer, the Sigilist or the Speculator.",
    ]


# --- each rule: where it narrows, and where it must not --------------------------------------------

def test_the_serial_killer_is_one_of_the_players_seen_at_its_victims_door():
    """C6: the Sentinel saw two players at the door of the Serial Killer's victim."""
    table = Table(_sk_sp())
    table.night(2, ("player_9", "kill", "player_6"), ("player_1", "investigate", "player_6"),
                ("player_2", "watch", "player_6"), ("player_7", "kill", "player_3"))
    assert table.texts("F3", "player_2")[0] == (
        "Both wolves are alive and are two of player_1, player_4, player_5, player_7, player_8, player_9 and "
        "player_10. The Serial Killer is alive and is one of player_1 and player_9.")
    # The public did not see the door.
    assert table.texts("F3")[0].endswith("The Serial Killer is alive and is one of player_1, player_2, player_4, "
                                         "player_5, player_7, player_8, player_9 and player_10.")


def test_a_wolf_at_the_door_with_the_other_wolf_known_is_the_chanteuse():
    """C6 with one wolf ruled out for the players seen: player_2's will shows player_1 and player_7 at
    the wolves' victim's door. The Illusionist knows its own role (here without its pack list), so the
    wolf among them is the Chanteuse, and no one else is."""
    table = Table(_sk_sp())
    table.night(1, ("player_7", "kill", "player_6"), ("player_2", "watch", "player_6"), ("player_9", "kill", "player_3"),
                ("player_1", "investigate", "player_6"))
    table.lynch("player_2", 2)
    payload = table.payload("player_8")
    payload["pack_roles"] = {}  # the Illusionist seat without its pack list: it still knows its own role
    candidates = seat_candidates(seat_view_from_payload(payload))
    assert [p for p, roles in candidates.roles.items() if "chanteuse" in roles] == ["player_1", "player_7"]


def test_k_players_who_can_only_hold_k_roles_exclude_everyone_else():
    """C18: two players who can only be the Healer or the Trailseer: no one else is either. Three
    such players cannot be (no deal agrees), and two with a third role between them say nothing."""
    roles = _sk_sp()
    players = list(roles)

    def solved(*constraints) -> Candidates | None:
        return solve(players, [], cast_role_counts(roles), {}, list(constraints))

    healer_or_trailseer = frozenset({"healer", "trailseer"})
    two = solved(OnlyRoles("player_1", healer_or_trailseer, "test"), OnlyRoles("player_2", healer_or_trailseer, "test"))
    assert all(not roles & healer_or_trailseer for p, roles in two.roles.items() if p not in ("player_1", "player_2"))
    three = solved(*(OnlyRoles(p, healer_or_trailseer, "test") for p in ("player_1", "player_2", "player_3")))
    assert three is None
    wider = healer_or_trailseer | {"vigilante"}
    loose = solved(OnlyRoles("player_1", wider, "test"), OnlyRoles("player_2", wider, "test"))
    assert all(loose.roles[p] == frozenset(roles.values()) for p in players[2:])


def test_a_role_only_one_player_can_hold_is_that_players():
    """C18: when everyone else is ruled out of the Speculator, the one left holds it."""
    roles = _sk_sp()
    players = list(roles)
    no_speculator = frozenset(cast_role_counts(roles)) - {"speculator"}
    constraints = [OnlyRoles(p, no_speculator, "test") for p in players if p != "player_4"]
    candidates = solve(players, [], cast_role_counts(roles), {}, constraints)
    assert candidates.roles["player_4"] == {"speculator"}


def _necromancer_voted_out(lynch: bool) -> Table:
    table = Table(_ne_sp())
    table.night(1, ("player_7", "kill", "player_1"))
    table.lynch("player_8", 2)
    table.night(2, ("player_7", "kill", "player_2"), ("player_9", "kill", "player_6", "player_8"))
    if lynch:
        table.lynch("player_9", 3)
    return table


def test_the_game_went_on_so_a_hidden_body_is_not_the_last_wolf():
    """C18, continuation: the Necromancer was voted out and the game went on, so the body hidden
    through the Illusionist's was not the Chanteuse: with both wolves and the lone killer dead the
    town would have won."""
    table = _necromancer_voted_out(lynch=True)
    assert [d.concealed for d in table.dead] == [False, False, False, True, False]
    assert table.texts("F3")[0] == (
        "One wolf is dead: player_8, the Illusionist. The Chanteuse is alive and is one of player_3, player_4, "
        "player_5, player_7 and player_10. The Necromancer is dead: player_9.")
    assert table.texts("F7") == [
        "player_6's hidden role can only be the Trailseer, the Vigilante, the Sigilist, the Healer or the "
        "Speculator."]


def test_before_the_necromancer_was_voted_out_the_body_may_be_the_chanteuse():
    table = _necromancer_voted_out(lynch=False)
    assert ("The Chanteuse is one of player_3, player_4, player_5, player_7, player_9 and player_10, or is "
            "player_6's hidden body.") in table.texts("F3")[0]


def test_a_wolf_attack_after_a_hidden_death_with_the_other_wolf_revealed_keeps_the_chanteuse_alive():
    """C18, a holder alive at a night: the Illusionist was revealed before night 3, so the wolves'
    attack that night was the Chanteuse's, and she is not the body hidden on night 2."""
    table = _necromancer_voted_out(lynch=False)
    table.night(3, ("player_7", "kill", "player_3"))
    assert table.texts("F3")[0] == (
        "One wolf is dead: player_8, the Illusionist. The Chanteuse is alive: it attacked player_3 on night 3. "
        "It is player_4, player_5, player_7, player_9 or player_10. The Necromancer is alive and is one of "
        "player_4, player_5, player_7, player_9 and player_10.")


def test_a_pick_after_a_hidden_death_keeps_the_speculator_off_that_body():
    """C18, a holder alive at a night: the Speculator picked on night 2, after player_2 was hidden."""
    table = Table(_sk_sp())
    table.night(1, ("player_7", "kill", "player_2"), ("player_8", "conceal", None))
    table.night(2, ("player_10", "pick", "town"), ("player_7", "kill", "player_3"))
    assert table.texts("F3")[1] == ("The Speculator is alive: it picked a side on night 2. It is player_1, "
                                    "player_4, player_5, player_6, player_7, player_8, player_9 or player_10.")
    # Picked on the night the body died: it may be that body.
    same_night = Table(_sk_sp())
    same_night.night(1, ("player_7", "kill", "player_2"), ("player_8", "conceal", None),
                     ("player_10", "pick", "town"))
    assert same_night.texts("F3")[1].endswith(", or is player_2's hidden body.")


def test_a_wolf_knows_the_body_its_pack_hid_and_leaves_its_pack_out():
    """The pack's kill record names the hidden role: for the wolf, the Speculator is that body."""
    table = Table(_sk_sp())
    table.night(1, ("player_7", "kill", "player_10"), ("player_8", "conceal", None))
    assert table.texts("F3", "player_7") == [
        "The Serial Killer is alive and is one of player_1, player_2, player_3, player_4, player_5, player_6 and "
        "player_9.",
        "The Speculator is dead: it is player_10's hidden body.",
    ]
    assert table.texts("F7", "player_7") == ["player_10's hidden role is the Speculator."]
    assert table.texts("F3")[1].endswith(", or is player_10's hidden body.")


def test_a_revealed_role_is_dead():
    table = Table(_sk_sp())
    table.night(1, ("player_7", "kill", "player_10"))
    assert table.texts("F3")[1] == "The Speculator is dead: player_10."


def test_a_view_that_does_not_list_the_living_says_nothing():
    payload = _ac2().payload("player_5")
    del payload["surviving_players"]
    assert seat_candidate_items(seat_view_from_payload(payload)) == []


# --- the two views ------------------------------------------------------------------------------

def _continuing_snapshots(rng: random.Random, games: int):
    """Every point a seat reasons from in `games` random games: a game over has no turn after it."""
    for _ in range(games):
        game = random_game(rng)
        for snapshot in game.snapshots:
            if not _game_over(game.roles, snapshot.dead_roster):
                yield game, snapshot


def test_every_seat_gets_the_same_public_candidates_and_planted_state_changes_nothing():
    for game, snapshot in _continuing_snapshots(random.Random(7), 150):
        expected = public_candidate_items(snapshot)
        for player in snapshot.living:
            payload = game.payload_of(player, snapshot)
            planted = {**payload, "roles": game.roles, "all_night_actions": game.records}
            assert public_candidate_items(public_record(seat_view_from_payload(payload))) == expected
            assert public_candidate_items(public_record(seat_view_from_payload(planted))) == expected
            assert seat_candidate_items(seat_view_from_payload(planted)) == \
                seat_candidate_items(seat_view_from_payload(payload))


def test_a_seat_knows_at_least_what_the_public_knows():
    for game, snapshot in _continuing_snapshots(random.Random(8), 150):
        public = public_candidates(snapshot)
        for player in snapshot.living:
            seat = seat_candidates(seat_view_from_payload(game.payload_of(player, snapshot)))
            for name, roles in seat.roles.items():
                assert roles <= public.roles[name], (name, roles, public.roles[name])


def test_hidden_roles_the_seat_cannot_see_do_not_change_its_items():
    """AC2 with the Serial Killer and the Speculator swapped: the Investigator sees the same game."""
    swapped = _ac2(serial_killer="player_10", speculator="player_6")
    assert swapped.roles["player_10"] == "serial_killer"
    assert seat_candidate_items(swapped.seat("player_5")) == seat_candidate_items(_ac2().seat("player_5"))


# --- soundness: the true roles, and every deal that agrees with the view ---------------------------

def _holds_in_every_deal(fact, support: dict[str, set[str]]) -> bool:
    if isinstance(fact, RoleIn):
        return support[fact.player] <= fact.roles
    if isinstance(fact, HeldBy):
        return all(player in fact.players for player, roles in support.items() if fact.role in roles)
    raise TypeError(fact)


def _check_by_brute_force(record: PublicRecord, view: SeatView | None, true_roles: dict[str, str]) -> None:
    """Every deal the view allows: there is one (the true deal is one), the engine keeps every role
    a deal gives, and every certain item holds in all of them."""
    oracle = oracle_of(record, view)
    assert oracle.allows(true_roles), "the true deal breaks a condition: an oracle or fact error"
    support, deals = oracle.support()
    assert deals >= 1
    candidates = public_candidates(record) if view is None else seat_candidates(view)
    items = public_candidate_items(record) if view is None else seat_candidate_items(view)
    assert candidates is not None
    for player, roles in support.items():
        assert roles <= candidates.roles[player], (player, roles, candidates.roles[player])
    for item in items:
        assert item.grade == "certain"
        for fact in item.conclusion:
            assert _holds_in_every_deal(fact, support), (item.text, fact, support)


CONSTRUCTED = {
    "AC2": (_ac2, "player_5"), "AC4": (_ac4, "player_2"),
    "continuation": (lambda: _necromancer_voted_out(lynch=True), "player_3"),
}


def test_the_brute_force_oracle_on_the_constructed_games():
    for build, seat in CONSTRUCTED.values():
        table = build()
        _check_by_brute_force(table.public(), None, table.roles)
        for player in table.living():
            _check_by_brute_force(table.public(), table.seat(player), table.roles)


def test_the_brute_force_oracle_on_random_games():
    """Every point a seat reasons from in 400 random games, the public's view and every living seat's."""
    views = 0
    for game, snapshot in _continuing_snapshots(random.Random(20261018), 400):
        _check_by_brute_force(snapshot, None, game.roles)
        for player in snapshot.living:
            _check_by_brute_force(snapshot, seat_view_from_payload(game.payload_of(player, snapshot)), game.roles)
            views += 1
    assert views > 8000


SENTENCES_REACHED = {
    "both wolves dead": r"Both wolves are dead:",
    "both wolves alive": r"Both wolves are alive",
    "one wolf dead": r"One wolf is dead:",
    "a reason it is alive": r" is alive: it ",
    "alive or a hidden body": r", or is \S+ hidden body\.",
    "dead as a hidden body": r" is dead: it is ",
    "a hidden body's roles": r"'s hidden role can only be",
    "a hidden body's one role": r"'s hidden role is the",
    "a living player's roles": r"^player_\d+ can only be ",
    "a living player's one role": r"^player_\d+ is the ",
}
"""The forms of F3 and F7 the random games must reach, by a pattern of their sentence."""


def test_every_fact_a_candidate_item_states_holds_in_the_real_game():
    """Random legal games until 20,000 nights: the public's items at every point a seat reasons from,
    and one living seat's at one such point per game, hold against the true roles; no legal game
    leaves a player no role. (The brute-force test above checks every seat of 400 games, and more
    strictly: every deal that agrees with the view, the true one among them.)"""
    rng = random.Random(20261017)
    nights_played = 0
    reached: set[str] = set()
    while nights_played < 20000:
        game = random_game(rng)
        nights_played += len(game.nights)
        snapshots = [s for s in game.snapshots if not _game_over(game.roles, s.dead_roster)]
        seat_at = rng.randrange(len(snapshots)) if snapshots else -1
        for index, snapshot in enumerate(snapshots):
            assert public_candidates(snapshot) is not None
            items = public_candidate_items(snapshot)
            if index == seat_at:
                view = seat_view_from_payload(game.payload_of(rng.choice(snapshot.living), snapshot))
                assert seat_candidates(view) is not None
                items += seat_candidate_items(view)
            for item in items:
                reached |= {name for name, pattern in SENTENCES_REACHED.items() if re.search(pattern, item.text)}
                for fact in item.conclusion:
                    assert public_fact_holds(fact, item.night, game), (item.text, fact, game.roles)
    assert reached == set(SENTENCES_REACHED)
