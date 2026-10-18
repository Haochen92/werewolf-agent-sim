"""Random legal nights for the deduction engine's soundness tests, and the checker that says whether
a stated fact holds in the real game.

A random night deals a random cast, kills a few players on earlier nights or days, lets every living
role make a random legal choice, and resolves it with the real engine (the rules, the records and the
resolution node, which writes the morning). The deduction tests then compute each surviving seat's
lines from its own records and the public morning only, and check every fact a line states against
the true roles and the resolved night. Thousands of such nights are the engine's oracle: a
rule that says more than the game guarantees fails here.
"""

from __future__ import annotations

import os
import random
from dataclasses import dataclass
from types import SimpleNamespace

# Before any engine import: a script that simulates thousands of games with these factories outside
# pytest (tests/conftest.py does the same) must not send a trace per turn to Langfuse. 2026-10-17:
# one 20,000-night run flooded it. An explicit LANGFUSE_TRACING_ENABLED=true still wins.
os.environ.setdefault("LANGFUSE_TRACING_ENABLED", "false")

from Agents.config.game import GameConfig  # noqa: E402
from Agents.nodes.night.resolution import night_resolution
from Agents.nodes.orchestrator import day_resolution, determine_winner, is_draw
from Agents.rules.night import borrowed_kind, is_pack_kill, pack_carrier, resolve_night, usable_bodies
from Agents.rules.night_record import PACK_ACTOR, night_action_records, own_night_actions
from Agents.schemas.deduction import (
    ActedThroughBody,
    AnyOf,
    CheckRead,
    ChoseAction,
    Compatible,
    DiedBy,
    NoShownVisitBy,
    NoShownVisitTo,
    NotAllTrue,
    NoVisitBy,
    OnNight,
    OpenRoles,
    AttackedInOwnName,
    AttackOutcome,
    AttacksOnlyOn,
    BlockedBy,
    BodyUsable,
    CarriedOrAmong,
    CarriedPackKill,
    HeldBy,
    KilledThroughBody,
    MadeBy,
    MadeNoChoice,
    NeverPicked,
    NoAttackUnless,
    NoConcealsLeft,
    NoHiddenVisitTo,
    NoKillThroughBody,
    NotProtected,
    NoUsesLeft,
    NotRoleUnlessBlocked,
    NoVisitTo,
    PickMade,
    ProtectedBy,
    PublicRecord,
    RoleIn,
    SilentAttack,
    VisitAsClaimed,
    Visited,
    VisitorsAmong,
    WentTo,
)
from Agents.schemas.game_events import DayVote, DeathRecord, NightActionRecord, NightAnnouncement, ReadOutWill
from Agents.schemas.metrics import Metrics
from Agents.schemas.night import NightChoice, NightOutcome
from Agents.schemas.roles import PICKABLE_SIDES, ROLE_SPECS, cast_role_counts

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
    announcement: NightAnnouncement
    """The public morning as data, as the resolution node committed it."""
    morning: str
    """The moderator's morning prose, from the same node run."""
    body_conceals: int = 0
    """The Illusionist's conceals left when the night began (one pool for it and its body)."""
    uses_after: dict[str, int] | None = None
    """Every limited ability's uses left when the night ended (a whole random game keeps them)."""

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


def _has_uses(role: str, uses_left: dict[str, int] | None) -> bool:
    """Whether a limited ability has a use left; every ability does when uses are not tracked."""
    return uses_left is None or uses_left.get(role, 1) > 0


