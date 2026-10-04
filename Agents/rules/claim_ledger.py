"""The claim ledger: every role claim and claimed night action made in the day discussion, folded
across days, with exact checks against the game master's record.

The day summariser only transcribes what was claimed (DaySummaryOutputV4.role_claims). The rest is
code: each player's history is kept (a changed claim keeps the earlier one), and each claim is
checked against engine facts: revealed roles, announced saves and deaths, the cast and the rules.
The ledger is never stored. Every prompt rebuilds it from the day summaries and the dead roster, so
a role revealed overnight shows up in the next prompt's checks.

A check states a fact ("player_7 was revealed as wolf"), never what it means. Where the record fits
more than one reading it says nothing: a shot player who lived may have been saved, or may be the
serial killer, whose survival is never announced.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from Agents.schemas.game_events import DaySummary, DeathRecord
from Agents.schemas.roles import roles as ROLES

# The engine's own announcement wording (night_resolution): a save, and the night it belongs to.
_SAVE = re.compile(r"(\S+) was attacked by [^!.]*? but was saved by the healer")
_NIGHT = re.compile(r"^Night of day (\d+):")

_VERBS = {"investigate": "investigated", "protect": "protected", "shoot": "shot", "kill": "attacked"}
_NOUNS = {"investigate": "investigation", "protect": "protection", "shoot": "shot", "kill": "kill"}
_SAYS = {
    "saved_from_attack": "says they saved them from an attack",
    "no_attack": "says there was no attack",
    "died": "says they died",
    "survived": "says they survived",
}


@dataclass
class ClaimedAction:
    night: int
    """The night the player says it happened; 0 when they did not say."""
    action: str
    """investigate / protect / shoot / kill; "" for a v3 summary's free-text result (never checked)."""
    target: str
    result: str
    day: int
    """The day the player said it."""
    earlier: list[str] = field(default_factory=list)
    """What the player said about the same night before changing it, oldest first."""
    also: list[str] = field(default_factory=list)
    """Other targets the player named for the same action and night on the same day."""


@dataclass
class PlayerClaims:
    roles: list[tuple[int, str, str]] = field(default_factory=list)
    """(day, role, "claimed" | "retracted"), one entry per change; a repeated claim adds nothing."""
    actions: dict[tuple, ClaimedAction] = field(default_factory=dict)
    """Keyed by (night, action), or (0, action, target) when no night was given."""

    @property
    def current_role(self) -> str | None:
        """The role the player claims now; None if they never did or withdrew it."""
        return self.roles[-1][1] if self.roles and self.roles[-1][2] == "claimed" else None


@dataclass(frozen=True)
class RecordFacts:
    """The engine facts a claim is checked against, all public."""

    dead: dict[str, DeathRecord]
    saves: set[tuple[int, str]]
    """(night, player) for every announced healer save."""
    resolved_nights: set[int]
    """Nights whose outcome has been announced."""
    role_counts: dict[str, int]
    """The public cast census; {} when unknown (then no claim is checked against it)."""


def record_facts(summaries: list[DaySummary], dead_roster=(), cast_role_counts=None) -> RecordFacts:
    saves, nights = set(), set()
    for s in summaries:
        if s.source != "game_master" or not (m := _NIGHT.match(s.summary.strip())):
            continue
        night = int(m.group(1))
        nights.add(night)
        saves |= {(night, p) for p in _SAVE.findall(s.summary)}
    return RecordFacts({d.player: d for d in dead_roster or []}, saves, nights, dict(cast_role_counts or {}))


def _entry(c: dict) -> tuple[str, list[dict]]:
    """(kind, night actions) of one stored role claim: v4 as written; a v3 claim's status and
    free-text results mapped onto it; a v1/v2 claim has neither."""
    kind = c.get("kind") or ("retracted" if c.get("status") == "retracted" else "claimed")
    actions = c.get("night_actions")
    if actions is None:
        actions = [{"night": r.get("night") or 0, "action": "", "target": r.get("target", ""),
                    "result": r.get("result", "")} for r in c.get("claimed_results") or []]
    return kind, actions


def build_claim_ledger(discussion: list[DaySummary]) -> dict[str, PlayerClaims]:
    """Each player's claims across days, in the order players first claimed."""
    ledger: dict[str, PlayerClaims] = {}
    for s in sorted(discussion, key=lambda s: s.day):
        for c in (s.structured or {}).get("role_claims") or []:
            player, role = c.get("player"), c.get("claimed_role")
            if not player or not role:
                continue
            kind, actions = _entry(c)
            p = ledger.setdefault(player, PlayerClaims())
            if kind == "retracted":
                if p.roles:
                    p.roles.append((s.day, role, "retracted"))
            elif role != p.current_role:
                p.roles.append((s.day, role, "claimed"))
            for a in actions:
                if a.get("target"):
                    _add_action(p, ClaimedAction(int(a.get("night") or 0), a.get("action", ""), a["target"],
                                                 a.get("result", ""), s.day))
    return ledger


def _same_claim(old: ClaimedAction, new: ClaimedAction) -> bool:
    return old.target == new.target and new.result in (old.result, "not_said")


def _add_action(p: PlayerClaims, new: ClaimedAction) -> None:
    same = [k for k, a in p.actions.items() if a.action == new.action and _same_claim(a, new)]
    if not new.night and same:
        return  # repeated without its night: the earlier entry already says it
    for k in same:  # a claim first made without its night, now dated
        if k[0] == 0:
            if new.result == "not_said":
                new.result = p.actions[k].result
            del p.actions[k]
    key = (new.night, new.action) if new.night else (0, new.action, new.target)
    old = p.actions.get(key)
    if old and _same_claim(old, new):
        return  # a repeat
    if old and new.action and old.day == new.day and old.target != new.target:
        new.earlier, new.also = old.earlier, [*old.also, action_text(old)]  # two targets named the same day
    elif old and not (old.target == new.target and old.result == "not_said"):
        new.earlier = [*old.earlier, *old.also, action_text(old)]  # a change; filling in a result is not one
    p.actions[key] = new


