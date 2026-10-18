"""Level 1 of the deduction engine, slice 3: what a check, a watch, a follow, a sigil, a block and a
scored bet imply (Agents/deduction/own_results/checks.py, sightings.py, sigils.py, blocks.py,
bets.py; rows A21–A27, A32–A35, A37–A43, A49, A50 of
evidence/reasoning_failures/deduction_catalogue.md, Table A).

Every night here runs through the real engine. Per row: a night where it fires and is true, with the
exact line; nights that differ in one respect where it must not fire or must weaken (bodies, blocks,
the living illusionist's conceal, same-night deaths, the cast). The leak boundary and the random-night
soundness check for these rows are in test_own_results.py.
"""

from __future__ import annotations

from Agents.deduction import own_result_lines
from Agents.deduction.records import read_record
from Agents.prompts.prompt_formatters import format_night_actions
from Agents.rules.night import resolve_night
from Agents.rules.night_record import night_action_records
from Agents.schemas.game_events import DeathRecord
from Agents.schemas.night import NightChoice
from tests.engine.deduction.test_own_results import _after_night, _game, _seat_view, _the_one_line


def _lynched(player: str, role: str, day: int) -> DeathRecord:
    return DeathRecord(player=player, role=role, day=day, phase="day")


def _killed(player: str, role: str, night: int, concealed: bool = False) -> DeathRecord:
    return DeathRecord(player=player, role="" if concealed else role, day=night, phase="night",
                       concealed=concealed)


# --- A21, A22: Suspicious -----------------------------------------------------------------------

def test_a_suspicious_check_in_a_serial_killer_cast_is_a_wolf():
    roles, player_of = _game("serial_killer", "speculator")
    chanteuse = player_of["chanteuse"]
    choices = [NightChoice(player_of["investigator"], "investigator", "investigate", chanteuse)]
    records, lines, _ = _after_night(choices, roles, 1, player_of["investigator"])
    assert format_night_actions(records, implications=lines) == (
        f"Night 1: you checked {chanteuse}. {chanteuse} reads Suspicious. Only a wolf reads Suspicious "
        f"in this game, so {chanteuse} is a wolf."
    )
    assert _the_one_line(lines).row == "A21"


def test_a_suspicious_check_on_night_one_in_a_necromancer_cast_is_a_wolf():
    roles, player_of = _game("necromancer", "fortune_teller")
    illusionist = player_of["illusionist"]
    choices = [NightChoice(player_of["investigator"], "investigator", "investigate", illusionist)]
    _, lines, _ = _after_night(choices, roles, 1, player_of["investigator"])
    assert _the_one_line(lines).text == (
        f"The Necromancer does nothing on night 1, so only a wolf reads Suspicious that night: "
        f"{illusionist} is a wolf.")


def test_acceptance_case_3_no_one_dead_before_night_two_means_a_wolf():
    """AC3: the exact sentence the investigator should have received."""
    roles, player_of = _game("necromancer", "speculator")
    illusionist = player_of["illusionist"]
    choices = [NightChoice(player_of["investigator"], "investigator", "investigate", illusionist)]
    _, lines, _ = _after_night(choices, roles, 2, player_of["investigator"])
    line = _the_one_line(lines)
    assert (line.row, line.grade) == ("A22", "certain")
    assert line.text == ("No one had died before that night, so the Necromancer had no body to kill "
                         f"through and could not read Suspicious: {illusionist} is a wolf.")


def test_with_no_killing_body_revealed_suspicious_is_a_wolf_even_if_the_vigilante_died_hidden():
    """A22 (a). A concealed body cannot be used, so a hidden dead vigilante gives no kill."""
    roles, player_of = _game("necromancer", "speculator")
    earlier = [_lynched(player_of["healer"], "healer", 2),
               _killed(player_of["vigilante"], "vigilante", 1, concealed=True)]
    chanteuse = player_of["chanteuse"]
    choices = [NightChoice(player_of["investigator"], "investigator", "investigate", chanteuse)]
    _, lines, _ = _after_night(choices, roles, 2, player_of["investigator"], earlier_deaths=earlier)
    assert _the_one_line(lines).text == (
        "Neither the Illusionist nor the Vigilante had been revealed dead before that night, so the "
        f"Necromancer had no body to kill through and could not read Suspicious: {chanteuse} is a wolf.")


def test_a_vigilante_killed_that_same_night_was_not_yet_a_body():
    roles, player_of = _game("necromancer", "speculator")
    vigilante = player_of["vigilante"]
    choices = [NightChoice(player_of["illusionist"], "illusionist", "kill", vigilante),
               NightChoice(player_of["investigator"], "investigator", "investigate", player_of["chanteuse"])]
    _, lines, outcome = _after_night(choices, roles, 2, player_of["investigator"],
                                     earlier_deaths=[_lynched(player_of["healer"], "healer", 2)])
    assert vigilante in outcome.deaths
    assert _the_one_line(lines).text.startswith("Neither the Illusionist nor the Vigilante had been revealed dead")


