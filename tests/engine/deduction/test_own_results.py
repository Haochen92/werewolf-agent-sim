"""Level 1 of the deduction engine: what a seat's own night records imply
(Agents/deduction/own_results/; rows in evidence/reasoning_failures/deduction_catalogue.md, Table A).

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
from Agents.schemas.roles import cast_role_counts
from Agents.turn import pipeline
from tests.factories.random_nights import BASE_ROLES, CASTS, fact_holds, random_night


def _game(killer: str, neutral: str) -> tuple[dict[str, str], dict[str, str]]:
    """A cast in a fixed seat order: the roles map, and each role's player."""
    order = BASE_ROLES + [killer, neutral]
    roles = {f"player_{seat + 1}": role for seat, role in enumerate(order)}
    player_of = {role: player for player, role in roles.items()}
    return roles, player_of


def _seat_view(receiver, roles, records, dead_roster) -> SeatView:
    return SeatView(
        player_id=receiver,
        role=roles[receiver],
        cast_role_counts=cast_role_counts(roles),
        dead_roster=list(dead_roster),
        night_records=own_night_actions(records, receiver, roles[receiver]),
    )


def _after_night(choices, roles, night, receiver, earlier_deaths=(), body_conceals=0, later_deaths=()):
    """Resolve one night and return the receiver's records, its lines and the outcome. The roster
    holds the earlier deaths, this night's, and any later ones the seat has since heard of."""
    outcome = resolve_night(choices, roles, night, body_conceals)
    records = night_action_records(choices, outcome, roles)
    this_nights_deaths = [
        DeathRecord(player=player, role="" if player in outcome.concealed else roles[player],
                    day=night, phase="night", concealed=player in outcome.concealed)
        for player in outcome.deaths
    ]
    roster = list(earlier_deaths) + this_nights_deaths + list(later_deaths)
    view = _seat_view(receiver, roles, records, roster)
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
        "Night 1 (last night): You were roleblocked: your action was not carried out. Only the "
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
        "Night 2 (last night): You were roleblocked: your action was not carried out. The Chanteuse was "
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


def test_in_sk_ft_an_immune_target_is_either_the_killer_or_a_self_betting_fortune_teller():
    roles, player_of = _game("serial_killer", "fortune_teller")
    fortune_teller = player_of["fortune_teller"]
    choices = [NightChoice(player_of["vigilante"], "vigilante", "kill", fortune_teller),
               NightChoice(fortune_teller, "fortune_teller", "bet", fortune_teller)]
    _, lines, _ = _after_night(choices, roles, 2, player_of["vigilante"])
    line = _the_one_line(lines)
    assert (line.row, line.grade) == ("A14", "possible")
    assert line.text == (f"{fortune_teller} could not be killed that night: {fortune_teller} is the Serial "
                         f"Killer, or the Fortune Teller betting on itself that night.")


def test_once_the_serial_killer_is_revealed_elsewhere_the_immune_target_is_the_fortune_teller():
    roles, player_of = _game("serial_killer", "fortune_teller")
    fortune_teller = player_of["fortune_teller"]
    killer_lynched = DeathRecord(player=player_of["serial_killer"], role="serial_killer", day=2, phase="day")
    choices = [NightChoice(player_of["vigilante"], "vigilante", "kill", fortune_teller),
               NightChoice(fortune_teller, "fortune_teller", "bet", fortune_teller)]
    _, lines, _ = _after_night(choices, roles, 2, player_of["vigilante"], earlier_deaths=[killer_lynched])
    assert _the_one_line(lines).text == (
        f"Only the Fortune Teller betting on itself could survive that attack, so {fortune_teller} is the "
        f"Fortune Teller and bet on itself that night.")