def _word(role: str) -> str:
    return role.replace("_", " ")


def action_text(a: ClaimedAction) -> str:
    night = f"Night {a.night}" if a.night else "Night not stated"
    if not a.action:
        return f"{night}: {a.target} {a.result}"
    text = f"{night}: {_VERBS[a.action]} {a.target}"
    if a.action == "investigate" and (a.result in ROLES or a.result == "not_a_wolf"):
        text += f", result: {_word(a.result) if a.result in ROLES else 'not a wolf'}"
    elif a.result in _SAYS:
        text += f", {_SAYS[a.result]}"
    return text


def role_history(p: PlayerClaims) -> str:
    parts = []
    for i, (day, role, kind) in enumerate(p.roles):
        verb = "retracted" if kind == "retracted" else ("claimed" if i == 0 else "then claimed")
        parts.append(f"{verb} {_word(role)} (day {day})")
    return ", ".join(parts)


def _when(d: DeathRecord) -> str:
    return f"died on night {d.day}" if d.phase == "night" else f"were voted out on day {d.day}"


def _names(players: list[str]) -> str:
    return " and ".join(players) if len(players) < 3 else ", ".join(players[:-1]) + " and " + players[-1]


def role_checks(player: str, p: PlayerClaims, ledger: dict[str, PlayerClaims], facts: RecordFacts) -> list[str]:
    notes = []
    claimed = [role for _, role, kind in p.roles if kind == "claimed"]
    death = facts.dead.get(player)
    if death and death.role and claimed:
        fits = death.role == claimed[-1]
        notes.append(f"Record: revealed as {_word(death.role)} when they {_when(death)}"
                     + (", as claimed." if fits else f", not {_word(claimed[-1])}."))
    role = p.current_role
    if role and not death and facts.role_counts:
        rivals = [q for q, c in ledger.items() if q != player and c.current_role == role and q not in facts.dead]
        revealed = [d.player for d in facts.dead.values() if d.role == role]
        cap = facts.role_counts.get(role, 0)
        if 1 + len(rivals) + len(revealed) > cap:
            parts = []
            if rivals:
                parts.append(f"{_names(rivals)} also claim{'s' if len(rivals) == 1 else ''} it")
            if revealed:
                parts.append(f"{_names(revealed)} {'was' if len(revealed) == 1 else 'were'} revealed as {_word(role)}")
            notes.append(f"Record: the game has {cap} {_word(role)}, and " + " and ".join(parts) + ".")
    return notes


def action_checks(player: str, a: ClaimedAction, facts: RecordFacts) -> list[str]:
    notes = []
    if a.also:
        notes.append(f"Rules: one {_NOUNS[a.action]} a night.")
    if a.action == "protect" and a.target == player:
        notes.append("Rules: the healer cannot protect themselves.")
    death = facts.dead.get(a.target)
    if a.action == "investigate" and death and death.role and (a.result in ROLES or a.result == "not_a_wolf"):
        fits = death.role == a.result or (a.result == "not_a_wolf" and death.role != "wolf")
        notes.append(f"Record: {a.target} was revealed as {_word(death.role)}" + (", as claimed." if fits else "."))
    if not a.night or a.night not in facts.resolved_nights:
        return notes
    if a.action == "protect":
        if (a.night, a.target) in facts.saves:
            notes.append(f"Record: {a.target} was attacked and saved by the healer that night.")
        elif a.result == "saved_from_attack":
            notes.append(f"Record: no save of {a.target} was announced that night.")
    elif a.action in ("shoot", "kill"):
        if death and death.phase == "night" and death.day == a.night:
            notes.append(f"Record: {a.target} died that night.")
        elif a.result == "died":
            notes.append(f"Record: {a.target} did not die that night.")
    return notes


def format_claim_ledger(summaries: list[DaySummary], dead_roster=(), cast_role_counts=None) -> str:
    """The ledger as prompt text: a line per player (role history and checks), then a line per
    claimed night action (with what it replaced, and its checks). "" when nobody has claimed."""
    ledger = build_claim_ledger([s for s in summaries if s.source != "game_master"])
    if not ledger:
        return ""
    facts = record_facts(summaries, dead_roster, cast_role_counts)
    lines = []
    for player, p in ledger.items():
        lines.append(" ".join([f"{player}: {role_history(p)}.", *role_checks(player, p, ledger, facts)]))
        for a in sorted(p.actions.values(), key=lambda a: (a.night or 99, a.day)):
            text = "  " + action_text(a)
            if a.earlier:
                text += f" (changed on day {a.day}; earlier: {'; '.join(a.earlier)})"
            if a.also:
                text += f" (on day {a.day} also named: {'; '.join(a.also)})"
            lines.append(" ".join([text + ".", *action_checks(player, a, facts)]))
    return "\n".join(lines)


def revealed_tag(player: str, dead: dict[str, DeathRecord]) -> str:
    """`player`, plus its revealed role once it is dead: "player_8 (revealed wolf, voted out day 3)"."""
    d = dead.get(player)
    if not d or not d.role:
        return player
    when = f"killed night {d.day}" if d.phase == "night" else f"voted out day {d.day}"
    return f"{player} (revealed {_word(d.role)}, {when})"