def test_with_a_vigilante_body_suspicious_may_be_the_necromancer_and_the_line_says_so():
    """The counterexample A22 (a) guards against: the necromancer, shooting through the lynched
    vigilante's body, reads Suspicious. "is a wolf" would be false here."""
    roles, player_of = _game("necromancer", "speculator")
    necromancer = player_of["necromancer"]
    choices = [NightChoice(necromancer, "necromancer", "kill", player_of["sentinel"], via=player_of["vigilante"]),
               NightChoice(player_of["investigator"], "investigator", "investigate", necromancer)]
    records, lines, _ = _after_night(choices, roles, 2, player_of["investigator"],
                                     earlier_deaths=[_lynched(player_of["vigilante"], "vigilante", 2)])
    assert records[0].result == "suspicious"
    line = _the_one_line(lines)
    assert (line.row, line.grade) == ("A22", "possible")
    assert line.text == (f"So {necromancer} is a wolf, or the Necromancer if it killed through a dead "
                         "player's body that night.")


def test_with_both_wolves_dead_suspicious_is_the_necromancer():
    roles, player_of = _game("necromancer", "speculator")
    necromancer = player_of["necromancer"]
    earlier = [_lynched(player_of["chanteuse"], "chanteuse", 2),
               _lynched(player_of["illusionist"], "illusionist", 3)]
    choices = [NightChoice(necromancer, "necromancer", "kill", player_of["healer"], via=player_of["illusionist"]),
               NightChoice(player_of["investigator"], "investigator", "investigate", necromancer)]
    _, lines, _ = _after_night(choices, roles, 3, player_of["investigator"], earlier_deaths=earlier)
    assert _the_one_line(lines).text == (
        f"Both wolves are dead and neither was {necromancer}, so {necromancer} is the Necromancer: it "
        "read Suspicious because it killed through a body that night.")


def test_a_wolf_checked_on_the_night_it_dies_is_not_called_the_necromancer():
    """'Both wolves dead' counts only wolves revealed on other players: here the checked wolf is
    itself the second wolf revealed this morning."""
    roles, player_of = _game("necromancer", "speculator")
    illusionist = player_of["illusionist"]
    choices = [NightChoice(player_of["vigilante"], "vigilante", "kill", illusionist),
               NightChoice(player_of["investigator"], "investigator", "investigate", illusionist)]
    _, lines, outcome = _after_night(choices, roles, 3, player_of["investigator"],
                                     earlier_deaths=[_lynched(player_of["chanteuse"], "chanteuse", 2),
                                                     _lynched(player_of["sigilist"], "sigilist", 3)])
    assert illusionist in outcome.deaths
    assert _the_one_line(lines).text == (
        "Only a wolf, or the Necromancer on a night it kills through a body, reads Suspicious, and "
        f"{illusionist} is not the Necromancer: {illusionist} is a wolf.")


def test_with_the_necromancer_dead_suspicious_is_a_wolf():
    roles, player_of = _game("necromancer", "speculator")
    chanteuse = player_of["chanteuse"]
    earlier = [_lynched(player_of["vigilante"], "vigilante", 2),
               _lynched(player_of["necromancer"], "necromancer", 3)]
    choices = [NightChoice(player_of["investigator"], "investigator", "investigate", chanteuse)]
    _, lines, _ = _after_night(choices, roles, 3, player_of["investigator"], earlier_deaths=earlier)
    assert _the_one_line(lines).text == (
        "Only a wolf, or the Necromancer on a night it kills through a body, reads Suspicious, and "
        f"{chanteuse} is not the Necromancer: {chanteuse} is a wolf.")


# --- A23, A24, A25: Not suspicious, and the Necromancer's check -----------------------------------

def test_not_suspicious_in_sk_sp_leaves_the_killer_and_the_neutral_open():
    roles, player_of = _game("serial_killer", "speculator")
    healer = player_of["healer"]
    choices = [NightChoice(player_of["investigator"], "investigator", "investigate", healer)]
    records, lines, _ = _after_night(choices, roles, 1, player_of["investigator"])
    assert format_night_actions(records, implications=lines) == (
        f"Night 1: you checked {healer}. {healer} reads Not suspicious. So {healer} is not a wolf, but "
        f"{healer} could still be the Serial Killer or the Speculator."
    )
    assert _the_one_line(lines).row == "A23"


