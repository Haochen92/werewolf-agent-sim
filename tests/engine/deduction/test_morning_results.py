"""Level 1 of the deduction engine, slice 5: the rows that read a seat's own result together with the
public morning announcement (Agents/deduction/morning.py): A22 conditions b and c (checks.py), A28–A31
(own_results/at_the_door.py, shown with the watch), A36's concealed case (sigils.py) and A45
(conceals.py), rows of evidence/reasoning_failures/deduction_catalogue.md, Table A.

Every night here runs through the real engine, the resolution node included: the morning a seat
reads is the one the node committed. Per row: a night where it fires, with the exact line; nights
that differ in one respect where it must not fire or must weaken (a kill through a body, the
fortune teller's self-bet, the living against the reanimated illusionist's conceal, a reanimated
healer, a payload with no morning). Hidden-state swaps check that a line depends only on what the
seat was told; the random-night soundness check for these rows is in test_own_results.py.
"""

from __future__ import annotations

from dataclasses import replace

from Agents.deduction import own_result_lines
from Agents.prompts.prompt_formatters import format_night_actions
from Agents.rules.night import resolve_night
from Agents.rules.night_record import night_action_records
from Agents.schemas.game_events import DeathRecord
from Agents.schemas.night import NightChoice
from tests.engine.deduction.test_own_results import _after_night, _game, _seat_view, _the_one_line
from tests.factories.random_nights import resolve_through_the_node


def _own_visit(target: str) -> str:
    """A56, last on every line of the living Sentinel's own watch."""
    return (f" Your watch was itself your visit to {target}; your own result never lists you. So a follow on you "
            f"that night shows you going to {target}.")


def _lynched(player: str, role: str, day: int) -> DeathRecord:
    return DeathRecord(player=player, role=role, day=day, phase="day")


def _without_the_morning(choices, roles, night, receiver, earlier_deaths=(), body_conceals=0):
    """The receiver's lines from a payload that carries no morning (a game from before slice 4)."""
    outcome = resolve_night(choices, roles, night, body_conceals)
    records = night_action_records(choices, outcome, roles)
    roster = list(earlier_deaths) + [
        DeathRecord(player=player, role="" if player in outcome.concealed else roles[player], day=night,
                    phase="night", concealed=player in outcome.concealed)
        for player in outcome.deaths]
    return own_result_lines(_seat_view(receiver, roles, records, roster))


# --- A22 (b), (c): Suspicious, read with the morning -------------------------------------------------

def test_with_no_kill_through_a_body_announced_suspicious_is_a_wolf():
    """A22 (c): a killing body was usable, but every kill through a body is announced from night 2."""
    roles, player_of = _game("necromancer", "speculator")
    chanteuse = player_of["chanteuse"]
    choices = [NightChoice(player_of["investigator"], "investigator", "investigate", chanteuse),
               NightChoice(player_of["illusionist"], "illusionist", "kill", player_of["sentinel"])]
    earlier = [_lynched(player_of["vigilante"], "vigilante", 2)]
    records, lines, _ = _after_night(choices, roles, 3, player_of["investigator"], earlier_deaths=earlier)
    assert format_night_actions(records, implications=lines) == (
        f"Night 3: you checked {chanteuse}. {chanteuse} reads Suspicious. No attack through a dead player's "
        "body was announced that night, and every such attack is announced, so the Necromancer made no kill "
        f"and could not read Suspicious: {chanteuse} is a wolf.")
    line = _the_one_line(lines)
    assert (line.row, line.grade) == ("A22", "certain")


def test_a_save_through_the_healers_body_was_the_necromancers_whole_night():
    """A22 (b): the reanimated healer's save is the Necromancer's one action, so it made no kill."""
    roles, player_of = _game("necromancer", "speculator")
    chanteuse, sentinel = player_of["chanteuse"], player_of["sentinel"]
    choices = [NightChoice(player_of["investigator"], "investigator", "investigate", chanteuse),
               NightChoice(chanteuse, "chanteuse", "kill", sentinel),
               NightChoice(player_of["necromancer"], "necromancer", "protect", sentinel, via=player_of["healer"])]
    earlier = [_lynched(player_of["vigilante"], "vigilante", 2), _lynched(player_of["healer"], "healer", 3)]
    _, lines, _ = _after_night(choices, roles, 3, player_of["investigator"], earlier_deaths=earlier)
    assert _the_one_line(lines).text == (
        "The Necromancer acts once a night, and the morning shows it saved a player through the dead Healer's "
        f"body that night, so it made no kill and could not read Suspicious: {chanteuse} is a wolf.")