def test_the_immune_target_lynched_later_is_still_named_by_the_line():
    """A role revealed on the target itself does not rule the target out, only one revealed on
    someone else does."""
    roles, player_of = _game("serial_killer", "speculator")
    killer = player_of["serial_killer"]
    lynched_next_day = [DeathRecord(player=killer, role="serial_killer", day=2, phase="day")]
    choices = [NightChoice(player_of["vigilante"], "vigilante", "kill", killer)]
    _, lines, _ = _after_night(choices, roles, 1, player_of["vigilante"], later_deaths=lynched_next_day)
    assert _the_one_line(lines).text.endswith(f"so {killer} is the Serial Killer.")


def test_the_serial_killer_hitting_an_immune_player_names_the_self_betting_fortune_teller():
    roles, player_of = _game("serial_killer", "fortune_teller")
    fortune_teller = player_of["fortune_teller"]
    choices = [NightChoice(player_of["serial_killer"], "serial_killer", "kill", fortune_teller),
               NightChoice(fortune_teller, "fortune_teller", "bet", fortune_teller)]
    _, lines, _ = _after_night(choices, roles, 2, player_of["serial_killer"])
    assert "is the Fortune Teller and bet on itself" in _the_one_line(lines).text


def test_on_night_one_in_ne_sp_the_immune_target_is_the_necromancer():
    roles, player_of = _game("necromancer", "speculator")
    necromancer = player_of["necromancer"]
    choices = [NightChoice(player_of["vigilante"], "vigilante", "kill", necromancer)]
    _, lines, _ = _after_night(choices, roles, 1, player_of["vigilante"])
    assert _the_one_line(lines).text == (f"Only the Necromancer (it cannot be killed on night 1) could "
                                         f"survive that attack, so {necromancer} is the Necromancer.")


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
    assert line.text == ("A reanimated healer is the Necromancer acting through the dead Healer's body: the "
                         f"Necromancer protected {target} that night.")


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


def test_no_attack_in_ne_sp_after_night_one_is_certain():
    roles, player_of = _game("necromancer", "speculator")
    target = player_of["sentinel"]
    choices = [NightChoice(player_of["healer"], "healer", "protect", target)]
    _, lines, _ = _after_night(choices, roles, 2, player_of["healer"])
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
        "player_id", "role", "cast_role_counts", "dead_roster", "night_records"}


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


@pytest.mark.parametrize("mode,shown", [("off", False), ("record", True), ("full", True), (None, True)])
def test_the_games_mode_decides_whether_an_ai_seat_gets_the_lines(mode, shown):
    payload = _blocked_healer_payload(deduction_mode=mode) if mode else _blocked_healer_payload()
    assert (prompt_inputs._own_result_lines(payload) is not None) == shown


def test_the_games_mode_reaches_the_turn_payload_from_the_run_config():
    config = build_runnable_config(RunConfig(deduction_mode="off"))
    assert pipeline._with_deduction_mode({}, config) == {"deduction_mode": "off"}
    assert pipeline._with_deduction_mode({}, {}) == {}  # no config: the payload keeps the default


def test_a_human_seat_gets_no_lines_whatever_the_mode():
    payload = _blocked_healer_payload(human_player=True, deduction_mode="full")
    assert prompt_inputs._own_result_lines(payload) is None


# --- soundness over random legal nights -------------------------------------------------------

ROWS_BUILT = {"A1", "A2", "A4", "A6", "A7", "A8", "A11", "A12", "A13", "A14"}


def test_every_fact_a_line_states_holds_in_the_real_game():
    rng = random.Random(20261016)
    times_each_row_fired: dict[str, int] = {}
    for _ in range(20000):
        game = random_night(rng)
        for receiver in game.receivers():
            view = _seat_view(receiver, game.roles, game.records, game.dead_roster)
            for line in own_result_lines(view):
                if line is None:
                    continue
                times_each_row_fired[line.row] = times_each_row_fired.get(line.row, 0) + 1
                for fact in line.facts:
                    assert fact_holds(fact, game), (line, fact, game)
    assert set(times_each_row_fired) >= ROWS_BUILT, times_each_row_fired


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
            view = _seat_view(receiver, game.roles, game.records, game.dead_roster)
            for line in own_result_lines(view):
                if line is not None:
                    for role in not_dealt:
                        assert titles[role] not in line.text, line.text
