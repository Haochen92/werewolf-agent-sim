"""The night, resolved once for every role.

Rules located at ``evidence/game_play_enhancement/role_sheet.md``.
"""

from __future__ import annotations

from Agents.rules.seats import seat_order
from Agents.schemas.night import (
    ATTACKER_TYPE_OF_ROLE,
    Attack,
    Bet,
    NightChoice,
    NightOutcome,
    NightVerdict,
)
from Agents.schemas.roles import BORROWED_ABILITY, ROLE_SPECS, TOWN, WOLVES, NightKind
from Agents.schemas.roles import side_of  # noqa: F401  (re-exported: the record and the nodes read it here)


def can_be_blocked(role: str) -> bool:
    """Whether a roleblock takes on a role: town and wolves yes; the lone killers (the serial
    killer, the necromancer) and the neutrals never."""
    return side_of(role) in (TOWN, WOLVES)


def is_night_immune(role: str | None, night: int) -> bool:
    """Whether a role cannot be killed at night: the serial killer always; the necromancer on
    night 1 only (the sheet's rule, kept here so immunity has one home)."""
    if role is None:
        return False
    if role == "necromancer":
        return night == 1
    return ROLE_SPECS[role].night_immune


def pack_carrier(surviving_wolves: list[str], night: int) -> str | None:
    """The wolf who performs tonight's kill and is the only wolf who visits. Rotates through the
    living wolves in seat order, one per night, so a lone survivor always carries."""
    wolves = seat_order(surviving_wolves)
    if not wolves:
        return None
    index = (night - 1) % len(wolves)
    return wolves[index]


def borrowed_kind(body_role: str) -> NightKind | None:
    """What a necromancer does through a dead player of this role; None for a body that gives
    nothing (a lone killer's, a neutral's)."""
    return BORROWED_ABILITY.get(body_role)


def usable_bodies(dead_roster) -> list[str]:
    """The dead players a necromancer may act through tonight: revealed (not concealed), with an
    ability to give. The same body may be used night after night (balance ruling 2026-10-09:
    on 19 of its 31 nights the necromancer had no body that could kill)."""
    bodies: list[str] = []
    for death in dead_roster:
        player = death.get("player") if isinstance(death, dict) else death.player
        role = death.get("role") if isinstance(death, dict) else death.role
        if not role or borrowed_kind(role) is None:
            continue
        bodies.append(player)
    return seat_order(bodies)


def is_pack_kill(choice: NightChoice) -> bool:
    """The pack's own kill: a wolf killing in its own name (a necromancer through a wolf's body
    is not the pack's)."""
    return choice.kind == "kill" and choice.via is None and ROLE_SPECS[choice.role].pack


def choices_from_targets(
    night: int,
    *,
    wolves_target: str | None,
    healer_target: str | None,
    serial_killer_target: str | None,
    vigilante_target: str | None,
    investigator_target: str | None = None,
    healer: str | None,
    serial_killer: str | None,
    vigilante: str | None,
    investigator: str | None = None,
    surviving_wolves: list[str],
    vigilante_held_fire: bool = False,
) -> list[NightChoice]:
    """The choices of a NINE-SEAT game's night, from the targets its state kept per role: what
    the hallucination bench rebuilds for old games. The ten-seat engine writes choices directly.

    The kills first, pack then serial killer then vigilante: the order the attacks on one
    player are announced in.
    """
    choices: list[NightChoice] = []
    if wolves_target:
        carrier = pack_carrier(surviving_wolves, night)
        if carrier is None:
            raise ValueError("the pack chose a target but no wolf is alive to carry the kill")
        choices.append(NightChoice(carrier, "wolf", "kill", wolves_target))
    if serial_killer and serial_killer_target:
        choices.append(NightChoice(serial_killer, "serial_killer", "kill", serial_killer_target))
    if vigilante and vigilante_target:
        choices.append(NightChoice(vigilante, "vigilante", "kill", vigilante_target))
    elif vigilante and vigilante_held_fire:
        choices.append(NightChoice(vigilante, "vigilante", "hold_fire", None))
    if healer and healer_target:
        choices.append(NightChoice(healer, "healer", "protect", healer_target))
    if investigator and investigator_target:
        choices.append(NightChoice(investigator, "investigator", "investigate", investigator_target))
    return choices