def _pack_choices(rng, roles, alive, night, kill_rate=0.9, uses_left=None) -> list[NightChoice]:
    """The pack's kill (made by the carrier), the Chanteuse's block and the Illusionist's conceal.
    `kill_rate` 1.0 keeps the pack's must-act rule (catalogue L5); `uses_left` limits the conceal."""
    choices = []
    wolves = [p for p in alive if roles[p] in WOLF_ROLES]
    non_wolves = [p for p in alive if roles[p] not in WOLF_ROLES]
    carrier = pack_carrier(wolves, night)
    if carrier and non_wolves and rng.random() < kill_rate:
        choices.append(NightChoice(carrier, roles[carrier], "kill", rng.choice(non_wolves)))
    for player in wolves:
        if roles[player] == "chanteuse" and rng.random() < 0.9:
            target = _someone_else(rng, player, non_wolves)
            if target:
                choices.append(NightChoice(player, "chanteuse", "block", target))
        if roles[player] == "illusionist" and rng.random() < 0.6 and _has_uses("illusionist", uses_left):
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


def _solo_choices(rng, roles, alive, night, earlier_deaths, uses_left=None) -> list[NightChoice]:
    """`uses_left`: the limited abilities left (a role out of them makes no choice); None: unlimited."""
    choices = []
    holder = {roles[player]: player for player in alive}
    if "serial_killer" in holder:
        actor = holder["serial_killer"]
        choices.append(NightChoice(actor, "serial_killer", "kill", _someone_else(rng, actor, alive)))
    if "necromancer" in holder:
        choices += _necromancer_choice(rng, holder["necromancer"], alive, night, earlier_deaths)
    for role, kind, how_often in TOWN_ACTIONS:
        if role not in holder or not _has_uses(role, uses_left):
            continue
        actor = holder[role]
        if rng.random() < how_often:
            choices.append(NightChoice(actor, role, kind, _someone_else(rng, actor, alive)))
        elif role == "vigilante":
            choices.append(NightChoice(actor, role, "hold_fire", None))
    if "speculator" in holder and rng.random() < 0.3 and _has_uses("speculator", uses_left):
        choices.append(NightChoice(holder["speculator"], "speculator", "pick", rng.choice(list(PICKABLE_SIDES))))
    if "fortune_teller" in holder:
        actor = holder["fortune_teller"]
        if rng.random() < 0.4 and _has_uses("fortune_teller", uses_left):
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
    update = resolve_through_the_node(choices, roles, night, alive, body_conceals)
    return ResolvedNight(roles=roles, night=night, choices=choices, outcome=outcome, records=records,
                         alive_at_dusk=alive, dead_roster=earlier_deaths + this_nights_deaths,
                         announcement=update["night_announcements"][0],
                         morning=update["day_summaries"][0].summary, body_conceals=body_conceals)


def resolve_through_the_node(choices: list[NightChoice], roles: dict[str, str], night: int, alive: list[str],
                             body_conceals: int = 0, earlier_records: list[NightActionRecord] = (),
                             uses_left: dict[str, int] | None = None) -> dict:
    """The night run through the real resolution node: its whole update (the morning prose, the
    morning as data, the records, the roster, the wills). `earlier_records` are the wills' source;
    `uses_left`, when given, replaces the conceals-only pool."""
    wolves = [player for player in alive if roles[player] in WOLF_ROLES]
    state = {
        "current_day": night, "roles": roles, "night_choices": list(choices),
        "uses_left": dict(uses_left) if uses_left is not None else {"illusionist": body_conceals},
        "day_channel": [], "night_actions": list(earlier_records),
        "surviving_wolves": wolves, "surviving_villagers": [player for player in alive if player not in wolves],
    }
    return night_resolution(state, SimpleNamespace(context={"metrics": Metrics()}))


# --- whole random games: several nights, lynches between them, real wills ---------------------