def test_a_sigil_through_the_sigilists_body_was_the_necromancers_whole_night():
    roles, player_of = _game("necromancer", "speculator")
    chanteuse, illusionist = player_of["chanteuse"], player_of["illusionist"]
    choices = [NightChoice(player_of["investigator"], "investigator", "investigate", illusionist),
               NightChoice(chanteuse, "chanteuse", "kill", player_of["sentinel"]),
               NightChoice(player_of["necromancer"], "necromancer", "sigil", chanteuse, via=player_of["sigilist"])]
    earlier = [_lynched(player_of["vigilante"], "vigilante", 2), _lynched(player_of["sigilist"], "sigilist", 3)]
    _, lines, outcome = _after_night(choices, roles, 3, player_of["investigator"], earlier_deaths=earlier)
    assert chanteuse in outcome.deaths
    assert _the_one_line(lines).text == (
        "The Necromancer acts once a night, and the morning shows it set a sigil through the dead Sigilist's "
        f"body that night, so it made no kill and could not read Suspicious: {illusionist} is a wolf.")


def test_a_kill_through_a_body_stopped_by_a_self_bet_is_announced_so_suspicious_stays_open():
    """R10: the self-bet stops the Necromancer's kill through the Vigilante's body, the morning
    announces it, and the Necromancer it read is Suspicious: "is a wolf" would be false here."""
    roles, player_of = _game("necromancer", "fortune_teller")
    necromancer, fortune_teller = player_of["necromancer"], player_of["fortune_teller"]
    choices = [NightChoice(player_of["investigator"], "investigator", "investigate", necromancer),
               NightChoice(fortune_teller, "fortune_teller", "bet", fortune_teller),
               NightChoice(necromancer, "necromancer", "kill", fortune_teller, via=player_of["vigilante"])]
    _, lines, outcome = _after_night(choices, roles, 3, player_of["investigator"],
                                     earlier_deaths=[_lynched(player_of["vigilante"], "vigilante", 2)])
    assert not outcome.deaths
    line = _the_one_line(lines)
    assert (line.row, line.grade) == ("A22", "possible")
    assert line.text == (f"So {necromancer} is a wolf, or the Necromancer if it killed through a dead player's "
                         "body that night.")


def test_a_kill_through_a_body_saved_by_the_healer_keeps_suspicious_open():
    roles, player_of = _game("necromancer", "speculator")
    necromancer, sentinel = player_of["necromancer"], player_of["sentinel"]
    choices = [NightChoice(player_of["investigator"], "investigator", "investigate", necromancer),
               NightChoice(player_of["healer"], "healer", "protect", sentinel),
               NightChoice(necromancer, "necromancer", "kill", sentinel, via=player_of["vigilante"])]
    _, lines, _ = _after_night(choices, roles, 3, player_of["investigator"],
                               earlier_deaths=[_lynched(player_of["vigilante"], "vigilante", 2)])
    assert _the_one_line(lines).grade == "possible"


def test_without_the_morning_on_the_payload_suspicious_stays_open():
    roles, player_of = _game("necromancer", "speculator")
    choices = [NightChoice(player_of["investigator"], "investigator", "investigate", player_of["chanteuse"])]
    lines = _without_the_morning(choices, roles, 3, player_of["investigator"],
                                 earlier_deaths=[_lynched(player_of["vigilante"], "vigilante", 2)])
    assert _the_one_line(lines).grade == "possible"


# --- A28: the attackers at the watched door -----------------------------------------------------

