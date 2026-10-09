"""The claim ledger: every role claim and claimed night action made in the day discussion, folded
across days, with exact checks against the game master's record.

A role claim comes from the speaker: the claim field of the discussion output rides the spoken
entry (DayChannel.claim), so who claimed what on which day is never misattributed. The day
summariser transcribes the claimed night actions, the retractions and the plans
(DaySummaryOutputV4.role_claims); its transcription of the role itself is the cross-check: taken
only for a player who set no claim that day (a human's line has no field), dropped where it
disagrees with the field. The rest is code: each player's history is kept (a changed claim keeps
the earlier one), and each claim is checked against engine facts: revealed roles, announced saves
and deaths, the cast and the rules.
A plan said in the day for that night is set beside what the player later says they did, as fact
("on day 2 said they planned to investigate player_2"), never as a broken promise.
The ledger is never stored. Every prompt rebuilds it from the day summaries and the dead roster, so
a role revealed overnight shows up in the next prompt's checks.

A check states a fact ("player_7 was revealed as wolf"), never what it means. Where the record fits
more than one reading it says nothing: a shot player who lived may have been saved, or may be the
serial killer, whose survival is never announced.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from Agents.schemas.game_events import DayChannel, DaySummary, DeathRecord
from Agents.schemas.roles import ROLE_SPECS, WOLVES, roles as ROLES

# The engine's own announcement wording (night_resolution): a save, and the night it belongs to.
_SAVE = re.compile(r"(\S+) was attacked by [^!.]*? but was saved by the healer")
_NIGHT = re.compile(r"^Night of day (\d+):")

_VERBS = {"investigate": "checked", "protect": "protected", "shoot": "shot", "kill": "attacked",
          "watch": "watched", "follow": "followed", "sigil": "set a sigil on", "block": "blocked",
          "conceal": "concealed", "bet": "bet on", "pick": "picked"}
_NOUNS = {"investigate": "check", "protect": "protection", "shoot": "shot", "kill": "kill",
          "watch": "watch", "follow": "trail", "sigil": "sigil", "block": "block",
          "conceal": "conceal", "bet": "bet", "pick": "pick"}
PLAN_VERBS = {"investigate": "check", "protect": "protect", "shoot": "shoot", "kill": "attack",
              "watch": "watch", "follow": "follow", "sigil": "set a sigil on", "block": "block",
              "conceal": "conceal", "bet": "bet on", "pick": "pick"}
_SAYS = {
    "suspicious": "says they read Suspicious",
    "not_suspicious": "says they read Not suspicious",
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
    reason: str = ""
    """The player's reason for doing something other than what they planned, if they gave one."""


@dataclass
class PlayerClaims:
    roles: list[tuple[int, str, str]] = field(default_factory=list)
    """(day, role, "claimed" | "retracted"), one entry per change; a repeated claim adds nothing."""
    actions: dict[tuple, ClaimedAction] = field(default_factory=dict)
    """Keyed by (night, action), or (0, action, target) when no night was given."""
    plans: dict[tuple[int, str], str] = field(default_factory=dict)
    """(night, action) -> target the player said on that day they would act on that night."""

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


def spoken_claims(messages: list[DayChannel]) -> dict[int, list[tuple[str, str]]]:
    """The role claims the speakers made, by day: (player, role) in the order spoken. A held or
    passed entry claimed nothing the table heard."""
    by_day: dict[int, list[tuple[str, str]]] = {}
    for m in sorted(messages, key=lambda m: (m.day, m.seq)):
        if m.passed or m.claim == "none" or not m.claim:
            continue
        by_day.setdefault(m.day, []).append((m.player, m.claim))
    return by_day