@dataclass
class RandomGame:
    """A random legal game of one to five nights, every night resolved by the real engine, with a
    random lynch on most days from day 2. The public record is kept at every point a seat reasons
    from (after each lynch and each morning), so a test sees what the public knew then."""

    roles: dict[str, str]
    nights: dict[int, ResolvedNight]
    snapshots: list[PublicRecord]
    """The public record after each lynch and each morning, in order."""
    records: list[NightActionRecord]
    """Every record the seats received, all nights."""
    messages: list[tuple[str, list[ReadOutWill]]]
    """Each game-master message (a vote result with a lynch, a morning) and the wills its node
    committed beside it as data."""

    def payload_of(self, player: str, snapshot: PublicRecord) -> dict:
        """The deduction fields of `player`'s payload at that point (its own records up to then)."""
        last_night = max((a.night for a in snapshot.announcements), default=0)
        known = [r for r in self.records if r.day <= last_night]
        return {"player_id": player, "player_role": self.roles[player],
                "cast_role_counts": snapshot.cast_role_counts, "dead_roster": snapshot.dead_roster,
                "night_actions": own_night_actions(known, player, self.roles[player]),
                "night_announcements": snapshot.announcements, "read_out_wills": snapshot.wills,
                "surviving_players": snapshot.living}


def _game_over(roles: dict[str, str], dead: list[DeathRecord]) -> bool:
    gone = {death.player for death in dead}
    wolves = [p for p in roles if p not in gone and roles[p] in WOLF_ROLES]
    state = {"roles": roles, "lineup": sorted(set(roles.values())), "surviving_wolves": wolves,
             "surviving_villagers": [p for p in roles if p not in gone and p not in wolves]}
    return determine_winner(state) is not None or is_draw(state)


def random_game(rng: random.Random) -> RandomGame:
    """One random legal game: the pack always attacks (catalogue L5), limited abilities stop when
    spent, lynches read out wills, and the night node writes the mornings and the night's wills."""
    roles = _deal_roles(rng)
    counts = cast_role_counts(roles)
    uses = {role: n for role, n in GameConfig().starting_uses().items() if role in counts}
    dead: list[DeathRecord] = []
    records: list[NightActionRecord] = []
    mornings, wills, nights, snapshots, messages = [], [], {}, [], []

    def snapshot():
        gone = {death.player for death in dead}
        snapshots.append(PublicRecord(cast_role_counts=counts, dead_roster=list(dead),
                                      announcements=list(mornings), wills=list(wills),
                                      living=[p for p in roles if p not in gone]))

    for night in range(1, rng.randint(1, 5) + 1):
        if night >= 2 and rng.random() < 0.6:
            player = rng.choice([p for p in roles if p not in {d.player for d in dead}])
            update = lynch_through_the_node(player, roles, night, dead, records)
            dead += update["dead_roster"]
            wills += update["read_out_wills"]
            messages.append((update["day_summaries"][0].summary, update["read_out_wills"]))
            snapshot()
            if _game_over(roles, dead):
                break
        alive = [p for p in roles if p not in {d.player for d in dead}]
        choices = (_pack_choices(rng, roles, alive, night, kill_rate=1.0, uses_left=uses)
                   + _solo_choices(rng, roles, alive, night, dead, uses_left=uses))
        body_conceals = uses.get("illusionist", 0)
        update = resolve_through_the_node(choices, roles, night, alive, earlier_records=records, uses_left=uses)
        outcome = resolve_night(choices, roles, night, body_conceals)
        nights[night] = ResolvedNight(
            roles=roles, night=night, choices=choices, outcome=outcome,
            records=night_action_records(choices, outcome, roles), alive_at_dusk=alive,
            dead_roster=list(dead) + list(update.get("dead_roster", [])),
            announcement=update["night_announcements"][0], morning=update["day_summaries"][0].summary,
            body_conceals=body_conceals, uses_after=dict(update["uses_left"]))
        records += update["night_actions"]
        dead += update.get("dead_roster", [])
        mornings += update["night_announcements"]
        wills += update["read_out_wills"]
        messages.append((update["day_summaries"][0].summary, update["read_out_wills"]))
        uses = update["uses_left"]
        snapshot()
        if _game_over(roles, dead):
            break
    return RandomGame(roles=roles, nights=nights, snapshots=snapshots, records=records, messages=messages)