def test_the_only_visitor_who_can_be_the_serial_killer_is_named():
    roles, player_of = _game("serial_killer", "speculator")
    trailseer, killer = player_of["trailseer"], player_of["serial_killer"]
    choices = [NightChoice(killer, "serial_killer", "kill", trailseer),
               NightChoice(player_of["sentinel"], "sentinel", "watch", trailseer)]
    records, lines, _ = _after_night(choices, roles, 1, player_of["sentinel"])
    assert format_night_actions(records, implications=lines) == (
        f"Night 1: you watched {trailseer}. Tonight {trailseer} was visited by {killer}. A visit does not show "
        f"which action was taken. {killer} is not the Speculator: the Speculator never visits. Everyone who "
        f"attacked {trailseer} came to {trailseer}, and your watch saw every visitor but you. Of the players you "
        f"saw, only {killer} can be the Serial Killer, so {killer} is the Serial Killer.{_own_visit(trailseer)}")
    line = _the_one_line(lines)
    assert (line.row, line.grade) == ("A26+A28+A56", "certain")


def test_two_visitors_who_could_each_be_the_wolf_are_both_named():
    roles, player_of = _game("serial_killer", "speculator")
    trailseer = player_of["trailseer"]
    choices = [NightChoice(player_of["chanteuse"], "chanteuse", "kill", trailseer),
               NightChoice(player_of["investigator"], "investigator", "investigate", trailseer),
               NightChoice(player_of["sentinel"], "sentinel", "watch", trailseer)]
    _, lines, _ = _after_night(choices, roles, 1, player_of["sentinel"])
    assert _the_one_line(lines).text.endswith(
        f"The wolf who attacked {trailseer} is {player_of['investigator']} or {player_of['chanteuse']}."
        f"{_own_visit(trailseer)}")


def test_a_visitor_revealed_this_morning_settles_who_made_the_other_attack():
    """Different attack types are different players: the vigilante, revealed when the serial killer
    killed it the same night, made the shot, so the other visitor made the wolves' attack."""
    roles, player_of = _game("serial_killer", "speculator")
    trailseer, vigilante, chanteuse = player_of["trailseer"], player_of["vigilante"], player_of["chanteuse"]
    choices = [NightChoice(chanteuse, "chanteuse", "kill", trailseer),
               NightChoice(vigilante, "vigilante", "kill", trailseer),
               NightChoice(player_of["serial_killer"], "serial_killer", "kill", vigilante),
               NightChoice(player_of["sentinel"], "sentinel", "watch", trailseer)]
    _, lines, outcome = _after_night(choices, roles, 1, player_of["sentinel"])
    assert vigilante in outcome.deaths
    assert _the_one_line(lines).text.endswith(
        f"Of the players you saw, only {chanteuse} can be the wolf who attacked {trailseer}, so {chanteuse} is a "
        f"wolf. Of the players you saw, only {vigilante} can be the Vigilante, so {vigilante} is the Vigilante."
        f"{_own_visit(trailseer)}")


def test_the_necromancer_watching_through_the_sentinels_body_names_the_shooter():
    roles, player_of = _game("necromancer", "speculator")
    trailseer, vigilante = player_of["trailseer"], player_of["vigilante"]
    choices = [NightChoice(vigilante, "vigilante", "kill", trailseer),
               NightChoice(player_of["necromancer"], "necromancer", "watch", trailseer, via=player_of["sentinel"])]
    _, lines, _ = _after_night(choices, roles, 2, player_of["necromancer"],
                               earlier_deaths=[_lynched(player_of["sentinel"], "sentinel", 2)])
    assert _the_one_line(lines).text.endswith(
        f"Of the players you saw, only {vigilante} can be the Vigilante, so {vigilante} is the Vigilante.")