def test_not_suspicious_drops_a_role_revealed_on_someone_else():
    roles, player_of = _game("serial_killer", "speculator")
    healer = player_of["healer"]
    choices = [NightChoice(player_of["investigator"], "investigator", "investigate", healer)]
    _, lines, _ = _after_night(choices, roles, 2, player_of["investigator"],
                               earlier_deaths=[_lynched(player_of["serial_killer"], "serial_killer", 2)])
    assert _the_one_line(lines).text == f"So {healer} is not a wolf, but {healer} could still be the Speculator."


def test_not_suspicious_in_ne_ft_names_the_necromancer_and_the_fortune_teller():
    roles, player_of = _game("necromancer", "fortune_teller")
    sentinel = player_of["sentinel"]
    choices = [NightChoice(player_of["investigator"], "investigator", "investigate", sentinel)]
    _, lines, _ = _after_night(choices, roles, 2, player_of["investigator"])
    line = _the_one_line(lines)
    assert line.row == "A24"
    assert line.text == (f"So {sentinel} is not a wolf, but {sentinel} could still be the Necromancer or "
                         "the Fortune Teller.")


def test_the_necromancers_check_through_a_body_reads_suspicious_only_on_a_wolf():
    roles, player_of = _game("necromancer", "speculator")
    investigator, chanteuse = player_of["investigator"], player_of["chanteuse"]
    choices = [NightChoice(player_of["necromancer"], "necromancer", "investigate", chanteuse, via=investigator)]
    records, lines, _ = _after_night(choices, roles, 2, player_of["necromancer"],
                                     earlier_deaths=[_lynched(investigator, "investigator", 2)])
    assert format_night_actions(records, implications=lines) == (
        f"Night 2: you checked {chanteuse}. Through {investigator}'s body: {chanteuse} reads Suspicious. "
        f"You made no kill that night, so only a wolf could read Suspicious: {chanteuse} is a wolf."
    )
    assert _the_one_line(lines).row == "A25"


def test_the_necromancers_not_suspicious_check_does_not_name_itself():
    roles, player_of = _game("necromancer", "speculator")
    investigator, healer = player_of["investigator"], player_of["healer"]
    choices = [NightChoice(player_of["necromancer"], "necromancer", "investigate", healer, via=investigator)]
    _, lines, _ = _after_night(choices, roles, 2, player_of["necromancer"],
                               earlier_deaths=[_lynched(investigator, "investigator", 2)])
    assert _the_one_line(lines).text == f"So {healer} is not a wolf, but {healer} could still be the Speculator."


# --- L14: a borrowed watch puts the body's name first ---------------------------------------------

def test_an_empty_watch_through_a_body_has_no_visitor():
    """Raw `seen` is [the body]; read raw it would invent a visitor."""
    roles, player_of = _game("necromancer", "speculator")
    sentinel, healer = player_of["sentinel"], player_of["healer"]
    choices = [NightChoice(player_of["necromancer"], "necromancer", "watch", healer, via=sentinel)]
    records, lines, _ = _after_night(choices, roles, 2, player_of["necromancer"],
                                     earlier_deaths=[_lynched(sentinel, "sentinel", 2)])
    assert records[0].seen == [sentinel]
    view = _seat_view(player_of["necromancer"], roles, records, [_lynched(sentinel, "sentinel", 2)])
    read = read_record(records[0], view)
    assert (read.body, read.observed) == (sentinel, ())
    line = _the_one_line(lines)
    assert line.row == "A32"
    assert sentinel not in line.text


def test_a_check_and_a_pack_kill_put_no_visitor_in_the_reading():
    roles, player_of = _game("serial_killer", "speculator")
    target = player_of["healer"]
    choices = [NightChoice(player_of["chanteuse"], "chanteuse", "kill", target),
               NightChoice(player_of["illusionist"], "illusionist", "conceal", None),
               NightChoice(player_of["investigator"], "investigator", "investigate", player_of["sentinel"])]
    outcome = resolve_night(choices, roles, 1)
    records = night_action_records(choices, outcome, roles)
    view = _seat_view(player_of["illusionist"], roles, records, [])
    pack_record, check_record = records[0], records[2]
    assert pack_record.seen == ["healer"] and check_record.seen == [player_of["sentinel"]]
    assert read_record(pack_record, view).observed == ()
    assert read_record(pack_record, view).hidden_role == "healer"
    assert read_record(check_record, view).observed == ()


# --- A26, A27, A32: the watch ---------------------------------------------------------------------

