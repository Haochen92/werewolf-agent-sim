"""The role traits table (Agents/schemas/role_traits.py) against the real night engine.

Each trait the deduction rows read is derived here from what Agents/rules/night.py `resolve_night`
(and the action space, Agents/turn/action_space.py) actually do on a constructed night, one role at
a time, and compared with the table. A trait the engine disagrees with fails, so a new role is
declared in the table and these tests say whether the engine agrees.

The night: one seat per role of the pool, plus spare seats (a target, a second Chanteuse to block,
a second Sigilist to strike, dead bodies for the Necromancer), all acting at once as the engine
resolves them.
"""

from __future__ import annotations

import pytest

from Agents.deduction.verified import VERIFIED_ROLES
from Agents.rules.night import borrowed_kind, resolve_night, usable_bodies, visited_by, visitors_of
from Agents.schemas.game_events import DeathRecord
from Agents.schemas.night import NightChoice
from Agents.schemas.role_traits import (
    ROLE_TRAITS,
    STRUCK_BY_SIGIL,
    UNBLOCKABLE,
    roles_acting,
    roles_with,
    silently_immune,
)
from Agents.schemas.roles import BORROWED_ABILITY, NECROMANCER_IMMUNE_NIGHTS, ROLE_SPECS, roles
from Agents.turn.action_space import valid_targets_for_action

POOL = list(ROLE_TRAITS)
HOLDER = {role: f"player_{seat}" for seat, role in enumerate(POOL, start=1)}
TARGET = "player_30"  # an investigator no one else acts on
SECOND_TARGET = "player_31"  # a second investigator
BLOCKER = "player_32"  # a second Chanteuse, to block any seat
STRIKER = "player_33"  # a second Sigilist, to strike any seat
BODY = {"illusionist": "player_40", "vigilante": "player_41", "healer": "player_42",
        "investigator": "player_43", "sigilist": "player_44"}
"""Dead players the Necromancer acts through, by role."""
ROLES = {**{player: role for role, player in HOLDER.items()}, TARGET: "investigator", SECOND_TARGET: "investigator",
         BLOCKER: "chanteuse", STRIKER: "sigilist", **{player: role for role, player in BODY.items()}}


def own_action(role: str, target: str = TARGET, body: str = "investigator") -> NightChoice:
    """The role's own night action on `target`, as its turn makes it (the Necromancer through a body
    of role `body`; a wolf's skill, not the pack's kill)."""
    actor, kind = HOLDER[role], ROLE_SPECS[role].night_action
    if kind == "borrow":
        return NightChoice(actor, role, BORROWED_ABILITY[body], target, via=BODY[body])
    if kind == "pick":
        return NightChoice(actor, role, "pick", "town")
    if kind == "conceal":
        return NightChoice(actor, role, "conceal", None)
    return NightChoice(actor, role, kind, target)


def pack_kill(carrier_role: str, target: str = TARGET) -> NightChoice:
    """The pack's kill, carried by the holder of `carrier_role`."""
    return NightChoice(HOLDER[carrier_role], carrier_role, "kill", target)


def own_attack(role: str, target: str = TARGET) -> list[NightChoice]:
    """The role's attack under its own name when it has one: a wolf carries the pack's kill; a role
    whose own action is a kill makes it. Otherwise its own action (a Necromancer's kill is through
    the Illusionist's body)."""
    if ROLE_SPECS[role].pack:
        return [pack_kill(role, target)]
    return [own_action(role, target, body="illusionist")]


def test_the_table_is_the_pool_in_order():
    assert POOL == roles
    assert VERIFIED_ROLES <= set(ROLE_TRAITS)


# --- night immunity (L1) ---------------------------------------------------------------------------

def _immunity_seen(role: str, night: int, self_bet: bool) -> str:
    """What the engine does with an attack on the role's holder: "silent", "announced" or "killed"."""
    attacker = "vigilante" if role == "serial_killer" else "serial_killer"
    choices = [NightChoice(HOLDER[attacker], attacker, "kill", HOLDER[role])]
    if self_bet:
        choices.append(NightChoice(HOLDER[role], role, "bet", HOLDER[role]))
    outcome = resolve_night(choices, ROLES, night)
    if outcome.verdicts[HOLDER[role]] != "immune":
        return "killed"
    return "announced" if HOLDER[role] in outcome.self_bets else "silent"


def _immunity_expected(immunity: str, night: int, self_bet: bool) -> str:
    if immunity == "always" or (immunity == "first_nights" and night <= NECROMANCER_IMMUNE_NIGHTS):
        return "silent"
    if immunity == "self_bet" and self_bet:
        return "announced"
    return "killed"


@pytest.mark.parametrize("role", POOL)
@pytest.mark.parametrize("night", [1, 2, 3])
def test_night_immune(role, night):
    immunity = ROLE_TRAITS[role].night_immune
    assert _immunity_seen(role, night, self_bet=False) == _immunity_expected(immunity, night, False)
    if immunity == "self_bet":
        assert _immunity_seen(role, night, self_bet=True) == "announced"