def test_an_attack_through_a_body_is_explained_by_the_body_alone():
    """A reanimated vigilante's shot shows the dead vigilante's name: A27 says what it was, and no
    living visitor is called the shooter."""
    roles, player_of = _game("necromancer", "speculator")
    trailseer, vigilante = player_of["trailseer"], player_of["vigilante"]
    choices = [NightChoice(player_of["necromancer"], "necromancer", "kill", trailseer, via=vigilante),
               NightChoice(player_of["investigator"], "investigator", "investigate", trailseer),
               NightChoice(player_of["sentinel"], "sentinel", "watch", trailseer)]
    _, lines, _ = _after_night(choices, roles, 2, player_of["sentinel"],
                               earlier_deaths=[_lynched(vigilante, "vigilante", 2)])
    line = _the_one_line(lines)
    assert line.row == "A27+A56"
    assert "Of the players you saw" not in line.text and " is the Vigilante" not in line.text


# --- A29: the Healer at the watched door ----------------------------------------------------------

def _wolf_and_healer_at_the_door(roles, carrier, healer, target, watcher):
    choices = [NightChoice(carrier, roles[carrier], "kill", target),
               NightChoice(healer, "healer", "protect", target),
               NightChoice(watcher, "sentinel", "watch", target)]
    return _after_night(choices, roles, 1, watcher)


def test_a_wolf_and_the_healer_at_the_door_are_named_together_never_apart():
    """The catalogue's A28/A29 interplay: two living names, one attack by the wolves, one save by the
    Healer. One is a wolf and the other the Healer, and the line must not say which."""
    roles, player_of = _game("serial_killer", "speculator")
    healer, chanteuse, trailseer = player_of["healer"], player_of["chanteuse"], player_of["trailseer"]
    records, lines, _ = _wolf_and_healer_at_the_door(roles, chanteuse, healer, trailseer, player_of["sentinel"])
    line = _the_one_line(lines)
    assert (line.row, line.grade) == ("A26+A28+A29+A56", "certain")
    assert line.text.endswith(
        f"Everyone who attacked {trailseer} and the Healer who saved them came to {trailseer}, and your watch saw "
        f"every visitor but you. {healer} and {chanteuse} are a wolf and the Healer, one each; your watch does not "
        f"show which is which.{_own_visit(trailseer)}")
    for name in (healer, chanteuse):
        assert f"{name} is a wolf" not in line.text and f"{name} is the Healer" not in line.text

    # The other hidden state the watcher cannot tell apart: the two players' roles swapped.
    swapped = {**roles, healer: "chanteuse", chanteuse: "healer"}
    swapped_records, swapped_lines, _ = _wolf_and_healer_at_the_door(swapped, healer, chanteuse, trailseer,
                                                                     player_of["sentinel"])
    assert swapped_records == records and swapped_lines == lines


def test_when_the_wolf_is_known_the_other_visitor_is_the_healer():
    roles, player_of = _game("serial_killer", "speculator")
    healer, chanteuse, trailseer = player_of["healer"], player_of["chanteuse"], player_of["trailseer"]
    choices = [NightChoice(chanteuse, "chanteuse", "kill", trailseer),
               NightChoice(healer, "healer", "protect", trailseer),
               NightChoice(player_of["vigilante"], "vigilante", "kill", chanteuse),
               NightChoice(player_of["sentinel"], "sentinel", "watch", trailseer)]
    _, lines, _ = _after_night(choices, roles, 2, player_of["sentinel"])
    assert _the_one_line(lines).text.endswith(
        f"Of the players you saw, only {chanteuse} can be the wolf who attacked {trailseer}, so {chanteuse} is a "
        f"wolf. Of the players you saw, only {healer} can be the Healer, so {healer} is the Healer."
        f"{_own_visit(trailseer)}")


def test_a_reanimated_healers_save_names_no_living_healer():
    roles, player_of = _game("necromancer", "speculator")
    healer, chanteuse, trailseer = player_of["healer"], player_of["chanteuse"], player_of["trailseer"]
    choices = [NightChoice(chanteuse, "chanteuse", "kill", trailseer),
               NightChoice(player_of["necromancer"], "necromancer", "protect", trailseer, via=healer),
               NightChoice(player_of["sentinel"], "sentinel", "watch", trailseer)]
    _, lines, _ = _after_night(choices, roles, 2, player_of["sentinel"], earlier_deaths=[_lynched(healer, "healer", 2)])
    line = _the_one_line(lines)
    assert line.row == "A27+A28+A56"
    assert "the Healer who saved them" not in line.text and "is the Healer" not in line.text
    assert line.text.endswith(f"so {chanteuse} is a wolf.{_own_visit(trailseer)}")