def lynch_through_the_node(player: str, roles: dict[str, str], day: int, dead: list[DeathRecord],
                            records: list[NightActionRecord]) -> dict:
    """A lynch of `player` on `day`, run through the real day-resolution node (every living
    player votes for it): the vote prose, the roster entry and the will, as a game commits them."""
    gone = {death.player for death in dead}
    alive = [p for p in roles if p not in gone]
    wolves = [p for p in alive if roles[p] in WOLF_ROLES]
    state = {"current_day": day, "roles": roles, "day_channel": [], "night_actions": list(records),
             "day_votes": [DayVote(voter=voter, votee=player) for voter in alive if voter != player],
             "surviving_wolves": wolves, "surviving_villagers": [p for p in alive if p not in wolves],
             "no_lynch_streak": 0}
    return day_resolution(state, SimpleNamespace(context={"metrics": Metrics()}))


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


def _every_visit(game: ResolvedNight) -> list[tuple[str, str]]:
    """Every visit an action that went ahead made, under the name it shows (the body's, for the
    Necromancer), hidden visits included: what really happened, not what a watcher saw."""
    in_effect = [choice for choice in game.choices if _went_ahead(choice, game.outcome)]
    pack_victims = [choice.target for choice in in_effect if is_pack_kill(choice) and choice.target]
    visits = []
    for choice in in_effect:
        if choice.kind == "conceal":
            visits.extend((choice.actor, victim) for victim in pack_victims)
        elif choice.kind not in ("pick", "bet", "hold_fire") and choice.target is not None:
            visits.append((choice.via or choice.actor, choice.target))
    return visits


def _acted_through_body_holds(fact: ActedThroughBody, game: ResolvedNight) -> bool:
    return any(choice.via == fact.body and choice.target == fact.target and _went_ahead(choice, game.outcome)
               for choice in game.choices)


def _killed_through_body_holds(fact: KilledThroughBody, game: ResolvedNight) -> bool:
    return any(choice.actor == fact.player and choice.kind == "kill" and choice.via is not None
               and _went_ahead(choice, game.outcome) for choice in game.choices)


def _carried_pack_kill_holds(fact: CarriedPackKill, game: ResolvedNight) -> bool:
    return any(is_pack_kill(choice) and choice.actor == fact.player and _went_ahead(choice, game.outcome)
               for choice in game.choices)


def _no_visit_to_holds(fact: NoVisitTo, game: ResolvedNight) -> bool:
    return all(visitor == fact.except_name for visitor, visited in _every_visit(game) if visited == fact.target)


def _no_attack_unless_holds(fact: NoAttackUnless, game: ResolvedNight) -> bool:
    if game.roles[fact.player] in fact.unless_roles:
        return True
    return not any(choice.actor == fact.player and choice.kind == "kill" and _went_ahead(choice, game.outcome)
                   for choice in game.choices)


def _made_by_holds(fact: MadeBy, game: ResolvedNight) -> bool:
    if fact.action == "healer":
        return any(choice.kind == "protect" and choice.via is None and choice.target == fact.target
                   and choice.actor in fact.players and _went_ahead(choice, game.outcome) for choice in game.choices)
    return any(attack.attacker_type == fact.action and attack.attacker in fact.players
               for attack in game.outcome.attacks_on.get(fact.target, []))


