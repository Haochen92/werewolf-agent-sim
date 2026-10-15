"""The private night record: what each night actor did and what it may know of the result.

Pure, like the layer beside it: night resolution builds the records from the night's choices and
their outcome, and the hallucination bench rebuilds the same records for old games from their
stored targets. Each record says only what its actor could know: the public announcement, plus
its own action. The wolves also learn that an attack on an immune player failed (the public is
told nothing), as the vigilante does.

The record is also the source of the dead role's disclosure. There are no wills: when a town
player dies and the role is revealed, the moderator publishes what that role received each night
as a public fact (the owner's ruling, 2026-10-07). So beside the prose written to the actor, each
record carries a fixed result word and the names it learned, from which a third-person line is
composed that no player could have forged.
"""

from __future__ import annotations

from Agents.rules.night import is_pack_kill, visited_by, visitors_of
from Agents.schemas.game_events import NightActionRecord
from Agents.schemas.night import NightChoice, NightOutcome, NightVerdict
from Agents.schemas.roles import ROLE_SPECS, TOWN, side_of

_ATTACKER_PHRASE = {
    "wolves": "the wolves",
    "serial_killer": "the serial killer",
    "vigilante": "the vigilante",
    "sigilist": "a sigil",
    "reanimated_wolves": "a reanimated wolf",
    "reanimated_vigilante": "a reanimated vigilante",
    "reanimated_sigilist": "a reanimated sigil",
}

# The result words a record may carry, by action. The disclosure reads these, never the prose.
#   protect:     saved | no_attack
#   kill/shoot:  killed | saved | immune
#   hold_fire:   held
#   investigate: suspicious | not_suspicious   (the target is in `seen`)
#   watch, follow: seen            (the names are in `seen`; empty = no one)
#   sigil:       hit | saved | miss  (a quiet night and an immune attacker both read as a miss,
#                owner 2026-10-09: the sigilist learns only that the sigil had no effect)
#   block:       blocked | no_effect
#   conceal:     concealed | no_body  (the concealed role is in `seen`)
#   pick:        picked              (the side is in `seen`)
#   bet:         scored_1 | scored_2 | missed | self_bet
#   any action a block cancelled: roleblocked
# A necromancer's record carries the body's action, with the body in `seen` first.

PACK_ACTOR = "wolves"
"""The actor every pack kill is recorded under, so each wolf reads the pack's record."""


def _join(items: list[str]) -> str:
    if len(items) == 0:
        return ""
    if len(items) == 1:
        return items[0]
    return ", ".join(items[:-1]) + " and " + items[-1]


def _role_words(role: str) -> str:
    return role.replace("_", " ")


def _kill_outcome(target: str, verdict: NightVerdict | None, roles: dict[str, str], concealed: bool) -> str:
    """The result of a kill or a shot, as its actor learns it. An immune target is unharmed and
    the public hears nothing; which roles can be immune on which nights is in the rules."""
    if verdict == "killed":
        if concealed:
            return f"{target} died. Their role was concealed."
        return f"{target} died. They were a {_role_words(roles.get(target, 'unknown'))}."
    if verdict == "saved":
        return f"{target} survived: the healer saved them."
    return (
        f"{target} was unharmed: immune to night kills tonight. "
        "The public was told nothing about this attack."
    )


def _record_actor(choice: NightChoice) -> str:
    return PACK_ACTOR if is_pack_kill(choice) else choice.actor


