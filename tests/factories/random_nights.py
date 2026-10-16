"""Random legal nights for the deduction engine's soundness tests, and the checker that says whether
a stated fact holds in the real game.

A random night deals a random cast, kills a few players on earlier nights or days, lets every living
role make a random legal choice, and resolves it with the real engine. The deduction tests then
compute each surviving seat's lines from its own records only, and check every fact a line states
against the true roles and the resolved night. Thousands of such nights are the engine's oracle: a
rule that says more than the game guarantees fails here.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from Agents.rules.night import borrowed_kind, pack_carrier, resolve_night, usable_bodies
from Agents.rules.night_record import PACK_ACTOR, night_action_records
from Agents.schemas.deduction import AttackOutcome, BlockedBy, ProtectedBy, RoleIn
from Agents.schemas.game_events import DeathRecord, NightActionRecord
from Agents.schemas.night import NightChoice, NightOutcome
from Agents.schemas.roles import PICKABLE_SIDES, ROLE_SPECS

BASE_ROLES = ["investigator", "sentinel", "trailseer", "vigilante", "sigilist", "healer", "chanteuse", "illusionist"]
"""The eight roles in every cast; the lone killer and the neutral are drawn on top."""
CASTS = [(killer, neutral) for killer in ("serial_killer", "necromancer")
         for neutral in ("speculator", "fortune_teller")]
WOLF_ROLES = {role for role in BASE_ROLES if ROLE_SPECS[role].pack}


@dataclass
class ResolvedNight:
    """One random night after the engine resolved it."""

    roles: dict[str, str]
    night: int
    choices: list[NightChoice]
    outcome: NightOutcome
    records: list[NightActionRecord]
    alive_at_dusk: list[str]
    dead_roster: list[DeathRecord]
    """The public roster the next morning: earlier deaths, then this night's."""

    def receivers(self) -> list[str]:
        """The seats that get a record of this night: alive at dusk and alive at dawn."""
        return [player for player in self.alive_at_dusk if player not in self.outcome.deaths]


# --- dealing and earlier deaths ---------------------------------------------------------------

def _deal_roles(rng: random.Random) -> dict[str, str]:
    killer, neutral = rng.choice(CASTS)
    roles = BASE_ROLES + [killer, neutral]
    rng.shuffle(roles)
    return {f"player_{seat + 1}": role for seat, role in enumerate(roles)}


def _earlier_deaths(rng: random.Random, roles: dict[str, str], night: int) -> list[DeathRecord]:
    """Up to four players who died before `night`: at night (never the serial killer, never the
    necromancer on night 1; a non-wolf body may have been concealed) or by a lynch."""
    deaths: list[DeathRecord] = []
    if night == 1:
        return deaths  # day 1 has no vote and nothing happened before night 1
    for player in rng.sample(list(roles), rng.randint(0, 4)):
        role = roles[player]
        died_at_night = role != "serial_killer" and rng.random() < 0.5
        if died_at_night:
            day = rng.randint(1, night - 1)
            if role == "necromancer" and day == 1:
                continue
            concealed = role not in WOLF_ROLES and role != "serial_killer" and rng.random() < 0.3
            deaths.append(DeathRecord(player=player, role="" if concealed else role, day=day,
                                      phase="night", concealed=concealed))
        else:
            deaths.append(DeathRecord(player=player, role=role, day=rng.randint(2, night), phase="day"))
    return deaths


# --- the night's choices ----------------------------------------------------------------------

def _someone_else(rng: random.Random, actor: str, pool: list[str]) -> str | None:
    others = [player for player in pool if player != actor]
    return rng.choice(others) if others else None


def _pack_choices(rng, roles, alive, night) -> list[NightChoice]:
    """The pack's kill (made by the carrier), the Chanteuse's block and the Illusionist's conceal."""
    choices = []
    wolves = [p for p in alive if roles[p] in WOLF_ROLES]
    non_wolves = [p for p in alive if roles[p] not in WOLF_ROLES]
    carrier = pack_carrier(wolves, night)
    if carrier and non_wolves and rng.random() < 0.9:
        choices.append(NightChoice(carrier, roles[carrier], "kill", rng.choice(non_wolves)))
    for player in wolves:
        if roles[player] == "chanteuse" and rng.random() < 0.9:
            target = _someone_else(rng, player, non_wolves)
            if target:
                choices.append(NightChoice(player, "chanteuse", "block", target))
        if roles[player] == "illusionist" and rng.random() < 0.6:
            choices.append(NightChoice(player, "illusionist", "conceal", None))
    return choices


def _necromancer_choice(rng, actor, alive, night, earlier_deaths) -> list[NightChoice]:
    bodies = usable_bodies(earlier_deaths)
    if night == 1 or not bodies or rng.random() >= 0.85:
        return []
    body = rng.choice(bodies)
    body_role = next(d.role for d in earlier_deaths if d.player == body)
    target = _someone_else(rng, actor, alive)
    if target is None:
        return []
    return [NightChoice(actor, "necromancer", borrowed_kind(body_role), target, via=body)]


