"""Level 1 of the deduction engine: what a seat's own night records imply
(Agents/deduction/own_results/; rows in evidence/gameplay/deduction/deduction_catalogue.md, Table A).

Every night here runs through the real engine (resolve_night, night_action_records). Three kinds of
test, per the catalogue's build bar:
- examples and counterexamples per row and cast, with the exact line the seat reads;
- the leak boundary: the engine reads only the seat's own payload fields, and a human seat or a
  game set to "off" gets no lines;
- soundness over thousands of random legal nights: every fact a line states must hold in the real
  game (tests/factories/random_nights.py).
"""

from __future__ import annotations

import random

import pytest

from Agents.config import RunConfig, build_runnable_config
from Agents.deduction import own_result_lines, seat_view_from_payload
from Agents.prompts import prompt_inputs
from Agents.prompts.prompt_formatters import format_night_actions
from Agents.rules.night import resolve_night
from Agents.rules.night_record import night_action_records, own_night_actions
from Agents.schemas.deduction import SeatView
from Agents.schemas.game_events import DeathRecord
from Agents.schemas.night import NightChoice
from Agents.schemas.roles import ROLE_SPECS, cast_role_counts
from Agents.turn import pipeline
from tests.factories.random_nights import BASE_ROLES, CASTS, fact_holds, random_night, resolve_through_the_node


def _game(killer: str, neutral: str) -> tuple[dict[str, str], dict[str, str]]:
    """A cast in a fixed seat order: the roles map, and each role's player."""
    order = BASE_ROLES + [killer, neutral]
    roles = {f"player_{seat + 1}": role for seat, role in enumerate(order)}
    player_of = {role: player for player, role in roles.items()}
    return roles, player_of


def _pack_roles(receiver, roles, dead_roster) -> dict[str, str]:
    """What a wolf's payload carries: its living pack and their roles (empty for anyone else)."""
    if not ROLE_SPECS[roles[receiver]].pack:
        return {}
    dead = {death.player for death in dead_roster}
    return {player: role for player, role in roles.items() if ROLE_SPECS[role].pack and player not in dead}


def _seat_view(receiver, roles, records, dead_roster, announcements=()) -> SeatView:
    return SeatView(
        player_id=receiver,
        role=roles[receiver],
        cast_role_counts=cast_role_counts(roles),
        dead_roster=list(dead_roster),
        night_records=own_night_actions(records, receiver, roles[receiver]),
        pack_roles=_pack_roles(receiver, roles, dead_roster),
        announcements=list(announcements),
    )


def _after_night(choices, roles, night, receiver, earlier_deaths=(), body_conceals=0, later_deaths=()):
    """Resolve one night and return the receiver's records, its lines and the outcome. The roster
    holds the earlier deaths, this night's, and any later ones the seat has since heard of; the
    morning is the one the resolution node committed."""
    outcome = resolve_night(choices, roles, night, body_conceals)
    records = night_action_records(choices, outcome, roles)
    this_nights_deaths = [
        DeathRecord(player=player, role="" if player in outcome.concealed else roles[player],
                    day=night, phase="night", concealed=player in outcome.concealed)
        for player in outcome.deaths
    ]
    roster = list(earlier_deaths) + this_nights_deaths + list(later_deaths)
    dead_before = {death.player for death in earlier_deaths}
    alive = [player for player in roles if player not in dead_before]
    morning = resolve_through_the_node(choices, roles, night, alive, body_conceals)["night_announcements"]
    view = _seat_view(receiver, roles, records, roster, morning)
    return view.night_records, own_result_lines(view), outcome


def _the_one_line(lines):
    found = [line for line in lines if line is not None]
    assert len(found) == 1, found
    return found[0]


# --- A6, A7, A8: the roleblock ---------------------------------------------------------------