def _record_of(choice: NightChoice, outcome: NightOutcome, roles: dict[str, str]) -> NightActionRecord:
    """One choice that went ahead, as its actor learns the result."""
    night = outcome.night
    target = choice.target
    actor = _record_actor(choice)
    action = "shoot" if (choice.kind == "kill" and choice.role == "vigilante") else choice.kind

    result = ""
    seen: list[str] = []
    outcome_text = ""

    if choice.kind == "protect":
        if outcome.verdicts.get(target) == "saved":
            attacker_types = []
            for attack in outcome.attacks_on[target]:
                attacker_types.append(_ATTACKER_PHRASE[attack.attacker_type])
            result = "saved"
            outcome_text = f"{target} was attacked by {_join(attacker_types)}, and your protection saved them."
        else:
            # Covers an attack on an immune player too: that attack is silent, so the healer
            # learns nothing more than the public does.
            result = "no_attack"
            outcome_text = f"No attack on {target} was announced."

    elif choice.kind == "hold_fire":
        result = "held"
        outcome_text = "You held your fire."

    elif choice.kind == "kill":
        verdict = outcome.verdicts.get(target)
        result = verdict or "killed"
        outcome_text = _kill_outcome(target, verdict, roles, target in outcome.concealed)
        if choice.via is not None and roles.get(choice.via) == "illusionist" and target in outcome.concealed:
            # The necromancer cleaned this body through the illusionist's, and learns the role.
            seen = [target]
            outcome_text = (f"{target} died, and you hid their role: they were a "
                            f"{_role_words(roles.get(target, 'unknown'))}.")

    elif choice.kind == "investigate":
        seen = [target]
        if target in outcome.suspicious:
            result = "suspicious"
            outcome_text = f"{target} reads Suspicious."
        else:
            result = "not_suspicious"
            outcome_text = f"{target} reads Not suspicious."

    elif choice.kind == "watch":
        # The watcher's own visit is not among the visitors it is told of.
        result = "seen"
        seen = [v for v in visitors_of(outcome, target) if v != (choice.via or choice.actor)]
        if seen:
            outcome_text = f"Tonight {target} was visited by {_join(seen)}."
        else:
            outcome_text = f"No one visited {target} tonight."

    elif choice.kind == "follow":
        result = "seen"
        seen = visited_by(outcome, target)
        if seen:
            outcome_text = f"Tonight {target} visited {_join(seen)}."
        else:
            outcome_text = f"{target} visited no one tonight."

    elif choice.kind == "sigil":
        if target in outcome.attackers:
            verdict = outcome.verdicts.get(target)
            if verdict == "killed":
                result = "hit"
                outcome_text = f"{target} attacked someone tonight, and your sigil struck them down."
            elif verdict == "immune":
                # An immune attacker (the serial killer, on this cast) reads exactly as a quiet
                # night: the "immune" record named it in one step (balance run, 2026-10-09; owner).
                result = "miss"
                outcome_text = "Your sigil had no effect."
            else:
                result = "saved"
                outcome_text = (
                    f"{target} attacked someone tonight, but the healer's protection saved them "
                    "from your sigil."
                )
        else:
            result = "miss"
            outcome_text = "Your sigil had no effect."

    elif choice.kind == "block":
        if target in outcome.blocked:
            result = "blocked"
            outcome_text = f"{target} was roleblocked tonight."
        else:
            result = "no_effect"
            outcome_text = f"Your block did not affect {target}."

    elif choice.kind == "conceal":
        if outcome.concealed:
            victim = outcome.concealed[0]
            victim_role = roles.get(victim, "unknown")
            result = "concealed"
            seen = [victim_role]
            outcome_text = f"You concealed {victim}'s body. They were a {_role_words(victim_role)}."
        else:
            result = "no_body"
            outcome_text = "The pack's victim did not die, so no body was concealed."

    elif choice.kind == "pick":
        result = "picked"
        seen = [target or ""]
        outcome_text = f"You picked {_role_words(target or '')}. The morning will announce the pick, not you."

    elif choice.kind == "bet":
        if target == choice.actor:
            result = "self_bet"
            outcome_text = "You bet on yourself: an attack on you tonight fails, and nothing is scored."
        else:
            bet = next((b for b in outcome.bets if b.actor == choice.actor), None)
            points = bet.points if bet else 0
            if points == 2:
                result = "scored_2"
                outcome_text = f"{target} died and was a {_role_words(choice.role_named or '')}: two points."
            elif points == 1:
                result = "scored_1"
                outcome_text = f"{target} died: one point." + (
                    f" They were not a {_role_words(choice.role_named)}." if choice.role_named else ""
                )
            else:
                result = "missed"
                outcome_text = f"{target} did not die tonight: no points."

    if choice.via is not None:
        seen = [choice.via, *seen]
        outcome_text = f"Through {choice.via}'s body: " + outcome_text

    return NightActionRecord(
        day=night, actor=actor, action=action, target=target,
        outcome=outcome_text, result=result, seen=seen,
    )