def test_a_self_bet_save_has_no_healer_at_the_door():
    roles, player_of = _game("serial_killer", "fortune_teller")
    fortune_teller, killer = player_of["fortune_teller"], player_of["serial_killer"]
    choices = [NightChoice(killer, "serial_killer", "kill", fortune_teller),
               NightChoice(fortune_teller, "fortune_teller", "bet", fortune_teller),
               NightChoice(player_of["sentinel"], "sentinel", "watch", fortune_teller)]
    _, lines, _ = _after_night(choices, roles, 2, player_of["sentinel"])
    line = _the_one_line(lines)
    assert line.row == "A26+A28+A56"
    assert line.text.endswith(f"Of the players you saw, only {killer} can be the Serial Killer, so {killer} is "
                              f"the Serial Killer.{_own_visit(fortune_teller)}")


# --- A30: a victim the living Illusionist hid ----------------------------------------------------

def test_an_empty_watch_on_a_victim_the_living_illusionist_hid_shows_the_illusionist_made_the_kill():
    roles, player_of = _game("serial_killer", "speculator")
    trailseer, illusionist = player_of["trailseer"], player_of["illusionist"]
    choices = [NightChoice(illusionist, "illusionist", "kill", trailseer),
               NightChoice(illusionist, "illusionist", "conceal", None),
               NightChoice(player_of["sentinel"], "sentinel", "watch", trailseer)]
    records, lines, _ = _after_night(choices, roles, 2, player_of["sentinel"])
    assert format_night_actions(records, implications=lines) == (
        f"Night 2: you watched {trailseer}. No one visited {trailseer} tonight. {trailseer}'s role was hidden by "
        "the living Illusionist, whose conceal also hides the visit of the wolf who made the kill: your watch "
        f"could not see that wolf. The Illusionist's conceal is a visit to {trailseer}, and none of the players "
        f"you saw can be the Illusionist, so the Illusionist made the kill itself.{_own_visit(trailseer)}")
    line = _the_one_line(lines)
    assert (line.row, line.grade) == ("A30+A56", "certain")


def test_a_concealing_illusionist_that_did_not_carry_is_among_the_visitors():
    roles, player_of = _game("serial_killer", "speculator")
    trailseer, illusionist = player_of["trailseer"], player_of["illusionist"]
    choices = [NightChoice(player_of["chanteuse"], "chanteuse", "kill", trailseer),
               NightChoice(illusionist, "illusionist", "conceal", None),
               NightChoice(player_of["sentinel"], "sentinel", "watch", trailseer)]
    _, lines, _ = _after_night(choices, roles, 1, player_of["sentinel"])
    line = _the_one_line(lines)
    assert (line.row, line.grade) == ("A26+A30+A56", "possible")
    assert line.text.endswith(f"The Illusionist's conceal is a visit to {trailseer}, so either the Illusionist "
                              f"made the kill itself, or it is {illusionist}.{_own_visit(trailseer)}")
    assert "wolf who attacked" not in line.text  # the killer's visit is hidden: no wolf is placed at the door


def test_the_same_watch_reads_the_same_whoever_concealed():
    """Two hidden states the watcher cannot tell apart: player_8 is the concealing Illusionist, or the
    Investigator checking the victim while the Illusionist carried and concealed unseen."""
    roles, player_of = _game("serial_killer", "speculator")
    trailseer, sentinel = player_of["trailseer"], player_of["sentinel"]
    choices = [NightChoice(player_of["chanteuse"], "chanteuse", "kill", trailseer),
               NightChoice("player_8", "illusionist", "conceal", None),
               NightChoice(sentinel, "sentinel", "watch", trailseer)]
    records, lines, _ = _after_night(choices, roles, 1, sentinel)
    swapped = {**roles, "player_1": "illusionist", "player_8": "investigator"}
    swapped_choices = [NightChoice("player_1", "illusionist", "kill", trailseer),
                       NightChoice("player_1", "illusionist", "conceal", None),
                       NightChoice("player_8", "investigator", "investigate", trailseer),
                       NightChoice(sentinel, "sentinel", "watch", trailseer)]
    swapped_records, swapped_lines, _ = _after_night(swapped_choices, swapped, 1, sentinel)
    assert swapped_records == records and swapped_lines == lines