def test_a_watchs_visitors_are_not_the_roles_that_never_visit_under_their_own_name():
    roles, player_of = _game("serial_killer", "fortune_teller")
    sigilist, healer, killer = player_of["sigilist"], player_of["healer"], player_of["serial_killer"]
    choices = [NightChoice(healer, "healer", "protect", sigilist),
               NightChoice(killer, "serial_killer", "kill", sigilist),
               NightChoice(player_of["sentinel"], "sentinel", "watch", sigilist)]
    records, lines, _ = _after_night(choices, roles, 1, player_of["sentinel"])
    # The morning's attack and save on the watched player add A28 and A29 (slice 5).
    assert _the_one_line(lines).row == "A26+A28+A29"
    assert format_night_actions(records, implications=lines) == (
        f"Night 1: you watched {sigilist}. Tonight {sigilist} was visited by {healer} and {killer}. A visit "
        f"does not show which action was taken. Neither {healer} nor {killer} is the Fortune Teller: the "
        f"Fortune Teller never visits. Everyone who attacked {sigilist} and the Healer who saved them came "
        f"to {sigilist}, and your watch saw every visitor but you. {healer} and {killer} are the Serial "
        "Killer and the Healer, one each; your watch does not show which is which."
    )


def test_in_a_necromancer_cast_a_visitor_is_not_the_necromancer_either():
    roles, player_of = _game("necromancer", "speculator")
    healer, sigilist = player_of["healer"], player_of["sigilist"]
    choices = [NightChoice(healer, "healer", "protect", sigilist),
               NightChoice(player_of["sentinel"], "sentinel", "watch", sigilist)]
    _, lines, _ = _after_night(choices, roles, 2, player_of["sentinel"])
    assert _the_one_line(lines).text == (
        f"A visit does not show which action was taken. {healer} is not the Necromancer or the "
        "Speculator: the Necromancer visits only under a dead player's name, and the Speculator never visits.")


def test_a_visitor_already_dead_is_the_necromancer_using_its_body():
    roles, player_of = _game("necromancer", "speculator")
    healer, sigilist = player_of["healer"], player_of["sigilist"]
    choices = [NightChoice(player_of["necromancer"], "necromancer", "protect", sigilist, via=healer),
               NightChoice(player_of["sentinel"], "sentinel", "watch", sigilist)]
    _, lines, _ = _after_night(choices, roles, 2, player_of["sentinel"],
                               earlier_deaths=[_lynched(healer, "healer", 2)])
    line = _the_one_line(lines)
    assert line.row == "A27"
    assert line.text == f"{healer} was already dead, so the Necromancer used {healer}'s body to protect {sigilist}."


def test_a_visitor_who_died_that_same_night_made_its_own_visit():
    """Revealed this morning, not before the night: its own visit, not a body."""
    roles, player_of = _game("necromancer", "speculator")
    healer, sigilist = player_of["healer"], player_of["sigilist"]
    choices = [NightChoice(player_of["chanteuse"], "chanteuse", "kill", healer),
               NightChoice(healer, "healer", "protect", sigilist),
               NightChoice(player_of["sentinel"], "sentinel", "watch", sigilist)]
    _, lines, outcome = _after_night(choices, roles, 3, player_of["sentinel"])
    assert healer in outcome.deaths
    line = _the_one_line(lines)
    assert line.row == "A26"
    assert "already dead" not in line.text


def test_an_empty_watch_on_a_survivor_means_no_one_else_acted_on_them():
    roles, player_of = _game("serial_killer", "fortune_teller")
    trailseer = player_of["trailseer"]
    choices = [NightChoice(player_of["sentinel"], "sentinel", "watch", trailseer),
               NightChoice(player_of["fortune_teller"], "fortune_teller", "bet", trailseer)]
    records, lines, _ = _after_night(choices, roles, 1, player_of["sentinel"])
    assert format_night_actions(records, implications=lines) == (
        f"Night 1: you watched {trailseer}. No one visited {trailseer} tonight. {trailseer} survived, so no "
        f"visit to {trailseer} was hidden: no one attacked, protected, checked, blocked, followed or set a "
        f"sigil on {trailseer} that night. This says nothing about what {trailseer} did."
    )
    assert _the_one_line(lines).row == "A32"


def test_an_empty_watch_on_a_victim_the_living_illusionist_hid_never_says_no_one_attacked():
    """The carrier (here the illusionist itself) killed and concealed: its visits are hidden, so
    "no one attacked" would be false. The morning's line (A30, slice 5) says so instead."""
    roles, player_of = _game("serial_killer", "speculator")
    trailseer, illusionist = player_of["trailseer"], player_of["illusionist"]
    choices = [NightChoice(illusionist, "illusionist", "kill", trailseer),
               NightChoice(illusionist, "illusionist", "conceal", None),
               NightChoice(player_of["sentinel"], "sentinel", "watch", trailseer)]
    records, lines, outcome = _after_night(choices, roles, 2, player_of["sentinel"])
    assert trailseer in outcome.concealed
    assert records[0].outcome == f"No one visited {trailseer} tonight."
    line = _the_one_line(lines)
    assert line.row == "A30"
    assert "no one attacked" not in line.text