def build_claim_ledger(discussion: list[DaySummary], messages: list[DayChannel] = ()) -> dict[str, PlayerClaims]:
    """Each player's claims across days, in the order players first claimed. The role lines come
    from the speakers' own claim fields (``messages``); the summariser's role claims fill in for
    a player who set none that day, and its night actions, retractions and plans are taken as
    transcribed."""
    ledger: dict[str, PlayerClaims] = {}
    spoken = spoken_claims(list(messages))
    summaries = {s.day: s for s in discussion}
    for day in sorted({*spoken, *summaries}):
        claimed_today: set[str] = set()
        for player, role in spoken.get(day, []):
            claimed_today.add(player)
            p = ledger.setdefault(player, PlayerClaims())
            if role != p.current_role:
                p.roles.append((day, role, "claimed"))
        s = summaries.get(day)
        if s is None:
            continue
        for c in (s.structured or {}).get("role_claims") or []:
            player, role = c.get("player"), c.get("claimed_role")
            if not player or not role:
                continue
            kind, actions = _entry(c)
            p = ledger.setdefault(player, PlayerClaims())
            if kind == "retracted":
                if p.roles and player not in claimed_today:
                    p.roles.append((s.day, role, "retracted"))
            elif role != p.current_role and player not in claimed_today:
                p.roles.append((s.day, role, "claimed"))
            for a in actions:
                if a.get("target"):
                    _add_action(p, ClaimedAction(int(a.get("night") or 0), a.get("action", ""), a["target"],
                                                 a.get("result", ""), s.day, reason=a.get("reason") or ""))
            for plan in c.get("planned_actions") or []:  # said on day N about night N
                if plan.get("action") in PLAN_VERBS and plan.get("target"):
                    p.plans[(s.day, plan["action"])] = plan["target"]
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
        old.reason = old.reason or new.reason
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


@dataclass(frozen=True)
class Check:
    text: str
    fits: bool | None
    """True: the record agrees with the claim; False: it disagrees, or the claim breaks a rule;
    None: a fact beside the claim that is neither (a plan whose target died)."""


@dataclass
class LedgerEntry:
    """One line under a player: a claimed night action, or a plan they never said they carried out."""

    night: int
    action: str
    target: str
    claim: ClaimedAction | None
    """None for a plan the player never reported on."""
    planned: str | None = None
    """The target the player said on that night's day they would act on, if they did."""
    checks: list[Check] = field(default_factory=list)


@dataclass
class LedgerPlayer:
    player: str
    claims: PlayerClaims
    checks: list[Check]
    entries: list[LedgerEntry]


def role_checks(player: str, p: PlayerClaims, ledger: dict[str, PlayerClaims], facts: RecordFacts) -> list[Check]:
    notes = []
    claimed = [role for _, role, kind in p.roles if kind == "claimed"]
    death = facts.dead.get(player)
    if death and death.role and claimed:
        fits = death.role == claimed[-1]
        notes.append(Check(f"Record: revealed as {_word(death.role)} when they {_when(death)}"
                           + (", as claimed." if fits else f", not {_word(claimed[-1])}."), fits))
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
            notes.append(Check(f"Record: the game has {cap} {_word(role)}, and " + " and ".join(parts) + ".", False))
    return notes


def action_checks(player: str, a: ClaimedAction, facts: RecordFacts) -> list[Check]:
    notes = []
    if a.also:
        notes.append(Check(f"Rules: one {_NOUNS[a.action]} a night.", False))
    if a.action == "protect" and a.target == player:
        notes.append(Check("Rules: the healer cannot protect themselves.", False))
    death = facts.dead.get(a.target)
    if a.action == "investigate" and death and death.role and a.result in (*ROLES, "not_a_wolf", "suspicious", "not_suspicious"):
        revealed_wolf = ROLE_SPECS.get(death.role) is not None and ROLE_SPECS[death.role].side == WOLVES
        if a.result in ROLES:
            fits = death.role == a.result
        elif a.result == "suspicious":
            # A Suspicious read fits a wolf; a necromancer reads Suspicious only on its attack nights.
            fits = revealed_wolf or death.role == "necromancer"
        else:
            fits = not revealed_wolf
        notes.append(Check(f"Record: {a.target} was revealed as {_word(death.role)}" + (", as claimed." if fits else "."),
                           fits))
    if not a.night or a.night not in facts.resolved_nights:
        return notes
    if a.action == "protect":
        if (a.night, a.target) in facts.saves:
            notes.append(Check(f"Record: {a.target} was attacked and saved by the healer that night.", True))
        elif a.result == "saved_from_attack":
            notes.append(Check(f"Record: no save of {a.target} was announced that night.", False))
    elif a.action in ("shoot", "kill"):
        if death and death.phase == "night" and death.day == a.night:
            notes.append(Check(f"Record: {a.target} died that night.", True))
        elif a.result == "died":
            notes.append(Check(f"Record: {a.target} did not die that night.", False))
    return notes