def test_another_attacker_on_a_hidden_victim_is_still_at_the_door():
    roles, player_of = _game("serial_killer", "speculator")
    trailseer, killer = player_of["trailseer"], player_of["serial_killer"]
    choices = [NightChoice(player_of["chanteuse"], "chanteuse", "kill", trailseer),
               NightChoice(player_of["illusionist"], "illusionist", "conceal", None),
               NightChoice(killer, "serial_killer", "kill", trailseer),
               NightChoice(player_of["sentinel"], "sentinel", "watch", trailseer)]
    _, lines, _ = _after_night(choices, roles, 1, player_of["sentinel"])
    line = _the_one_line(lines)
    assert line.row == "A26+A30+A28+A56"
    assert line.text.endswith(f"Everyone else who attacked {trailseer} came to {trailseer}, and your watch saw "
                              f"them. The Serial Killer is {player_of['illusionist']} or {killer}.{_own_visit(trailseer)}")


# --- A31: a victim hidden through the Illusionist's body --------------------------------------------

def _hidden_through_the_body(body_conceals):
    roles, player_of = _game("necromancer", "speculator")
    trailseer, illusionist = player_of["trailseer"], player_of["illusionist"]
    choices = [NightChoice(player_of["chanteuse"], "chanteuse", "kill", trailseer),
               NightChoice(player_of["necromancer"], "necromancer", "kill", trailseer, via=illusionist),
               NightChoice(player_of["sentinel"], "sentinel", "watch", trailseer)]
    return player_of, _after_night(choices, roles, 2, player_of["sentinel"],
                                   earlier_deaths=[_lynched(illusionist, "illusionist", 2)], body_conceals=body_conceals)


def test_a_reanimated_illusionists_conceal_hides_no_visit_so_the_carrier_is_seen():
    player_of, (records, lines, outcome) = _hidden_through_the_body(body_conceals=2)
    trailseer, illusionist, chanteuse = player_of["trailseer"], player_of["illusionist"], player_of["chanteuse"]
    assert trailseer in outcome.concealed
    assert format_night_actions(records, implications=lines) == (
        f"Night 2: you watched {trailseer}. Tonight {trailseer} was visited by {chanteuse} and {illusionist}. A "
        f"visit does not show which action was taken. {chanteuse} is not the Necromancer or the Speculator: the "
        "Necromancer visits only under a dead player's name, and the Speculator never visits. "
        f"{illusionist} was already dead, so the Necromancer used {illusionist}'s body to attack {trailseer}. "
        f"{trailseer}'s role was hidden through the dead Illusionist's body, which hides no visit: everyone who "
        f"attacked {trailseer} came to {trailseer}, and your watch saw every visitor but you. Of the players you "
        f"saw, only {chanteuse} can be the wolf who attacked {trailseer}, so {chanteuse} is a wolf."
        f"{_own_visit(trailseer)}")
    assert _the_one_line(lines).row == "A27+A31+A28+A56"


def test_with_no_conceal_left_the_role_is_shown_and_there_is_no_conceal_line():
    player_of, (_, lines, outcome) = _hidden_through_the_body(body_conceals=0)
    assert not outcome.concealed
    line = _the_one_line(lines)
    assert line.row == "A27+A28+A56"
    assert "hidden" not in line.text


# --- A36: a sigil that struck down a hidden player -------------------------------------------------