# --- A33, A34, A35: the follow --------------------------------------------------------------------

def test_a_follow_with_one_destination_is_a_visit_by_the_followed_player():
    roles, player_of = _game("necromancer", "fortune_teller")
    healer, sigilist = player_of["healer"], player_of["sigilist"]
    choices = [NightChoice(healer, "healer", "protect", sigilist),
               NightChoice(player_of["trailseer"], "trailseer", "follow", healer)]
    records, lines, _ = _after_night(choices, roles, 2, player_of["trailseer"])
    assert format_night_actions(records, implications=lines) == (
        f"Night 2: you followed {healer}. Tonight {healer} visited {sigilist}. A visit does not show which "
        f"action was taken. {healer} is not the Necromancer or the Fortune Teller: the Necromancer visits "
        "only under a dead player's name, and the Fortune Teller never visits."
    )
    assert _the_one_line(lines).row == "A33"


def test_a_follow_with_two_destinations_is_the_chanteuse_carrying_the_kill():
    roles, player_of = _game("serial_killer", "speculator")
    chanteuse, investigator, healer = player_of["chanteuse"], player_of["investigator"], player_of["healer"]
    choices = [NightChoice(chanteuse, "chanteuse", "kill", investigator),
               NightChoice(chanteuse, "chanteuse", "block", healer),
               NightChoice(player_of["trailseer"], "trailseer", "follow", chanteuse)]
    _, lines, _ = _after_night(choices, roles, 1, player_of["trailseer"])
    line = _the_one_line(lines)
    assert line.row == "A34"
    assert line.text == (
        "Only a wolf who carries the pack's kill and also blocks someone visits two players, so "
        f"{chanteuse} is the Chanteuse and carried the kill that night: one of {investigator} and {healer} "
        "was the pack's target, the other the player she tried to block.")


def test_a_block_attempt_on_the_neutral_still_shows_two_destinations():
    """A34 says "tried to block": a block on the speculator has no effect but is still a visit."""
    roles, player_of = _game("serial_killer", "speculator")
    chanteuse = player_of["chanteuse"]
    choices = [NightChoice(chanteuse, "chanteuse", "kill", player_of["investigator"]),
               NightChoice(chanteuse, "chanteuse", "block", player_of["speculator"]),
               NightChoice(player_of["trailseer"], "trailseer", "follow", chanteuse)]
    _, lines, outcome = _after_night(choices, roles, 1, player_of["trailseer"])
    assert outcome.blocked == []
    assert _the_one_line(lines).row == "A34"


def test_a_chanteuse_blocking_her_own_victim_shows_one_destination_and_is_not_named():
    roles, player_of = _game("serial_killer", "speculator")
    chanteuse, investigator = player_of["chanteuse"], player_of["investigator"]
    choices = [NightChoice(chanteuse, "chanteuse", "kill", investigator),
               NightChoice(chanteuse, "chanteuse", "block", investigator),
               NightChoice(player_of["trailseer"], "trailseer", "follow", chanteuse)]
    _, lines, _ = _after_night(choices, roles, 1, player_of["trailseer"])
    line = _the_one_line(lines)
    assert line.row == "A33"
    assert "Chanteuse" not in line.text


def test_a_follow_that_shows_no_one_rules_out_the_serial_killer_and_an_unblocked_healer():
    roles, player_of = _game("serial_killer", "speculator")
    speculator = player_of["speculator"]
    choices = [NightChoice(player_of["trailseer"], "trailseer", "follow", speculator)]
    records, lines, _ = _after_night(choices, roles, 1, player_of["trailseer"])
    assert format_night_actions(records, implications=lines) == (
        f"Night 1: you followed {speculator}. {speculator} visited no one tonight. No visit was made in "
        f"{speculator}'s name that night, so {speculator} is not the Serial Killer, and not the Healer unless "
        f"{speculator} was roleblocked. This does not show that {speculator} did nothing."
    )
    assert _the_one_line(lines).row == "A35"


def test_a_blocked_healer_visits_no_one_which_is_why_the_line_keeps_unless_roleblocked():
    roles, player_of = _game("serial_killer", "speculator")
    healer = player_of["healer"]
    choices = [NightChoice(player_of["chanteuse"], "chanteuse", "block", healer),
               NightChoice(healer, "healer", "protect", player_of["sigilist"]),
               NightChoice(player_of["trailseer"], "trailseer", "follow", healer)]
    _, lines, _ = _after_night(choices, roles, 1, player_of["trailseer"])
    assert _the_one_line(lines).text == (
        f"No visit was made in {healer}'s name that night, so {healer} is not the Serial Killer, and not "
        f"the Healer unless {healer} was roleblocked. This does not show that {healer} did nothing.")


