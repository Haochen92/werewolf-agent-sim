"""The private night record: what each night actor did and what it may know of the result.

Pure, like the resolution kernel beside it: night resolution builds the records from the night's
targets and verdicts, and the hallucination bench rebuilds the same records for old games from
their stored targets. Each record says only what its actor could know: the public announcement,
plus its own action. The wolves also learn that an attack on the serial killer failed (the public
is told nothing), as the vigilante does.
"""

from __future__ import annotations

from Agents.rules.resolution import AttackerType, NightVerdict
from Agents.schemas.game_events import NightActionRecord

_ATTACKER_PHRASE = {"wolves": "the wolves", "serial_killer": "the serial killer", "vigilante": "the vigilante"}


def _join(items: list[str]) -> str:
    return items[0] if len(items) == 1 else ", ".join(items[:-1]) + " and " + items[-1]


def _kill_outcome(target: str, verdict: NightVerdict | None, roles: dict[str, str]) -> str:
    """The result of a kill or a shot, as its actor learns it."""
    if verdict == "killed":
        return f"{target} died. They were a {roles.get(target, 'unknown').replace('_', ' ')}."
    if verdict == "saved":
        return f"{target} survived: the healer saved them."
    return (
        f"{target} was unharmed: immune to night kills, which confirms {target} is the serial "
        "killer. The public was told nothing about this attack."
    )


def night_action_records(
    day: int,
    *,
    wolves_target: str | None,
    healer_target: str | None,
    serial_killer_target: str | None,
    vigilante_target: str | None,
    attacks_on: dict[str, list[AttackerType]],
    verdicts: dict[str, NightVerdict],
    roles: dict[str, str],
    healer: str | None,
    serial_killer: str | None,
    vigilante: str | None,
    vigilante_held_fire: bool = False,
) -> list[NightActionRecord]:
    """The night's records, one per action taken. `healer` / `serial_killer` / `vigilante` are
    the living actors at nightfall (None when absent); `vigilante_held_fire` is True when the
    vigilante was asked and chose not to shoot."""
    records: list[NightActionRecord] = []
    if healer and healer_target:
        if verdicts.get(healer_target) == "saved":
            phrase = _join([_ATTACKER_PHRASE[a] for a in attacks_on[healer_target]])
            outcome = f"{healer_target} was attacked by {phrase}, and your protection saved them."
        else:
            # Covers an attack on the immune serial killer too: that attack is silent, so the
            # healer learns nothing more than the public does.
            outcome = f"No attack on {healer_target} was announced."
        records.append(NightActionRecord(day=day, actor=healer, action="protect",
                                         target=healer_target, outcome=outcome))
    if vigilante and vigilante_target:
        records.append(NightActionRecord(
            day=day, actor=vigilante, action="shoot", target=vigilante_target,
            outcome=_kill_outcome(vigilante_target, verdicts.get(vigilante_target), roles)))
    elif vigilante and vigilante_held_fire:
        records.append(NightActionRecord(day=day, actor=vigilante, action="hold_fire", target=None,
                                         outcome="You held your fire."))
    if serial_killer and serial_killer_target:
        records.append(NightActionRecord(
            day=day, actor=serial_killer, action="kill", target=serial_killer_target,
            outcome=_kill_outcome(serial_killer_target, verdicts.get(serial_killer_target), roles)))
    if wolves_target:
        records.append(NightActionRecord(
            day=day, actor="wolves", action="kill", target=wolves_target,
            outcome=_kill_outcome(wolves_target, verdicts.get(wolves_target), roles)))
    return records


def own_night_actions(records: list[NightActionRecord], player_id: str, role: str) -> list[NightActionRecord]:
    """The records one player may see: its own, or the pack's for a wolf."""
    actor = "wolves" if role == "wolf" else player_id
    return [r for r in records if r.actor == actor]