# Town roles that act on another player: (role, kind, how often they act).
TOWN_ACTIONS = [("healer", "protect", 1.0), ("investigator", "investigate", 0.85), ("sentinel", "watch", 0.85),
                ("trailseer", "follow", 0.85), ("sigilist", "sigil", 0.7), ("vigilante", "kill", 0.5)]


def _solo_choices(rng, roles, alive, night, earlier_deaths) -> list[NightChoice]:
    choices = []
    holder = {roles[player]: player for player in alive}
    if "serial_killer" in holder:
        actor = holder["serial_killer"]
        choices.append(NightChoice(actor, "serial_killer", "kill", _someone_else(rng, actor, alive)))
    if "necromancer" in holder:
        choices += _necromancer_choice(rng, holder["necromancer"], alive, night, earlier_deaths)
    for role, kind, how_often in TOWN_ACTIONS:
        if role not in holder:
            continue
        actor = holder[role]
        if rng.random() < how_often:
            choices.append(NightChoice(actor, role, kind, _someone_else(rng, actor, alive)))
        elif role == "vigilante":
            choices.append(NightChoice(actor, role, "hold_fire", None))
    if "speculator" in holder and rng.random() < 0.3:
        choices.append(NightChoice(holder["speculator"], "speculator", "pick", rng.choice(list(PICKABLE_SIDES))))
    if "fortune_teller" in holder:
        actor = holder["fortune_teller"]
        if rng.random() < 0.4:
            choices.append(NightChoice(actor, "fortune_teller", "bet", actor))
        else:
            named_role = rng.choice([None, *sorted(set(roles.values()))])
            choices.append(NightChoice(actor, "fortune_teller", "bet", _someone_else(rng, actor, alive),
                                       role_named=named_role))
    return choices


def random_night(rng: random.Random) -> ResolvedNight:
    """One random legal night, resolved by the real engine."""
    roles = _deal_roles(rng)
    night = rng.randint(1, 4)
    earlier_deaths = _earlier_deaths(rng, roles, night)
    dead = {death.player for death in earlier_deaths}
    alive = [player for player in roles if player not in dead]

    choices = _pack_choices(rng, roles, alive, night) + _solo_choices(rng, roles, alive, night, earlier_deaths)
    illusionist_body = any(death.role == "illusionist" for death in earlier_deaths)
    body_conceals = rng.randint(0, 2) if illusionist_body else 0

    outcome = resolve_night(choices, roles, night, body_conceals)
    records = night_action_records(choices, outcome, roles)
    this_nights_deaths = [
        DeathRecord(player=player, role="" if player in outcome.concealed else roles[player],
                    day=night, phase="night", concealed=player in outcome.concealed)
        for player in outcome.deaths
    ]
    return ResolvedNight(roles=roles, night=night, choices=choices, outcome=outcome, records=records,
                         alive_at_dusk=alive, dead_roster=earlier_deaths + this_nights_deaths)


# --- checking a stated fact against the real night --------------------------------------------

def _went_ahead(choice: NightChoice, outcome: NightOutcome) -> bool:
    return choice.actor not in outcome.blocked


def _pack_carrier_of(game: ResolvedNight) -> str | None:
    for choice in game.choices:
        if choice.kind == "kill" and choice.via is None and ROLE_SPECS[choice.role].pack:
            return choice.actor
    return None


def _blocked_by_holds(fact: BlockedBy, game: ResolvedNight) -> bool:
    blocked_player = _pack_carrier_of(game) if fact.player == PACK_ACTOR else fact.player
    if blocked_player not in game.outcome.blocked:
        return False
    for choice in game.choices:
        made_through_body = choice.via is not None
        if (choice.kind == "block" and choice.target == blocked_player
                and made_through_body == fact.through_body and _went_ahead(choice, game.outcome)):
            return True
    return False


def _attack_outcome_holds(fact: AttackOutcome, game: ResolvedNight) -> bool:
    if fact.player not in game.outcome.attacks_on:
        return True  # no attack went ahead on the player: every reading allows that
    if not fact.immune_as or game.outcome.verdicts[fact.player] != "immune":
        return False
    if fact.player in game.outcome.self_bets:
        reason = "self_bet"
    else:
        reason = game.roles[fact.player]
    return reason in fact.immune_as


def _protected_by_holds(fact: ProtectedBy, game: ResolvedNight) -> bool:
    for choice in game.choices:
        made_through_body = choice.via is not None
        if (choice.kind == "protect" and choice.target == fact.player
                and made_through_body == fact.through_body and _went_ahead(choice, game.outcome)):
            return True
    return False


def fact_holds(fact, game: ResolvedNight) -> bool:
    """Whether a fact a line states is true in the real game."""
    if isinstance(fact, RoleIn):
        return game.roles[fact.player] in fact.roles
    if isinstance(fact, BlockedBy):
        return _blocked_by_holds(fact, game)
    if isinstance(fact, AttackOutcome):
        return _attack_outcome_holds(fact, game)
    if isinstance(fact, ProtectedBy):
        return _protected_by_holds(fact, game)
    raise TypeError(f"no checker for {type(fact).__name__}")