def night_action_records(
    choices: list[NightChoice], outcome: NightOutcome, roles: dict[str, str]
) -> list[NightActionRecord]:
    """The night's records, one per choice, in choice order. A choice a block cancelled is
    recorded as roleblocked: its actor is told, and learns nothing else."""
    records: list[NightActionRecord] = []
    for choice in choices:
        if choice.actor in outcome.blocked:
            action = "shoot" if (choice.kind == "kill" and choice.role == "vigilante") else choice.kind
            records.append(NightActionRecord(
                day=outcome.night, actor=_record_actor(choice), action=action, target=choice.target,
                outcome="You were roleblocked: your action was not carried out and you learned nothing tonight.",
                result="roleblocked", seen=[],
            ))
            continue
        records.append(_record_of(choice, outcome, roles))
    return records


def own_night_actions(records: list[NightActionRecord], player_id: str, role: str) -> list[NightActionRecord]:
    """The records one player may see: its own, and the pack's kills for a wolf."""
    spec = ROLE_SPECS.get(role)
    own = [r for r in records if r.actor == player_id]
    if spec is not None and spec.pack:
        own = [r for r in records if r.actor in (player_id, PACK_ACTOR)]
    return own


# --- the dead role's disclosure -------------------------------------------------------------

def _disclosed(record: NightActionRecord) -> str:
    """One record in the third person, from its result word and names, never its prose."""
    target = record.target
    if record.result == "roleblocked":
        return "was roleblocked"
    if record.action == "protect":
        if record.result == "saved":
            return f"protected {target}, who was attacked and saved"
        return f"protected {target}; no attack on them was announced"
    if record.action == "hold_fire":
        return "held fire"
    if record.action in ("shoot", "kill"):
        if record.result == "killed":
            return f"shot {target}, who died"
        if record.result == "saved":
            return f"shot {target}, who was saved"
        return f"shot {target}, who was unharmed"
    if record.action == "investigate":
        if record.result == "suspicious":
            return f"checked {target}: Suspicious"
        return f"checked {target}: Not suspicious"
    if record.action == "watch":
        if record.seen:
            return f"watched {target}; saw {_join(record.seen)} visit them"
        return f"watched {target}; saw no one"
    if record.action == "follow":
        if record.seen:
            return f"followed {target}; they visited {_join(record.seen)}"
        return f"followed {target}; they visited no one"
    if record.action == "sigil":
        if record.result == "hit":
            return f"set a sigil on {target}, who attacked and was struck down"
        if record.result == "saved":
            return f"set a sigil on {target}, who attacked and was saved"
        return f"set a sigil on {target}; it had no effect"
    return f"{record.action} {target}"


def disclosure(player: str, role: str, records: list[NightActionRecord]) -> str | None:
    """The dead town role's record, as the moderator publishes it at the reveal: every night's
    action and what it received, in night order. None for a role off the town side, a role with
    nothing on record, or a role the registry does not know."""
    if role not in ROLE_SPECS or side_of(role) != TOWN:
        return None
    entries: list[tuple[int, str]] = []
    for record in records:
        if record.actor == player:
            entries.append((record.day, _disclosed(record)))
    if not entries:
        return None
    entries.sort(key=lambda entry: entry[0])
    parts: list[str] = []
    for night, text in entries:
        parts.append(f"night {night}, {text}")
    return f"The record of {player}, the {_role_words(role)}: " + "; ".join(parts) + "."