def test_a_block_by_the_living_chanteuse_says_she_came_to_you_and_replaces_the_record():
    roles, player_of = _game("serial_killer", "speculator")
    choices = [NightChoice(player_of["chanteuse"], "chanteuse", "block", player_of["healer"]),
               NightChoice(player_of["healer"], "healer", "protect", player_of["investigator"])]
    records, lines, _ = _after_night(choices, roles, 1, player_of["healer"])
    assert format_night_actions(records, current_day=2, implications=lines) == (
        f"Night 1 (last night): You were roleblocked: your protection of {player_of['investigator']} did not "
        "happen. Only the "
        "Chanteuse could roleblock that night, and a block is a visit, so the Chanteuse, a wolf, came "
        "to you that night."
    )
    assert _the_one_line(lines).row == "A6"


def test_a_chanteuse_revealed_dead_this_morning_still_blocked_last_night():
    roles, player_of = _game("serial_killer", "speculator")
    choices = [NightChoice(player_of["chanteuse"], "chanteuse", "block", player_of["healer"]),
               NightChoice(player_of["healer"], "healer", "protect", player_of["investigator"]),
               NightChoice(player_of["vigilante"], "vigilante", "kill", player_of["chanteuse"])]
    _, lines, outcome = _after_night(choices, roles, 2, player_of["healer"])
    assert player_of["chanteuse"] in outcome.deaths
    assert _the_one_line(lines).row == "A6"


def test_a_block_after_the_chanteuse_was_lynched_is_the_necromancer_through_her_body():
    roles, player_of = _game("necromancer", "speculator")
    lynched = DeathRecord(player=player_of["chanteuse"], role="chanteuse", day=2, phase="day")
    choices = [NightChoice(player_of["necromancer"], "necromancer", "block", player_of["healer"],
                           via=player_of["chanteuse"]),
               NightChoice(player_of["healer"], "healer", "protect", player_of["investigator"])]
    records, lines, _ = _after_night(choices, roles, 2, player_of["healer"], earlier_deaths=[lynched])
    assert format_night_actions(records, current_day=3, implications=lines) == (
        f"Night 2 (last night): You were roleblocked: your protection of {player_of['investigator']} did not "
        "happen. The Chanteuse was "
        "already dead, so the Necromancer blocked you through her body; a watcher at your door would "
        "have seen the Chanteuse's name, not the Necromancer's."
    )


def test_the_lone_illusionist_carrier_blocked_through_the_chanteuse_reads_the_pack_line():
    roles, player_of = _game("necromancer", "speculator")
    lynched = DeathRecord(player=player_of["chanteuse"], role="chanteuse", day=2, phase="day")
    choices = [NightChoice(player_of["illusionist"], "illusionist", "kill", player_of["healer"]),
               NightChoice(player_of["necromancer"], "necromancer", "block", player_of["illusionist"],
                           via=player_of["chanteuse"])]
    _, lines, _ = _after_night(choices, roles, 2, player_of["illusionist"], earlier_deaths=[lynched])
    line = _the_one_line(lines)
    assert line.row == "A8"
    assert line.text.startswith("The pack's carrier was roleblocked: the kill did not happen.")


# --- A13–A19: an attack that met immunity -----------------------------------------------------

def test_the_pack_hitting_an_immune_player_in_sk_sp_names_the_serial_killer():
    roles, player_of = _game("serial_killer", "speculator")
    killer = player_of["serial_killer"]
    choices = [NightChoice(player_of["chanteuse"], "chanteuse", "kill", killer)]
    records, lines, _ = _after_night(choices, roles, 1, player_of["illusionist"])
    assert format_night_actions(records, implications=lines) == (
        f"Night 1: your pack attacked {killer}. {killer} was unharmed: immune to night kills tonight. The "
        f"public was told nothing about this attack. Only the Serial Killer could survive that attack, so "
        f"{killer} is the Serial Killer."
    )