@pytest.mark.parametrize("role", POOL)
def test_only_a_self_bet_role_may_target_itself(role):
    """The action space offers a seat itself as a target only for the role the self-bet trait names."""
    spec = ROLE_SPECS[role]
    payload = {"player_id": HOLDER[role], "surviving_players": list(HOLDER.values()),
               "surviving_villagers": list(HOLDER.values()), "uses_left": 1}
    may_target_itself = HOLDER[role] in valid_targets_for_action(payload, spec.target_field)
    assert may_target_itself == (ROLE_TRAITS[role].night_immune == "self_bet")


@pytest.mark.parametrize("night", [1, 2, 3])
def test_silently_immune_is_who_the_engine_spares_in_silence(night):
    spared = {role for role in POOL if _immunity_seen(role, night, self_bet=False) == "silent"}
    assert silently_immune(night) == spared


# --- blocks (L2, L3) -------------------------------------------------------------------------------

@pytest.mark.parametrize("role", POOL)
def test_blockable(role):
    """A block on the role's holder, while it makes its own action: cancelled, or without effect."""
    choices = [NightChoice(BLOCKER, "chanteuse", "block", HOLDER[role]), own_action(role)]
    outcome = resolve_night(choices, ROLES, 2)
    assert (HOLDER[role] in outcome.blocked) == ROLE_TRAITS[role].blockable
    assert (HOLDER[role] in outcome.blocks_without_effect) == (not ROLE_TRAITS[role].blockable)
    assert (role in UNBLOCKABLE) == (not ROLE_TRAITS[role].blockable)


@pytest.mark.parametrize("role", POOL)
def test_blocks(role):
    """The role's own action on a Town player cancels that player's action exactly when it blocks."""
    town = SECOND_TARGET
    choices = [own_action(role, target=town), NightChoice(town, "investigator", "investigate", TARGET)]
    outcome = resolve_night(choices, ROLES, 2)
    assert (town in outcome.blocked) == ROLE_TRAITS[role].blocks


@pytest.mark.parametrize("role", POOL)
def test_a_body_that_blocks(role):
    """Through the role's dead body, the Necromancer blocks exactly when the body is the blocker's."""
    if borrowed_kind(role) is None:
        return
    body = "player_50"
    roles_with_body = {**ROLES, body: role}
    choice = NightChoice(HOLDER["necromancer"], "necromancer", borrowed_kind(role), SECOND_TARGET, via=body)
    outcome = resolve_night([choice, NightChoice(SECOND_TARGET, "investigator", "investigate", TARGET)],
                            roles_with_body, 2)
    assert (SECOND_TARGET in outcome.blocked) == ROLE_TRAITS[role].blocks


# --- visits (L4, C10) ------------------------------------------------------------------------------

def _night_of_one_visit(role: str) -> list[NightChoice]:
    """The role's own action on TARGET; the Illusionist's conceal needs the pack's kill on it."""
    if ROLE_SPECS[role].night_action == "conceal":
        return [pack_kill("chanteuse"), own_action(role)]
    return [own_action(role)]


@pytest.mark.parametrize("role", POOL)
def test_visits(role):
    """A watch on its target and a follow of its holder: whose name each shows."""
    outcome = resolve_night(_night_of_one_visit(role), ROLES, 2)
    watched = visitors_of(outcome, TARGET)
    followed = visited_by(outcome, HOLDER[role])
    visits = ROLE_TRAITS[role].visits
    assert (HOLDER[role] in watched) == (visits == "own_name")
    assert (TARGET in followed) == (visits == "own_name")
    if visits == "under_body":
        assert BODY["investigator"] in watched
    if visits == "never":
        assert watched == [] and followed == []


@pytest.mark.parametrize("role", POOL)
def test_visits_two(role):
    """The most players one holder visits on a night: carrying the pack's kill and using its own
    skill on someone else, for a wolf."""
    if ROLE_SPECS[role].pack:
        choices = [pack_kill(role, TARGET), own_action(role, target=SECOND_TARGET)]
    else:
        choices = [own_action(role)]
    outcome = resolve_night(choices, ROLES, 2)
    assert (len(visited_by(outcome, HOLDER[role])) == 2) == ROLE_TRAITS[role].visits_two


# --- attacks in one's own name, and the sigil (L6) -------------------------------------------------

@pytest.mark.parametrize("role", POOL)
def test_attacks_in_own_name(role):
    """The role's attack (or own action) with a sigil on its holder: the sigil strikes back exactly
    when it attacked in its own name, and harms it unless it is always immune."""
    choices = [*own_attack(role), NightChoice(STRIKER, "sigilist", "sigil", HOLDER[role])]
    outcome = resolve_night(choices, ROLES, 2)
    struck = any(attack.attacker == STRIKER for attack in outcome.attacks_on.get(HOLDER[role], []))
    assert (HOLDER[role] in outcome.attackers) == ROLE_TRAITS[role].attacks_in_own_name
    assert struck == ROLE_TRAITS[role].attacks_in_own_name
    harmed = outcome.verdicts.get(HOLDER[role]) == "killed"
    assert harmed == (role in STRUCK_BY_SIGIL)