def test_with_no_possible_blocker_no_visit_rules_the_healer_out():
    """SK cast, the Chanteuse lynched before the night: no one could block."""
    roles, player_of = _game("serial_killer", "speculator")
    sentinel = player_of["sentinel"]
    choices = [NightChoice(player_of["trailseer"], "trailseer", "follow", sentinel)]
    _, lines, _ = _after_night(choices, roles, 2, player_of["trailseer"],
                               earlier_deaths=[_lynched(player_of["chanteuse"], "chanteuse", 2)])
    assert _the_one_line(lines).text == (
        f"No visit was made in {sentinel}'s name that night, so {sentinel} is not the Serial Killer, and "
        f"not the Healer. This does not show that {sentinel} did nothing.")


def test_the_chanteuse_hidden_with_her_victim_visits_no_one_and_is_not_ruled_out():
    """The R5 case: the carrier Chanteuse blocks her own victim, the living illusionist conceals it."""
    roles, player_of = _game("serial_killer", "speculator")
    chanteuse, speculator = player_of["chanteuse"], player_of["speculator"]
    choices = [NightChoice(chanteuse, "chanteuse", "kill", speculator),
               NightChoice(chanteuse, "chanteuse", "block", speculator),
               NightChoice(player_of["illusionist"], "illusionist", "conceal", None),
               NightChoice(player_of["trailseer"], "trailseer", "follow", chanteuse)]
    records, lines, _ = _after_night(choices, roles, 1, player_of["trailseer"])
    assert records[-1].outcome == f"{chanteuse} visited no one tonight."
    line = _the_one_line(lines)
    assert "Chanteuse" not in line.text and "wolf" not in line.text


def test_in_a_necromancer_cast_a_follow_on_the_necromancer_shows_no_one():
    roles, player_of = _game("necromancer", "speculator")
    necromancer = player_of["necromancer"]
    choices = [NightChoice(necromancer, "necromancer", "protect", player_of["sigilist"], via=player_of["healer"]),
               NightChoice(player_of["trailseer"], "trailseer", "follow", necromancer)]
    _, lines, _ = _after_night(choices, roles, 2, player_of["trailseer"],
                               earlier_deaths=[_lynched(player_of["healer"], "healer", 2)])
    # The Healer is dead, and there is no Serial Killer: nothing to rule out.
    assert lines == [None]


def test_the_necromancer_following_through_a_body_knows_it_did_not_block():
    """NE cast, the Chanteuse dead: only the Necromancer could block, and it followed instead."""
    roles, player_of = _game("necromancer", "speculator")
    trailseer, healer = player_of["trailseer"], player_of["healer"]
    earlier = [_lynched(player_of["chanteuse"], "chanteuse", 2), _lynched(trailseer, "trailseer", 2)]
    choices = [NightChoice(player_of["necromancer"], "necromancer", "follow", healer, via=trailseer)]
    _, lines, _ = _after_night(choices, roles, 2, player_of["necromancer"], earlier_deaths=earlier)
    # The healer always protects someone; with no possible block, "visited no one" rules it out.
    assert _the_one_line(lines).text == (
        f"No visit was made in {healer}'s name that night, so {healer} is not the Healer. This does not "
        f"show that {healer} did nothing.")


# --- A37, A38, A39: the sigil ---------------------------------------------------------------------

def test_a_target_saved_from_the_sigil_is_a_wolf_or_the_vigilante():
    roles, player_of = _game("serial_killer", "speculator")
    chanteuse = player_of["chanteuse"]
    choices = [NightChoice(chanteuse, "chanteuse", "kill", player_of["investigator"]),
               NightChoice(player_of["sigilist"], "sigilist", "sigil", chanteuse),
               NightChoice(player_of["healer"], "healer", "protect", chanteuse)]
    records, lines, _ = _after_night(choices, roles, 1, player_of["sigilist"])
    assert format_night_actions(records, implications=lines) == (
        f"Night 1: you set a sigil on {chanteuse}. {chanteuse} attacked someone tonight, but the healer's "
        f"protection saved them from your sigil. {chanteuse} attacked someone and needed saving from your "
        f"sigil, so {chanteuse} is a wolf or the Vigilante."
    )
    assert _the_one_line(lines).row == "A37"


def test_with_the_vigilante_dead_a_target_saved_from_the_sigil_is_a_wolf():
    roles, player_of = _game("necromancer", "speculator")
    illusionist = player_of["illusionist"]
    choices = [NightChoice(illusionist, "illusionist", "kill", player_of["investigator"]),
               NightChoice(player_of["sigilist"], "sigilist", "sigil", illusionist),
               NightChoice(player_of["healer"], "healer", "protect", illusionist)]
    _, lines, _ = _after_night(choices, roles, 2, player_of["sigilist"],
                               earlier_deaths=[_lynched(player_of["vigilante"], "vigilante", 2)])
    assert _the_one_line(lines).text == (f"{illusionist} attacked someone and needed saving from your sigil, "
                                         f"so {illusionist} is a wolf.")