def test_a_struck_down_player_the_living_illusionist_hid_is_the_vigilante():
    roles, player_of = _game("serial_killer", "speculator")
    vigilante = player_of["vigilante"]
    choices = [NightChoice(vigilante, "vigilante", "kill", player_of["trailseer"]),
               NightChoice(player_of["chanteuse"], "chanteuse", "kill", vigilante),
               NightChoice(player_of["illusionist"], "illusionist", "conceal", None),
               NightChoice(player_of["sigilist"], "sigilist", "sigil", vigilante)]
    records, lines, outcome = _after_night(choices, roles, 1, player_of["sigilist"])
    assert vigilante in outcome.concealed
    assert format_night_actions(records, implications=lines) == (
        f"Night 1: you set a sigil on {vigilante}. {vigilante} attacked someone tonight, and your sigil struck them "
        "down. Only a wolf carrying the pack's kill or the Vigilante can be struck down by a sigil, and "
        f"{vigilante}'s role was hidden by the living Illusionist, who hides only the pack's victim, never a wolf: "
        f"{vigilante} is the Vigilante.")
    assert _the_one_line(lines).row == "A36"


def _struck_down_through_the_body(earlier_deaths, body_conceals=1):
    roles, player_of = _game("necromancer", "speculator")
    chanteuse = player_of["chanteuse"]
    choices = [NightChoice(chanteuse, "chanteuse", "kill", player_of["trailseer"]),
               NightChoice(player_of["necromancer"], "necromancer", "kill", chanteuse, via=player_of["illusionist"]),
               NightChoice(player_of["sigilist"], "sigilist", "sigil", chanteuse)]
    _, lines, outcome = _after_night(choices, roles, 3, player_of["sigilist"], earlier_deaths=earlier_deaths,
                                     body_conceals=body_conceals)
    return chanteuse, lines, outcome


def test_a_struck_down_player_hidden_through_the_body_may_be_a_wolf_or_the_vigilante():
    roles, player_of = _game("necromancer", "speculator")
    chanteuse, lines, outcome = _struck_down_through_the_body([_lynched(player_of["illusionist"], "illusionist", 2)])
    assert chanteuse in outcome.concealed
    assert _the_one_line(lines).text == (
        "Only a wolf carrying the pack's kill or the Vigilante can be struck down by a sigil, so "
        f"{chanteuse}, whose role was hidden, is a wolf or the Vigilante.")


def test_with_the_vigilante_revealed_dead_the_struck_down_hidden_player_is_a_wolf():
    roles, player_of = _game("necromancer", "speculator")
    earlier = [_lynched(player_of["illusionist"], "illusionist", 2), _lynched(player_of["vigilante"], "vigilante", 3)]
    chanteuse, lines, _ = _struck_down_through_the_body(earlier)
    assert _the_one_line(lines).text.endswith(f"so {chanteuse}, whose role was hidden, is a wolf.")


def test_a_struck_down_player_whose_role_was_shown_needs_no_line():
    roles, player_of = _game("necromancer", "speculator")
    _, lines, outcome = _struck_down_through_the_body([_lynched(player_of["illusionist"], "illusionist", 2)],
                                                      body_conceals=0)
    assert not outcome.concealed and lines == [None]


# --- A45: a conceal that found no body ------------------------------------------------------------

def _conceal_line(roles, choices, night=1, earlier_deaths=()):
    illusionist = next(player for player, role in roles.items() if role == "illusionist")
    records, lines, _ = _after_night(choices, roles, night, illusionist, earlier_deaths=earlier_deaths)
    conceal_index = next(i for i, record in enumerate(records) if record.action == "conceal")
    return records[conceal_index], lines[conceal_index]


def test_a_conceal_with_no_body_after_a_healer_save():
    roles, player_of = _game("serial_killer", "speculator")
    trailseer = player_of["trailseer"]
    record, line = _conceal_line(roles, [NightChoice(player_of["chanteuse"], "chanteuse", "kill", trailseer),
                                         NightChoice(player_of["illusionist"], "illusionist", "conceal", None),
                                         NightChoice(player_of["healer"], "healer", "protect", trailseer)])
    assert record.result == "no_body"
    assert format_night_actions([record], implications=[line]) == (
        "Night 1: The pack's victim did not die, so no body was concealed. "
        f"{trailseer}, the pack's target, survived: the Healer saved them, so your conceal was not spent.")
    assert line.row == "A45"