@pytest.mark.parametrize("role", POOL)
def test_attack_announced_as(role):
    """The attacker type the engine gives the attack the role makes itself (not through a body). The
    Sigilist's is its sigil's strike, on a player who attacked."""
    choices = own_attack(role)
    if ROLE_SPECS[role].night_action == "sigil":
        choices = [NightChoice(HOLDER[role], role, "sigil", HOLDER["serial_killer"]),
                   NightChoice(HOLDER["serial_killer"], "serial_killer", "kill", TARGET)]
    outcome = resolve_night(choices, ROLES, 2)
    own = {choice.actor for choice in choices if choice.via is None and choice.role == role}
    types = {attack.attacker_type for attacks in outcome.attacks_on.values() for attack in attacks
             if attack.attacker in own}
    expected = ROLE_TRAITS[role].attack_announced_as
    assert types == ({expected} if expected else set())


def test_attacks_through_a_body_are_announced_by_the_body():
    """BODY_OF_ATTACK_TYPE: the type the engine names an attack through each body by."""
    from Agents.schemas.role_traits import BODY_OF_ATTACK_TYPE

    seen = {}
    for role in POOL:
        kind = borrowed_kind(role)
        if kind not in ("kill", "sigil"):
            continue
        body = "player_50"
        target = HOLDER["serial_killer"] if kind == "sigil" else TARGET
        choices = [NightChoice(HOLDER["necromancer"], "necromancer", kind, target, via=body),
                   NightChoice(HOLDER["serial_killer"], "serial_killer", "kill", SECOND_TARGET)]
        outcome = resolve_night(choices, {**ROLES, body: role}, 2)
        for attack in outcome.attacks_on.get(target, []):
            if attack.attacker == HOLDER["necromancer"]:
                seen[attack.attacker_type] = role
    assert seen == BODY_OF_ATTACK_TYPE


# --- Suspicious (L7) -------------------------------------------------------------------------------

def _suspicious_on(necromancer_choice: NightChoice) -> set[str]:
    """The roles the engine reads Suspicious on a night every role makes its own action and the
    Necromancer makes `necromancer_choice`."""
    choices = [own_action(role, target=TARGET) for role in POOL if role != "necromancer"]
    outcome = resolve_night([*choices, necromancer_choice], ROLES, 2)
    return {role for role in POOL if HOLDER[role] in outcome.suspicious}


def test_reads_suspicious():
    necromancer = HOLDER["necromancer"]
    quiet = _suspicious_on(NightChoice(necromancer, "necromancer", "protect", TARGET, via=BODY["healer"]))
    through_illusionist = _suspicious_on(NightChoice(necromancer, "necromancer", "kill", TARGET,
                                                     via=BODY["illusionist"]))
    through_vigilante = _suspicious_on(NightChoice(necromancer, "necromancer", "kill", TARGET,
                                                   via=BODY["vigilante"]))
    assert quiet == set(roles_with(reads_suspicious="always"))
    killing = set(roles_with(reads_suspicious="always")) | set(roles_with(reads_suspicious="when_killing_through_body"))
    assert through_illusionist == killing
    assert through_vigilante == killing


# --- must act (L5) ---------------------------------------------------------------------------------

@pytest.mark.parametrize("role", POOL)
def test_must_act(role):
    """The action space offers the role a word to decline its night action exactly when it need not act."""
    spec = ROLE_SPECS[role]
    payload = {"player_id": HOLDER[role], "surviving_players": list(HOLDER.values()),
               "surviving_villagers": list(HOLDER.values()), "uses_left": 1}
    can_decline = bool(spec.no_action) and spec.no_action in valid_targets_for_action(payload, spec.target_field)
    assert ROLE_TRAITS[role].must_act == (not can_decline)


# --- bodies ----------------------------------------------------------------------------------------

@pytest.mark.parametrize("role", POOL)
def test_borrowed_verb_for_every_body_that_gives_an_action(role):
    dead = [DeathRecord(player="player_50", role=role, phase="day", day=1)]
    gives = borrowed_kind(role) is not None
    assert (ROLE_TRAITS[role].borrowed_verb is not None) == gives
    assert (usable_bodies(dead) == ["player_50"]) == gives


# --- the rows written about one role ---------------------------------------------------------------

@pytest.mark.parametrize("traits", [
    {"blocks": True}, {"visits": "under_body"}, {"visits_two": True},
    {"reads_suspicious": "when_killing_through_body"}, {"night_immune": "always"},
    {"night_immune": "first_nights"}, {"night_immune": "self_bet"}, {"attack_announced_as": "vigilante"},
    {"must_act": True, "blockable": False, "visits": "own_name"},
])
def test_one_role_has_each_trait_a_row_names(traits):
    """Rows whose wording names one role ("only the Chanteuse can block") assume it is the only role
    with that trait. A second role with it needs new rows (and a catalogue entry) first."""
    assert len(roles_with(**traits)) == 1, traits


@pytest.mark.parametrize("night_action", ["protect", "conceal", "pick"])
def test_one_role_has_each_action_a_row_names(night_action):
    assert len(roles_acting(night_action)) == 1, night_action
