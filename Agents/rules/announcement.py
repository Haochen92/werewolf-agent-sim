"""The morning announcement as data, built from the night report that night resolution commits.

The moderator's prose (Agents/nodes/night/resolution.py) is what the players read. The deduction
engine needs the same facts without parsing that prose, so the node also commits this record,
built here from the same NightReport at the same point. A test resolves random legal nights
through the node and checks that the prose and this record say the same thing
(tests/engine/test_night_announcement.py).
"""

from __future__ import annotations

from Agents.schemas.game_events import AnnouncedDeath, AnnouncedSave, HiddenBy, NightAnnouncement, Saver
from Agents.schemas.night import NightReport

REANIMATED_WOLF = "reanimated_wolves"
"""A kill through the illusionist's body: the only way a reanimated wolf attacks."""


def hidden_by(attacker_types: list[str]) -> HiddenBy:
    """How a hidden death's role was hidden, as the morning words it. The living illusionist and
    its body cannot both act on one night, so a reanimated wolf among the attackers means the
    necromancer hid it through the body (catalogue L8)."""
    return "reanimated_illusionist" if REANIMATED_WOLF in attacker_types else "illusionist"


def _saver(player: str, report: NightReport) -> Saver:
    if player in report.self_bet_saves:
        return "self_bet"
    if player in report.reanimated_saves:
        return "reanimated_healer"
    return "healer"


def night_announcement(report: NightReport) -> NightAnnouncement:
    """The morning of `report.night`, as data."""
    deaths = [
        AnnouncedDeath(player=player, attacker_types=list(types), role=role,
                       hidden_by="" if role else hidden_by(types))
        for player, role, types in report.deaths
    ]
    saves = [AnnouncedSave(player=player, attacker_types=list(types), saver=_saver(player, report))
             for player, types in report.saves]
    return NightAnnouncement(
        night=report.night,
        deaths=deaths,
        saves=saves,
        pick=report.pick,
        no_one_died=not deaths and not saves,
    )