def test_a_conceal_with_no_body_after_a_reanimated_healer_save():
    roles, player_of = _game("necromancer", "speculator")
    trailseer = player_of["trailseer"]
    _, line = _conceal_line(roles, [NightChoice(player_of["chanteuse"], "chanteuse", "kill", trailseer),
                                    NightChoice(player_of["illusionist"], "illusionist", "conceal", None),
                                    NightChoice(player_of["necromancer"], "necromancer", "protect", trailseer,
                                                via=player_of["healer"])],
                            night=2, earlier_deaths=[_lynched(player_of["healer"], "healer", 2)])
    assert line.text == (f"{trailseer}, the pack's target, survived: the Necromancer saved them through the dead "
                         "Healer's body, so your conceal was not spent.")


def test_a_conceal_with_no_body_after_a_self_bet():
    roles, player_of = _game("serial_killer", "fortune_teller")
    fortune_teller = player_of["fortune_teller"]
    _, line = _conceal_line(roles, [NightChoice(player_of["chanteuse"], "chanteuse", "kill", fortune_teller),
                                    NightChoice(player_of["illusionist"], "illusionist", "conceal", None),
                                    NightChoice(fortune_teller, "fortune_teller", "bet", fortune_teller)])
    assert line.text == (f"{fortune_teller}, the pack's target, survived on their own self-bet, so {fortune_teller} "
                         "is the Fortune Teller, and your conceal was not spent.")


def test_a_conceal_with_no_body_and_nothing_announced_means_the_target_was_immune():
    roles, player_of = _game("serial_killer", "speculator")
    killer = player_of["serial_killer"]
    _, line = _conceal_line(roles, [NightChoice(player_of["chanteuse"], "chanteuse", "kill", killer),
                                    NightChoice(player_of["illusionist"], "illusionist", "conceal", None)])
    assert line.text == (f"{killer}, the pack's target, survived and no save was announced, so {killer} could not "
                         f"be killed: {killer} is the Serial Killer. Your conceal was not spent.")


def test_on_night_one_in_a_necromancer_cast_the_silent_survivor_is_the_necromancer():
    roles, player_of = _game("necromancer", "fortune_teller")
    necromancer = player_of["necromancer"]
    _, line = _conceal_line(roles, [NightChoice(player_of["chanteuse"], "chanteuse", "kill", necromancer),
                                    NightChoice(player_of["illusionist"], "illusionist", "conceal", None)])
    assert line.text.endswith(f"{necromancer} is the Necromancer. Your conceal was not spent.")


def test_a_conceal_with_no_body_and_no_morning_on_the_payload_says_nothing_more():
    roles, player_of = _game("serial_killer", "speculator")
    choices = [NightChoice(player_of["chanteuse"], "chanteuse", "kill", player_of["trailseer"]),
               NightChoice(player_of["illusionist"], "illusionist", "conceal", None),
               NightChoice(player_of["healer"], "healer", "protect", player_of["trailseer"])]
    lines = _without_the_morning(choices, roles, 1, player_of["illusionist"])
    assert lines[1] is None


# --- the morning is read only for its own night ------------------------------------------------------

def test_a_morning_from_another_night_is_never_read_as_this_ones():
    """Night 1's morning (the serial killer's stab) put on the payload of a seat whose record is
    from night 2: the night-2 watch must not use it."""
    roles, player_of = _game("serial_killer", "speculator")
    trailseer, killer, sentinel = player_of["trailseer"], player_of["serial_killer"], player_of["sentinel"]
    night_one = [NightChoice(killer, "serial_killer", "kill", trailseer)]
    morning_one = resolve_through_the_node(night_one, roles, 1, list(roles))["night_announcements"]
    night_two = [NightChoice(player_of["investigator"], "investigator", "investigate", trailseer),
                 NightChoice(sentinel, "sentinel", "watch", trailseer)]
    records = night_action_records(night_two, resolve_night(night_two, roles, 2), roles)
    view = _seat_view(sentinel, roles, records, [], morning_one)
    assert own_result_lines(view) == own_result_lines(replace(view, announcements=[]))