def _carried_or_among_holds(fact: CarriedOrAmong, game: ResolvedNight) -> bool:
    carrier = _pack_carrier_of(game)
    if (carrier is not None and game.roles[carrier] == fact.role
            and _carried_pack_kill_holds(CarriedPackKill(carrier), game)):
        return True
    return any(game.roles[player] == fact.role for player in fact.players)


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
    if isinstance(fact, WentTo):
        return (fact.visitor, fact.target) in _every_visit(game)
    if isinstance(fact, ActedThroughBody):
        return _acted_through_body_holds(fact, game)
    if isinstance(fact, NoVisitTo):
        return _no_visit_to_holds(fact, game)
    if isinstance(fact, NotRoleUnlessBlocked):
        return game.roles[fact.player] != fact.role or fact.player in game.outcome.blocked
    if isinstance(fact, CarriedPackKill):
        return _carried_pack_kill_holds(fact, game)
    if isinstance(fact, NoAttackUnless):
        return _no_attack_unless_holds(fact, game)
    if isinstance(fact, KilledThroughBody):
        return _killed_through_body_holds(fact, game)
    if isinstance(fact, MadeBy):
        return _made_by_holds(fact, game)
    if isinstance(fact, VisitorsAmong):
        return all(visitor in fact.players for visitor, visited in _every_visit(game) if visited == fact.target)
    if isinstance(fact, CarriedOrAmong):
        return _carried_or_among_holds(fact, game)
    if isinstance(fact, HeldBy):
        return all(player in fact.players for player, role in game.roles.items() if role == fact.role)
    if isinstance(fact, VisitAsClaimed):
        # A sighting is true only of a visit a watch or a follow could report (not a hidden one).
        visits = game.outcome.visits if fact.shown else _every_visit(game)
        return (fact.visitor, fact.target) in visits
    if isinstance(fact, AnyOf):
        return any(all(fact_holds(part, game) for part in branch) for branch in fact.branches)
    if isinstance(fact, NotAllTrue):
        return not all(fact_holds(part, game) for part in fact.facts)
    claimed = _claimed_fact_holds(fact, game)
    if claimed is not None:
        return claimed
    return _public_fact_holds(fact, game)


# --- the claims' facts (slice 11: catalogue Table E) -------------------------------------------

CHOICE_KIND = {"investigate": "investigate", "protect": "protect", "watch": "watch", "follow": "follow",
               "shoot": "kill", "kill": "kill", "sigil": "sigil", "block": "block", "bet": "bet"}
"""A claim's action word as the engine's choice kind (a shot is the Vigilante's kill)."""


def _chose_holds(fact: ChoseAction, game: ResolvedNight) -> bool:
    for choice in game.choices:
        if (choice.actor != fact.player or choice.via is not None or choice.target != fact.target
                or choice.kind != CHOICE_KIND.get(fact.action)):
            continue
        if fact.action == "shoot" and choice.role != "vigilante":
            continue
        if fact.went_ahead and not _went_ahead(choice, game.outcome):
            continue
        return True
    return False


def _claimed_fact_holds(fact, game: ResolvedNight) -> bool | None:
    """The facts the claims state; None for any other fact."""
    outcome = game.outcome
    if isinstance(fact, ChoseAction):
        return _chose_holds(fact, game)
    if isinstance(fact, CheckRead):
        return any(choice.actor == fact.player and choice.via is None and choice.kind == "investigate"
                   and choice.target == fact.target and _went_ahead(choice, outcome)
                   and (fact.target in outcome.suspicious) == fact.suspicious for choice in game.choices)
    if isinstance(fact, NoVisitBy):
        return not any(visitor == fact.player for visitor, _ in _every_visit(game))
    if isinstance(fact, NoShownVisitTo):
        return all(visitor == fact.except_name for visitor, visited in outcome.visits if visited == fact.target)
    if isinstance(fact, NoShownVisitBy):
        return not any(visitor == fact.player for visitor, _ in outcome.visits)
    if isinstance(fact, DiedBy):
        return fact.player in outcome.deaths and any(attack.attacker_type == fact.attacker_type
                                                     for attack in outcome.attacks_on.get(fact.player, []))
    if isinstance(fact, (Compatible, OpenRoles)):
        return True  # both can hold: the oracle counts where they did; OpenRoles is the brute force's
    return None


# --- the public rows' facts (level 5) ----------------------------------------------------------

def _visits_by_own_name(game: ResolvedNight) -> list[tuple[str, str]]:
    """Every visit an action under the actor's own name made, hidden ones included."""
    in_effect = [choice for choice in game.choices if _went_ahead(choice, game.outcome) and choice.via is None]
    pack_victims = [choice.target for choice in in_effect if is_pack_kill(choice) and choice.target]
    visits = []
    for choice in in_effect:
        if choice.kind == "conceal":
            visits.extend((choice.actor, victim) for victim in pack_victims)
        elif choice.kind not in ("pick", "bet", "hold_fire") and choice.target is not None:
            visits.append((choice.actor, choice.target))
    return visits