def _attacker_type(choice: NightChoice, roles: dict[str, str]) -> str:
    """How the morning names this kill: by the killer's role, or by the body's kind, reanimated, for
    a kill made through a body (owner, 2026-10-10: the body's kind alone told the table two wolf
    attacks happened when one was the necromancer's)."""
    if choice.via:
        return "reanimated_" + ATTACKER_TYPE_OF_ROLE[roles[choice.via]]
    return ATTACKER_TYPE_OF_ROLE[choice.role]


def resolve_night(choices: list[NightChoice], roles: dict[str, str], night: int,
                  body_conceals: int = 0) -> NightOutcome:
    """Apply the shared rules to the night's choices, all at once.

    In order: a block cancels the action of a town player or a wolf (the serial killer, the
    necromancer and the neutral cannot be blocked); every action that went ahead on a player is
    a visit, shown under the body's name for a necromancer; kills become attacks; a sigil on a
    player who attacked tonight in their own name adds the sigilist's retaliation to the attacks
    on them (their own victim still dies); each attacked player gets one verdict, immunity (the
    rules' or a fortune teller's self-bet) over protection over death; a conceal hides the pack's
    victim's role if that victim died; the investigators' reads, the speculators' picks and the
    fortune tellers' bets are settled.
    """
    # 1. Blocks. A block takes on town and on wolves; the serial killer, the necromancer and
    # the neutral can never be blocked (owner, 2026-10-08). A blocked blocker still blocks:
    # all actions are simultaneous, and a wolf blocking a wolf is the pack's own affair.
    blocked: list[str] = []
    blocks_without_effect: list[str] = []
    for choice in choices:
        if choice.kind != "block" or choice.target is None:
            continue
        target_role = roles.get(choice.target)
        if target_role is not None and can_be_blocked(target_role):
            if choice.target not in blocked:
                blocked.append(choice.target)
        else:
            blocks_without_effect.append(choice.target)

    in_effect: list[NightChoice] = []
    for choice in choices:
        if choice.actor not in blocked:
            in_effect.append(choice)

    # 2. Visits: every action that went ahead on a player. A pick names a side and a bet is not
    # a visit; a necromancer's visit shows its body; a conceal is a visit to the pack's victim
    # (the sheet: the sentinel can catch the carrier and the illusionist at one door).
    pack_victims: list[str] = []
    for choice in in_effect:
        if is_pack_kill(choice) and choice.target is not None:
            pack_victims.append(choice.target)
    visits: list[tuple[str, str]] = []
    for choice in in_effect:
        if choice.kind == "conceal":
            visits.extend((choice.actor, victim) for victim in pack_victims)
            continue
        if choice.kind in ("pick", "bet", "hold_fire") or choice.target is None:
            continue
        visits.append((choice.via or choice.actor, choice.target))

    # 3. Attacks, then the sigils' retaliation on tonight's attackers. An attack made through a
    # body cannot be punished: the body made it, and a sigil is never on a dead player.
    attackers: list[str] = []
    attacks_on: dict[str, list[Attack]] = {}
    for choice in in_effect:
        if choice.kind != "kill" or choice.target is None:
            continue
        attack = Attack(choice.actor, _attacker_type(choice, roles))
        attacks_on.setdefault(choice.target, []).append(attack)
        if choice.via is None and choice.actor not in attackers:
            attackers.append(choice.actor)
    for choice in in_effect:
        if choice.kind != "sigil" or choice.target is None:
            continue
        if choice.target in attackers:
            kind = "reanimated_sigilist" if choice.via else "sigilist"  # a sigil placed through a body
            attacks_on.setdefault(choice.target, []).append(Attack(choice.actor, kind))

    # 4. One verdict per attacked player. A fortune teller's self-bet makes it unharmed tonight.
    protected: list[str] = []
    for choice in in_effect:
        if choice.kind == "protect" and choice.target is not None:
            protected.append(choice.target)
    self_bets: list[str] = []
    for choice in in_effect:
        if choice.kind == "bet" and choice.target == choice.actor:
            self_bets.append(choice.actor)
    verdicts: dict[str, NightVerdict] = {}
    for target in attacks_on:
        if is_night_immune(roles.get(target), night) or target in self_bets:
            verdicts[target] = "immune"
        elif target in protected:
            verdicts[target] = "saved"
        else:
            verdicts[target] = "killed"

    killed: list[str] = []
    for target, verdict in verdicts.items():
        if verdict == "killed":
            killed.append(target)
    deaths = seat_order(killed)

    # 5. Conceal: the pack's victim, if the pack's kill landed.
    concealed: list[str] = []
    for choice in in_effect:
        if choice.kind != "conceal":
            continue
        for victim in pack_victims:
            if verdicts.get(victim) == "killed" and victim not in concealed:
                concealed.append(victim)
    # A kill through the illusionist's body also cleans its victim, while the dead illusionist has a
    # conceal left (``body_conceals``; owner, 2026-10-10): the role is hidden and the necromancer
    # learns it. The conceal is spent in the resolution node.
    for choice in in_effect:
        if (body_conceals > 0 and choice.kind == "kill" and choice.via is not None
                and roles.get(choice.via) == "illusionist" and verdicts.get(choice.target) == "killed"
                and choice.target not in concealed):
            concealed.append(choice.target)
    # A conceal that took also hides the attacking trace: the carrier's visit to that victim is
    # not among the visits the sentinel and trailseer see (balance ruling 2026-10-09). The
    # carrier's other visit that night, and the illusionist's own, stay visible.
    carriers = [c.actor for c in in_effect if is_pack_kill(c) and c.target in concealed]
    visits = [(visitor, visited) for visitor, visited in visits
              if not (visitor in carriers and visited in concealed)]

    # 6. What an investigator reads: the wolves, and a necromancer on a night it attacked.
    suspicious: list[str] = []
    for player, role in roles.items():
        if role in ROLE_SPECS and side_of(role) == WOLVES:
            suspicious.append(player)
    for choice in in_effect:
        if choice.kind == "kill" and choice.via is not None and choice.actor not in suspicious:
            suspicious.append(choice.actor)

    # 7. The neutrals: picks announced, bets settled against the deaths.
    picks: list[tuple[str, str]] = []
    bets: list[Bet] = []
    for choice in in_effect:
        if choice.kind == "pick" and choice.target is not None:
            picks.append((choice.actor, choice.target))
        elif choice.kind == "bet" and choice.target is not None and choice.target != choice.actor:
            points = 0
            if choice.target in deaths:
                points = 1
                if choice.role_named and roles.get(choice.target) == choice.role_named:
                    points = 2
            bets.append(Bet(choice.actor, choice.target, choice.role_named, points))

    return NightOutcome(
        night=night,
        blocked=blocked,
        blocks_without_effect=blocks_without_effect,
        visits=visits,
        attackers=attackers,
        attacks_on=attacks_on,
        verdicts=verdicts,
        deaths=deaths,
        concealed=concealed,
        suspicious=suspicious,
        picks=picks,
        bets=bets,
        self_bets=self_bets,
    )


def visitors_of(outcome: NightOutcome, player: str) -> list[str]:
    """Who visited a player tonight, in seat order (what the sentinel sees)."""
    visitors: list[str] = []
    for visitor, visited in outcome.visits:
        if visited == player and visitor not in visitors:
            visitors.append(visitor)
    return seat_order(visitors)


def visited_by(outcome: NightOutcome, player: str) -> list[str]:
    """Whom a player visited tonight (what the trailseer sees): usually one; a wolf who carries the
    kill and uses its skill visits two."""
    visited_players: list[str] = []
    for visitor, visited in outcome.visits:
        if visitor == player and visited not in visited_players:
            visited_players.append(visited)
    return visited_players