def test_in_sk_ft_a_silent_immune_target_is_the_serial_killer():
    """R10: a self-bet that stops an attack is announced, so a silent one is the serial killer."""
    roles, player_of = _game("serial_killer", "fortune_teller")
    killer = player_of["serial_killer"]
    choices = [NightChoice(player_of["vigilante"], "vigilante", "kill", killer),
               NightChoice(player_of["fortune_teller"], "fortune_teller", "bet", player_of["fortune_teller"])]
    _, lines, _ = _after_night(choices, roles, 2, player_of["vigilante"])
    line = _the_one_line(lines)
    assert (line.row, line.grade) == ("A13", "certain")
    assert line.text == f"Only the Serial Killer could survive that attack, so {killer} is the Serial Killer."


def test_the_immune_target_lynched_later_is_still_named_by_the_line():
    """A role revealed on the target itself does not rule the target out, only one revealed on
    someone else does."""
    roles, player_of = _game("serial_killer", "speculator")
    killer = player_of["serial_killer"]
    lynched_next_day = [DeathRecord(player=killer, role="serial_killer", day=2, phase="day")]
    choices = [NightChoice(player_of["vigilante"], "vigilante", "kill", killer)]
    _, lines, _ = _after_night(choices, roles, 1, player_of["vigilante"], later_deaths=lynched_next_day)
    assert _the_one_line(lines).text.endswith(f"so {killer} is the Serial Killer.")


def test_on_night_one_in_ne_ft_a_silent_immune_target_is_the_necromancer():
    roles, player_of = _game("necromancer", "fortune_teller")
    necromancer = player_of["necromancer"]
    choices = [NightChoice(player_of["vigilante"], "vigilante", "kill", necromancer)]
    _, lines, _ = _after_night(choices, roles, 1, player_of["vigilante"])
    assert _the_one_line(lines).text == (f"Only the Necromancer (it cannot be killed on nights 1 and 2) could "
                                         f"survive that attack, so {necromancer} is the Necromancer.")


def test_on_night_one_in_ne_sp_the_immune_target_is_the_necromancer():
    roles, player_of = _game("necromancer", "speculator")
    necromancer = player_of["necromancer"]
    choices = [NightChoice(player_of["vigilante"], "vigilante", "kill", necromancer)]
    _, lines, _ = _after_night(choices, roles, 1, player_of["vigilante"])
    assert _the_one_line(lines).text == (f"Only the Necromancer (it cannot be killed on nights 1 and 2) could "
                                         f"survive that attack, so {necromancer} is the Necromancer.")


# --- A53, A54: an attack the fortune teller's self-bet stopped ---------------------------------

def test_a_shot_stopped_by_a_self_bet_names_the_fortune_teller():
    roles, player_of = _game("serial_killer", "fortune_teller")
    fortune_teller = player_of["fortune_teller"]
    choices = [NightChoice(player_of["vigilante"], "vigilante", "kill", fortune_teller),
               NightChoice(fortune_teller, "fortune_teller", "bet", fortune_teller)]
    records, lines, _ = _after_night(choices, roles, 2, player_of["vigilante"])
    assert format_night_actions(records, implications=lines) == (
        f"Night 2: you shot {fortune_teller}. {fortune_teller} survived: the fortune teller's self-bet saved "
        f"them. Only the Fortune Teller's own bet saves a player like this, so {fortune_teller} is the "
        f"Fortune Teller."
    )
    line = _the_one_line(lines)
    assert (line.row, line.grade) == ("A53", "certain")


def test_the_serial_killer_hitting_a_self_betting_fortune_teller_names_it():
    roles, player_of = _game("serial_killer", "fortune_teller")
    fortune_teller = player_of["fortune_teller"]
    choices = [NightChoice(player_of["serial_killer"], "serial_killer", "kill", fortune_teller),
               NightChoice(fortune_teller, "fortune_teller", "bet", fortune_teller)]
    _, lines, _ = _after_night(choices, roles, 2, player_of["serial_killer"])
    line = _the_one_line(lines)
    assert line.row == "A53"
    assert line.text == (f"Only the Fortune Teller's own bet saves a player like this, so {fortune_teller} "
                         f"is the Fortune Teller.")