def _visited_holds(fact: Visited, game: ResolvedNight) -> bool:
    for visitor, visited in _visits_by_own_name(game):
        if visited != fact.target or game.roles[visitor] not in fact.roles:
            continue
        shown = (visitor, visited) in game.outcome.visits
        if fact.shown is None or shown == fact.shown:
            return True
    return False


def _silent_attack_holds(fact: SilentAttack, game: ResolvedNight) -> bool:
    outcome = game.outcome
    return any(attack.attacker_type == fact.attacker_type and outcome.verdicts[target] == "immune"
               and target not in outcome.self_bets and game.roles[target] in fact.immune_roles
               for target, attacks in outcome.attacks_on.items() for attack in attacks)


def _deaths_before(game: ResolvedNight) -> list[DeathRecord]:
    return [death for death in game.dead_roster if not (death.phase == "night" and death.day == game.night)]


def _public_fact_holds(fact, game: ResolvedNight) -> bool:
    outcome = game.outcome
    if isinstance(fact, NotProtected):
        return not any(choice.kind == "protect" and choice.target == fact.player and _went_ahead(choice, outcome)
                       for choice in game.choices)
    if isinstance(fact, Visited):
        return _visited_holds(fact, game)
    if isinstance(fact, NoHiddenVisitTo):
        return all(visit in outcome.visits for visit in _every_visit(game) if visit[1] == fact.target)
    if isinstance(fact, AttackedInOwnName):
        return any(choice.actor == fact.player and choice.kind == "kill" and choice.via is None
                   and _went_ahead(choice, outcome) for choice in game.choices)
    if isinstance(fact, SilentAttack):
        return _silent_attack_holds(fact, game)
    if isinstance(fact, AttacksOnlyOn):
        return all(game.roles[target] in fact.roles for target in outcome.attacks_on)
    if isinstance(fact, NoKillThroughBody):
        return not any(choice.kind == "kill" and choice.via is not None and _went_ahead(choice, outcome)
                       for choice in game.choices)
    if isinstance(fact, NoConcealsLeft):
        return game.body_conceals == 0
    if isinstance(fact, NoUsesLeft):
        assert game.uses_after is not None, "a single random night keeps no uses after it"
        return game.uses_after.get(fact.role, 0) == 0
    if isinstance(fact, MadeNoChoice):
        return not any(choice.actor == fact.player for choice in game.choices)
    if isinstance(fact, PickMade):
        return any(side == fact.side for _, side in outcome.picks)
    if isinstance(fact, BodyUsable):
        return fact.player in usable_bodies(_deaths_before(game))
    raise TypeError(f"no checker for {type(fact).__name__}")


def public_fact_holds(fact, night: int, game: RandomGame) -> bool:
    """Whether a public item's fact about `night` holds in the whole random game. A body usable
    "from night d on" may name a night the game never reached; that holds trivially."""
    if isinstance(fact, NeverPicked):
        return not any(actor == fact.player for resolved in game.nights.values()
                       for actor, _ in resolved.outcome.picks)
    if isinstance(fact, RoleIn):
        return game.roles[fact.player] in fact.roles  # a role is the same on every night
    if isinstance(fact, HeldBy):
        return all(player in fact.players for player, role in game.roles.items() if role == fact.role)
    if isinstance(fact, OnNight):
        return public_fact_holds(fact.fact, fact.night, game)
    if isinstance(fact, NotAllTrue):
        return not all(public_fact_holds(part, night, game) for part in fact.facts)
    if isinstance(fact, (Compatible, OpenRoles)):
        return True
    if night not in game.nights:
        assert isinstance(fact, BodyUsable), (fact, night)
        return True
    return fact_holds(fact, game.nights[night])