def test_a_sigil_on_the_serial_killer_reads_like_a_quiet_night():
    roles, player_of = _game("serial_killer", "speculator")
    killer = player_of["serial_killer"]
    choices = [NightChoice(killer, "serial_killer", "kill", player_of["investigator"]),
               NightChoice(player_of["sigilist"], "sigilist", "sigil", killer)]
    records, lines, _ = _after_night(choices, roles, 1, player_of["sigilist"])
    line = _the_one_line(lines)
    assert (line.row, line.grade) == ("A38", "possible")
    assert format_night_actions(records, implications=lines) == (
        f"Night 1: you set a sigil on {killer}. Your sigil had no effect. Either {killer} attacked no one "
        f"that night, or {killer} is the Serial Killer, whom a sigil cannot harm."
    )


def test_with_the_serial_killer_dead_a_sigil_with_no_effect_means_no_attack():
    roles, player_of = _game("serial_killer", "speculator")
    healer = player_of["healer"]
    choices = [NightChoice(player_of["sigilist"], "sigilist", "sigil", healer)]
    _, lines, _ = _after_night(choices, roles, 2, player_of["sigilist"],
                               earlier_deaths=[_lynched(player_of["serial_killer"], "serial_killer", 2)])
    assert _the_one_line(lines).text == f"{healer} did not attack anyone that night."


def test_a_sigil_misses_the_necromancer_killing_through_a_body():
    roles, player_of = _game("necromancer", "speculator")
    necromancer = player_of["necromancer"]
    choices = [NightChoice(necromancer, "necromancer", "kill", player_of["investigator"], via=player_of["vigilante"]),
               NightChoice(player_of["sigilist"], "sigilist", "sigil", necromancer)]
    records, lines, outcome = _after_night(choices, roles, 2, player_of["sigilist"],
                                           earlier_deaths=[_lynched(player_of["vigilante"], "vigilante", 2)])
    assert player_of["investigator"] in outcome.deaths and records[0].result == "miss"
    line = _the_one_line(lines)
    assert line.row == "A39"
    assert line.text == (f"{necromancer} did not attack anyone that night, unless {necromancer} is the "
                         "Necromancer attacking through a dead player's body.")


def test_on_night_one_the_necromancer_cannot_have_attacked():
    roles, player_of = _game("necromancer", "fortune_teller")
    necromancer = player_of["necromancer"]
    choices = [NightChoice(player_of["sigilist"], "sigilist", "sigil", necromancer)]
    _, lines, _ = _after_night(choices, roles, 1, player_of["sigilist"])
    assert _the_one_line(lines).text == f"{necromancer} did not attack anyone that night."


def test_the_necromancers_sigil_through_a_body_has_no_necromancer_branch():
    roles, player_of = _game("necromancer", "speculator")
    sigilist, healer = player_of["sigilist"], player_of["healer"]
    choices = [NightChoice(player_of["necromancer"], "necromancer", "sigil", healer, via=sigilist)]
    _, lines, _ = _after_night(choices, roles, 2, player_of["necromancer"],
                               earlier_deaths=[_lynched(sigilist, "sigilist", 2)])
    assert _the_one_line(lines).text == f"{healer} did not attack anyone that night."


# --- A40–A43: the block ----------------------------------------------------------------------------

def test_the_chanteuses_block_that_took_shows_a_town_player():
    roles, player_of = _game("serial_killer", "speculator")
    healer = player_of["healer"]
    choices = [NightChoice(player_of["chanteuse"], "chanteuse", "block", healer)]
    records, lines, _ = _after_night(choices, roles, 1, player_of["chanteuse"])
    assert format_night_actions(records, implications=lines) == (
        f"Night 1: you blocked {healer}. {healer} was roleblocked tonight. Your block took, so {healer} is "
        "on the Town side."
    )
    assert _the_one_line(lines).row == "A40"


def test_the_chanteuses_block_that_did_not_take_is_the_killer_or_the_neutral():
    roles, player_of = _game("serial_killer", "speculator")
    killer = player_of["serial_killer"]
    choices = [NightChoice(player_of["chanteuse"], "chanteuse", "block", killer)]
    _, lines, _ = _after_night(choices, roles, 1, player_of["chanteuse"])
    line = _the_one_line(lines)
    assert line.row == "A41"
    assert line.text == (f"Only the Serial Killer and the Speculator cannot be blocked, so {killer} is "
                         "one of them.")