def test_a_healer_whose_target_survived_on_its_own_self_bet_learns_it_is_the_fortune_teller():
    roles, player_of = _game("necromancer", "fortune_teller")
    fortune_teller = player_of["fortune_teller"]
    choices = [NightChoice(player_of["chanteuse"], "chanteuse", "kill", fortune_teller),
               NightChoice(fortune_teller, "fortune_teller", "bet", fortune_teller),
               NightChoice(player_of["healer"], "healer", "protect", fortune_teller)]
    records, lines, _ = _after_night(choices, roles, 2, player_of["healer"])
    assert format_night_actions(records, implications=lines) == (
        f"Night 2: you protected {fortune_teller}. {fortune_teller} was attacked by the wolves and survived: "
        f"the fortune teller's self-bet saved them, not your protection. Only the Fortune Teller's own bet "
        f"saves a player like this, so {fortune_teller} is the Fortune Teller."
    )
    line = _the_one_line(lines)
    assert (line.row, line.grade) == ("A54", "certain")


def test_a_self_bet_with_no_attack_leaves_the_healer_the_plain_no_attack_line():
    """No attack on the self-betting fortune teller: nothing announced, and its immunity is not
    among the explanations (in NE+FT after night 2 nobody is silently immune)."""
    roles, player_of = _game("necromancer", "fortune_teller")
    fortune_teller = player_of["fortune_teller"]
    choices = [NightChoice(fortune_teller, "fortune_teller", "bet", fortune_teller),
               NightChoice(player_of["healer"], "healer", "protect", fortune_teller)]
    _, lines, _ = _after_night(choices, roles, 3, player_of["healer"])
    line = _the_one_line(lines)
    assert (line.row, line.text) == ("A4", f"No attack reached {fortune_teller} that night.")


# --- A1, A11, A12: saves ------------------------------------------------------------------------

def test_the_healer_learns_its_saved_target_is_neither_the_killer_nor_a_wolf():
    roles, player_of = _game("serial_killer", "speculator")
    target = player_of["investigator"]
    choices = [NightChoice(player_of["chanteuse"], "chanteuse", "kill", target),
               NightChoice(player_of["healer"], "healer", "protect", target)]
    _, lines, _ = _after_night(choices, roles, 1, player_of["healer"])
    assert _the_one_line(lines).text == (f"{target} can be killed at night, so {target} is not the Serial "
                                         f"Killer. The wolves attacked {target}, so {target} is not a wolf.")


def test_saved_from_the_wolves_and_a_sigil_is_the_vigilante():
    roles, player_of = _game("necromancer", "speculator")
    vigilante = player_of["vigilante"]
    choices = [NightChoice(vigilante, "vigilante", "kill", player_of["sentinel"]),
               NightChoice(player_of["chanteuse"], "chanteuse", "kill", vigilante),
               NightChoice(player_of["sigilist"], "sigilist", "sigil", vigilante),
               NightChoice(player_of["healer"], "healer", "protect", vigilante)]
    _, lines, _ = _after_night(choices, roles, 2, player_of["healer"])
    assert _the_one_line(lines).text.endswith(
        f"so {vigilante} attacked someone in their own name that night and is not a wolf: {vigilante} is the "
        f"Vigilante.")