def plan_checks(action: str, target: str, night: int, facts: RecordFacts) -> list[Check]:
    """A planned protection whose target died that night: the healer blocks any night kill."""
    death = facts.dead.get(target)
    if action == "protect" and death and death.phase == "night" and death.day == night:
        return [Check(f"Record: {target} died that night.", None)]
    return []


def ledger_rows(summaries: list[DaySummary], dead_roster=(), cast_role_counts=None,
                messages: list[DayChannel] = ()) -> list[LedgerPlayer]:
    """The ledger with its checks: a row per player who claimed, in the order they first claimed,
    each with its night actions and unreported plans in night order. ``messages`` are the spoken
    entries whose claim fields make the role lines (the days the ledger covers)."""
    ledger = build_claim_ledger([s for s in summaries if s.source != "game_master"], messages)
    facts = record_facts(summaries, dead_roster, cast_role_counts)
    rows = []
    for player, p in ledger.items():
        plans = dict(p.plans)
        entries = []
        for a in p.actions.values():
            planned = plans.pop((a.night, a.action), None) if a.night else None
            entries.append(LedgerEntry(a.night, a.action, a.target, a, planned, action_checks(player, a, facts)))
        for (night, action), target in plans.items():
            entries.append(LedgerEntry(night, action, target, None, target, plan_checks(action, target, night, facts)))
        entries.sort(key=lambda e: (e.night or 99, e.claim.day if e.claim else e.night))
        rows.append(LedgerPlayer(player, p, role_checks(player, p, ledger, facts), entries))
    return rows


def entry_text(e: LedgerEntry) -> str:
    a = e.claim
    if a is None:
        return f"Night {e.night}: on day {e.night} said they planned to {PLAN_VERBS[e.action]} {e.target}."
    text = action_text(a)
    if a.earlier:
        text += f" (changed on day {a.day}; earlier: {'; '.join(a.earlier)})"
    if a.also:
        text += f" (on day {a.day} also named: {'; '.join(a.also)})"
    if e.planned == a.target:
        text += f" (planned on day {a.night})"
    text += "."
    if e.planned and e.planned != a.target:
        text += (f" On day {a.night} said they planned to {PLAN_VERBS[a.action]} {e.planned}"
                 + (f"; reason given on day {a.day}: {a.reason.rstrip('.')}." if a.reason else "."))
    return text


def format_claim_ledger(summaries: list[DaySummary], dead_roster=(), cast_role_counts=None,
                        messages: list[DayChannel] = ()) -> str:
    """The ledger as prompt text: a line per player (role history and checks), then a line per
    claimed night action or unreported plan (with what it replaced, and its checks). "" when
    nobody has claimed."""
    lines = []
    for row in ledger_rows(summaries, dead_roster, cast_role_counts, messages):
        lines.append(" ".join([f"{row.player}: {role_history(row.claims)}.", *(c.text for c in row.checks)]))
        lines += ["  " + " ".join([entry_text(e), *(c.text for c in e.checks)]) for e in row.entries]
    return "\n".join(lines)


def revealed_tag(player: str, dead: dict[str, DeathRecord]) -> str:
    """`player`, plus its revealed role once it is dead: "player_8 (revealed wolf, voted out day 3)"."""
    d = dead.get(player)
    if not d or not d.role:
        return player
    when = f"killed night {d.day}" if d.phase == "night" else f"voted out day {d.day}"
    return f"{player} (revealed {_word(d.role)}, {when})"