def test_after_the_pack_found_the_serial_killer_a_failed_block_is_the_neutral():
    """A41 with A13: the pack's attack on night 1 showed who the Serial Killer is."""
    roles, player_of = _game("serial_killer", "speculator")
    killer, speculator, chanteuse = player_of["serial_killer"], player_of["speculator"], player_of["chanteuse"]
    night_one = [NightChoice(chanteuse, "chanteuse", "kill", killer)]
    night_two = [NightChoice(player_of["illusionist"], "illusionist", "kill", player_of["healer"]),
                 NightChoice(chanteuse, "chanteuse", "block", speculator)]
    records = []
    for night, choices in ((1, night_one), (2, night_two)):
        records += night_action_records(choices, resolve_night(choices, roles, night), roles)
    roster = [_killed(player_of["healer"], "healer", 2)]
    lines = own_result_lines(_seat_view(chanteuse, roles, records, roster))
    assert lines[-1].text == (f"Only the Serial Killer and the Speculator cannot be blocked, and {speculator} is "
                              f"not the Serial Killer, so {speculator} is the Speculator.")


def test_a_block_through_the_chanteuses_body_that_took_may_be_on_a_wolf():
    roles, player_of = _game("necromancer", "speculator")
    chanteuse, illusionist = player_of["chanteuse"], player_of["illusionist"]
    choices = [NightChoice(player_of["necromancer"], "necromancer", "block", illusionist, via=chanteuse)]
    records, lines, _ = _after_night(choices, roles, 2, player_of["necromancer"],
                                     earlier_deaths=[_lynched(chanteuse, "chanteuse", 2)])
    assert records[0].result == "blocked"
    line = _the_one_line(lines)
    assert line.row == "A42"
    assert line.text == f"{illusionist} is a Town player or a wolf: a block does not take on the Speculator."


def test_a_block_through_the_chanteuses_body_that_did_not_take_is_the_neutral():
    roles, player_of = _game("necromancer", "fortune_teller")
    chanteuse, fortune_teller = player_of["chanteuse"], player_of["fortune_teller"]
    choices = [NightChoice(player_of["necromancer"], "necromancer", "block", fortune_teller, via=chanteuse)]
    records, lines, _ = _after_night(choices, roles, 3, player_of["necromancer"],
                                     earlier_deaths=[_killed(chanteuse, "chanteuse", 1)])
    assert format_night_actions(records, implications=lines) == (
        f"Night 3: you blocked {fortune_teller}. Through {chanteuse}'s body: Your block did not affect "
        f"{fortune_teller}. Only you and the Fortune Teller cannot be blocked, so {fortune_teller} is the "
        "Fortune Teller."
    )
    assert _the_one_line(lines).row == "A43"


# --- A49, A50: a scored bet on a hidden body ------------------------------------------------------

def _bet_on_hidden_victim(role_named):
    roles, player_of = _game("serial_killer", "fortune_teller")
    healer = player_of["healer"]
    choices = [NightChoice(player_of["chanteuse"], "chanteuse", "kill", healer),
               NightChoice(player_of["illusionist"], "illusionist", "conceal", None),
               NightChoice(player_of["fortune_teller"], "fortune_teller", "bet", healer, role_named=role_named)]
    records, lines, outcome = _after_night(choices, roles, 1, player_of["fortune_teller"])
    assert healer in outcome.concealed
    return healer, records, lines


def test_a_two_point_bet_on_a_hidden_body_shows_its_role():
    healer, records, lines = _bet_on_hidden_victim("healer")
    assert format_night_actions(records, implications=lines) == (
        f"Night 1: you bet on {healer}. {healer} died and was a healer: two points. {healer}'s role was "
        f"hidden, but your bet shows {healer} was the Healer."
    )
    assert _the_one_line(lines).row == "A49"


def test_a_one_point_bet_on_a_hidden_body_rules_out_the_named_role():
    healer, _, lines = _bet_on_hidden_victim("sentinel")
    line = _the_one_line(lines)
    assert line.row == "A50"
    assert line.text == f"{healer}'s role was hidden, but your bet shows {healer} was not the Sentinel."


def test_a_bet_naming_a_role_the_fortune_teller_already_ruled_out_adds_nothing():
    _, _, lines = _bet_on_hidden_victim("fortune_teller")
    assert lines == [None]


def test_a_scored_bet_on_a_revealed_body_needs_no_line():
    roles, player_of = _game("serial_killer", "fortune_teller")
    healer = player_of["healer"]
    choices = [NightChoice(player_of["chanteuse"], "chanteuse", "kill", healer),
               NightChoice(player_of["fortune_teller"], "fortune_teller", "bet", healer, role_named="healer")]
    records, lines, _ = _after_night(choices, roles, 1, player_of["fortune_teller"])
    assert records[0].result == "scored_2"
    assert lines == [None]