def test_a_save_by_a_reanimated_healer_is_explained_to_the_attacker():
    roles, player_of = _game("necromancer", "speculator")
    lynched = DeathRecord(player=player_of["healer"], role="healer", day=2, phase="day")
    target = player_of["sentinel"]
    choices = [NightChoice(player_of["chanteuse"], "chanteuse", "kill", target),
               NightChoice(player_of["necromancer"], "necromancer", "protect", target, via=player_of["healer"])]
    _, lines, _ = _after_night(choices, roles, 2, player_of["illusionist"], earlier_deaths=[lynched])
    line = _the_one_line(lines)
    assert line.row == "A12"
    # Night 2: the Necromancer acts through a body and is immune, so the save also rules the target out.
    assert line.text == ("A reanimated healer is the Necromancer acting through the dead Healer's body: the "
                         f"Necromancer protected {target} that night. {target} can be killed at night, so "
                         f"{target} is not the Necromancer.")


def test_the_serial_killer_is_not_told_its_saved_target_is_not_itself():
    roles, player_of = _game("serial_killer", "speculator")
    choices = [NightChoice(player_of["serial_killer"], "serial_killer", "kill", player_of["sentinel"]),
               NightChoice(player_of["healer"], "healer", "protect", player_of["sentinel"])]
    _, lines, _ = _after_night(choices, roles, 1, player_of["serial_killer"])
    assert lines == [None]


# --- A2–A5: no attack announced on the protected player ----------------------------------------

def test_no_attack_in_sk_sp_keeps_the_immune_branch():
    roles, player_of = _game("serial_killer", "speculator")
    target = player_of["sentinel"]
    choices = [NightChoice(player_of["healer"], "healer", "protect", target)]
    _, lines, _ = _after_night(choices, roles, 1, player_of["healer"])
    line = _the_one_line(lines)
    assert line.grade == "possible"
    assert line.text == (f"Either no attack reached {target} that night, or {target} could not be killed: "
                         f"{target} would then be the Serial Killer.")


def test_no_attack_in_ne_sp_after_night_two_is_certain():
    roles, player_of = _game("necromancer", "speculator")
    target = player_of["sentinel"]
    choices = [NightChoice(player_of["healer"], "healer", "protect", target)]
    _, lines, _ = _after_night(choices, roles, 3, player_of["healer"])
    assert _the_one_line(lines).text == f"No attack reached {target} that night."


# --- the leak boundary and the mode ---------------------------------------------------------------

def _blocked_healer_payload(**extra) -> dict:
    roles, player_of = _game("serial_killer", "speculator")
    choices = [NightChoice(player_of["chanteuse"], "chanteuse", "block", player_of["healer"]),
               NightChoice(player_of["healer"], "healer", "protect", player_of["investigator"])]
    records, _, _ = _after_night(choices, roles, 1, player_of["healer"])
    return {"night_actions": records, "player_id": player_of["healer"], "player_role": "healer",
            "cast_role_counts": cast_role_counts(roles), "dead_roster": [], **extra}


def test_the_seat_view_reads_only_the_seats_own_payload_fields():
    """Anything else on a payload (here, planted hidden state) cannot reach the engine."""
    plain = seat_view_from_payload(_blocked_healer_payload())
    with_hidden_state = seat_view_from_payload(_blocked_healer_payload(
        roles={"player_1": "investigator"}, night_choices=["secret"], surviving_wolves=["player_7"]))
    assert plain == with_hidden_state
    assert set(SeatView.__dataclass_fields__) == {
        "player_id", "role", "cast_role_counts", "dead_roster", "night_records", "pack_roles", "announcements",
        "wills", "living", "claims"}


def test_the_seat_view_reads_stored_dicts_like_live_models():
    payload = _blocked_healer_payload()
    stored = {**payload, "night_actions": [r.model_dump() for r in payload["night_actions"]]}
    assert seat_view_from_payload(stored) == seat_view_from_payload(payload)


