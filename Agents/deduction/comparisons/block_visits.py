"""A sighting of the known Chanteuse's visit, read with the morning, and the visited player's roleblock
claim (acceptance case AC2, line 3; catalogue B19, B20, C7, L2, L4).

The living Chanteuse goes to two players at most in a night: the one she blocks, every night (she must
act), and the pack's victim when she carries the kill (C7). So when an engine source (the seat's own
watch or follow, or a read-out will) shows her going to a player who was not the pack's announced
victim that night, that visit was her block on that player. A block on the Serial Killer or a neutral
has no effect, so the visit agrees with the player's claim to have been roleblocked without proving it
("agrees with", not "as it said": the catalogue's AC2 folded). The Chanteuse is known when the seat's
candidate roles pin her on one player; a sighting of her name after her death is the Necromancer's
block through her body, which F1 already reads ("true in name").
It keeps a seat from reading her visit as evidence against the visited player (R3's misread). When
that player says it was roleblocked that night, the line adds that the visit agrees with it; AC2's
frozen payload has no such claim (player_8 claimed only its night-2 protection), so there the line
ends at the block (catalogue AC2 line 3, corrected in the slice 12 build).
"""

from __future__ import annotations

from Agents.deduction.comparisons.statements import Possible, blocked_fact
from Agents.deduction.joins.known_visits import known_visits
from Agents.deduction.joins.roleblocks import _pinned
from Agents.deduction.morning import announcement_of
from Agents.deduction.night_state import deaths_before_night
from Agents.schemas.deduction import (
    ActionClaim,
    ChoseAction,
    Compatible,
    DeductionItem,
    PublicRecord,
    SeatView,
    Source,
)

VERB = {"watch": "came to", "follow": "went to"}


def chanteuse_block_items(view: SeatView, record: PublicRecord, possible: Possible) -> list[DeductionItem]:
    chanteuse = _pinned(possible, view)
    if chanteuse is None or chanteuse == view.player_id:
        return []
    items, said = [], set()
    for visit in known_visits(view, record):
        night, target = visit.night, visit.target
        if (visit.visitor != chanteuse or visit.how == "own_action" or target == view.player_id
                or target not in view.living or (night, target) in said):
            continue
        if chanteuse in {death.player for death in deaths_before_night(view.dead_roster, night)}:
            continue  # her name on a later night is the Necromancer's, through her body
        victim = _pack_victim(view, night)
        if victim is None or victim[0] == target:
            continue
        said.add((night, target))
        source = "Your" if visit.holder is None else f"{visit.holder}'s will shows"
        how = "" if visit.holder is not None else f" {visit.how} shows"
        text = (f"{source}{how} {chanteuse}, the Chanteuse, {VERB[visit.how]} {target} on night {night}. "
                f"The pack's {victim[1]} that night was on {victim[0]}, so that visit was her block on {target}.")
        block = ChoseAction(chanteuse, "block", target, went_ahead=True)
        conclusion: tuple = (block,)
        first = Source("own_record", night) if visit.holder is None else Source("will", night, visit.holder)
        sources = (first, Source("announcement", night, victim[0]))
        derivation: tuple = (visit.record,)
        claim = _roleblock_claim(view, target, night)
        if claim is not None:
            text += f" It agrees with {target}'s claim that it was roleblocked on night {night}."
            conclusion += (Compatible((block,), (blocked_fact(target),)),)
            sources += (Source("claim", night, target),)
            derivation = (claim, *derivation)
        items.append(DeductionItem(row="F1+C7", subject=target, night=night, conclusion=conclusion, text=text,
                                   sources=sources, derivation=derivation, receiver=view.player_id))
    return items


def _pack_victim(view: SeatView, night: int) -> tuple[str, str] | None:
    """The player the pack's attack was announced on that night, and "kill" or "attack" (survived)."""
    announcement = announcement_of(view, night)
    if announcement is None:
        return None
    for death in announcement.deaths:
        if "wolves" in death.attacker_types:
            return death.player, "kill"
    for save in announcement.saves:
        if "wolves" in save.attacker_types:
            return save.player, "attack"
    return None


def _roleblock_claim(view: SeatView, player: str, night: int) -> ActionClaim | None:
    for claims in view.claims:
        if claims.player == player:
            return next((claim for claim in claims.actions if claim.latest and claim.blocked and claim.night == night),
                        None)
    return None