def test_hidden_roles_that_do_not_change_the_seats_view_do_not_change_its_lines():
    """Swap two seats the receiver knows nothing about: same records, same roster, same lines."""
    roles, player_of = _game("serial_killer", "speculator")
    choices = [NightChoice(player_of["chanteuse"], "chanteuse", "kill", player_of["serial_killer"])]
    _, before, _ = _after_night(choices, roles, 1, player_of["illusionist"])
    swapped = dict(roles)
    swapped[player_of["sentinel"]], swapped[player_of["trailseer"]] = "trailseer", "sentinel"
    _, after, _ = _after_night(choices, swapped, 1, player_of["illusionist"])
    assert before == after


def test_a_watchers_lines_do_not_depend_on_which_role_made_the_visit():
    """Two hidden states the sentinel cannot tell apart: player_6 visited as the Healer, or as the
    Investigator (roles and actions swapped with player_1). Same record, same roster, same lines."""
    roles, player_of = _game("necromancer", "speculator")
    sentinel, sigilist = player_of["sentinel"], player_of["sigilist"]
    choices = [NightChoice("player_6", "healer", "protect", sigilist),
               NightChoice("player_1", "investigator", "investigate", player_of["trailseer"]),
               NightChoice(sentinel, "sentinel", "watch", sigilist)]
    records, before, _ = _after_night(choices, roles, 2, sentinel)
    swapped = {**roles, "player_1": "healer", "player_6": "investigator"}
    swapped_choices = [NightChoice("player_6", "investigator", "investigate", sigilist),
                       NightChoice("player_1", "healer", "protect", player_of["trailseer"]),
                       NightChoice(sentinel, "sentinel", "watch", sigilist)]
    swapped_records, after, _ = _after_night(swapped_choices, swapped, 2, sentinel)
    assert records == swapped_records
    assert before == after and before[0] is not None


def test_an_investigators_lines_do_not_depend_on_which_wolf_it_checked():
    roles, player_of = _game("serial_killer", "speculator")
    investigator = player_of["investigator"]
    choices = [NightChoice(investigator, "investigator", "investigate", "player_7")]
    _, before, _ = _after_night(choices, roles, 1, investigator)
    swapped = {**roles, "player_7": "illusionist", "player_8": "chanteuse"}
    _, after, _ = _after_night(choices, swapped, 1, investigator)
    assert before == after and before[0] is not None


def test_planted_hidden_state_on_the_payload_never_changes_a_line():
    """Over random legal nights, every seat's lines from its own payload equal its lines from the
    same payload with the whole hidden night planted beside it (roles, choices, every record)."""
    rng = random.Random(20261017)
    for _ in range(2000):
        game = random_night(rng)
        for receiver in game.receivers():
            view = _seat_view(receiver, game.roles, game.records, game.dead_roster, [game.announcement])
            payload = {"player_id": receiver, "player_role": view.role,
                       "cast_role_counts": view.cast_role_counts, "dead_roster": view.dead_roster,
                       "night_actions": view.night_records, "pack_roles": view.pack_roles,
                       "night_announcements": view.announcements}
            planted = {**payload, "roles": game.roles, "night_choices": game.choices,
                       "all_night_actions": game.records, "outcome": game.outcome}
            assert own_result_lines(seat_view_from_payload(planted)) == own_result_lines(view)
            assert own_result_lines(seat_view_from_payload(payload)) == own_result_lines(view)


@pytest.mark.parametrize("mode,shown", [("off", False), ("record", True), ("public", True), ("full", True), (None, True)])
def test_the_games_mode_decides_whether_an_ai_seat_gets_the_lines(mode, shown):
    payload = _blocked_healer_payload(deduction_mode=mode) if mode else _blocked_healer_payload()
    assert (prompt_inputs._own_result_lines(payload) is not None) == shown


def test_the_games_mode_reaches_the_turn_payload_from_the_run_config():
    config = build_runnable_config(RunConfig(deduction_mode="off"))
    assert pipeline._with_deduction_mode({}, config) == {"deduction_mode": "off"}
    assert pipeline._with_deduction_mode({}, {}) == {}  # no config: the payload keeps the default


def test_a_sides_own_level_overrides_the_games_mode():
    """Difficulty (owner, 2026-10-18): e.g. the town at level 3, the wolves at level 1."""
    config = build_runnable_config(RunConfig(deduction_by_side={"wolves": "record", "neutral": "public"}))
    assert pipeline._with_deduction_mode({"player_role": "chanteuse"}, config)["deduction_mode"] == "record"
    assert pipeline._with_deduction_mode({"player_role": "speculator"}, config)["deduction_mode"] == "public"
    assert pipeline._with_deduction_mode({"player_role": "healer"}, config)["deduction_mode"] == "full"
    # Use limits the engine was not verified for still turn it off, whatever the side's level.
    other = build_runnable_config(RunConfig(game={"sigils": 3}, deduction_by_side={"wolves": "full"}))
    assert pipeline._with_deduction_mode({"player_role": "chanteuse"}, other)["deduction_mode"] == "off"


def test_a_human_seat_gets_no_lines_whatever_the_mode():
    payload = _blocked_healer_payload(human_player=True, deduction_mode="full")
    assert prompt_inputs._own_result_lines(payload) is None


# --- soundness over random legal nights -------------------------------------------------------

ROWS_BUILT = {"A1", "A2", "A4", "A6", "A7", "A8", "A11", "A12", "A13", "A53", "A54",
              "A21", "A22", "A23", "A24", "A25", "A26", "A27", "A32", "A33", "A34", "A35",
              "A37", "A38", "A39", "A40", "A41", "A42", "A43", "A49", "A50",
              "A28", "A29", "A30", "A31", "A36", "A45", "A56"}
"""The rows the random nights must reach. A14's "either … or" line is retired (R10): every cast now
leaves one silent immune role at most."""
SENTENCES_REACHED = {
    "A22 (c)": "No attack through a dead player's body was announced that night",
    "A28, A29 one each": "one each; your watch does not show which is which",
    "A30 the Illusionist carried": "so the Illusionist made the kill itself",
}
"""Conditions inside a row the random nights must also reach, by a phrase of their sentence. A22 (b)
is too rare in random play to pin here (about once in 20,000 nights): its constructed nights are in
test_morning_results.py."""


def test_every_fact_a_line_states_holds_in_the_real_game():
    rng = random.Random(20261016)
    times_each_row_fired: dict[str, int] = {}
    sentences_reached: set[str] = set()
    for _ in range(20000):
        game = random_night(rng)
        for receiver in game.receivers():
            view = _seat_view(receiver, game.roles, game.records, game.dead_roster, [game.announcement])
            for line in own_result_lines(view):
                if line is None:
                    continue
                for row in line.row.split("+"):
                    times_each_row_fired[row] = times_each_row_fired.get(row, 0) + 1
                sentences_reached |= {name for name, phrase in SENTENCES_REACHED.items() if phrase in line.text}
                for fact in line.facts:
                    assert fact_holds(fact, game), (line, fact, game)
    assert set(times_each_row_fired) >= ROWS_BUILT, times_each_row_fired
    assert sentences_reached == set(SENTENCES_REACHED)


@pytest.mark.parametrize("killer,neutral", CASTS)
def test_a_line_never_names_a_role_outside_its_cast(killer, neutral):
    titles = {"serial_killer": "Serial Killer", "necromancer": "Necromancer", "fortune_teller": "Fortune Teller"}
    not_dealt = [role for role in titles if role not in (killer, neutral)]
    rng = random.Random(f"{killer}-{neutral}")
    for _ in range(4000):
        game = random_night(rng)
        if killer not in game.roles.values() or neutral not in game.roles.values():
            continue
        for receiver in game.receivers():
            view = _seat_view(receiver, game.roles, game.records, game.dead_roster, [game.announcement])
            for line in own_result_lines(view):
                if line is not None:
                    for role in not_dealt:
                        assert titles[role] not in line.text, line.text
