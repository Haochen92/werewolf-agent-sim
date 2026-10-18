"""Random claims for a random game (tests/factories/random_nights.py), true and false, for the truth
oracle of the joins with claims (slice 9b: catalogue F1, F2).

Every claim is a spoken line of today with the speaker's own field filled (DayChannel
claimed_night_actions), the way the claim ledger reads it. Truthful claims are read off the engine's
real night: a watch's or a follow's own list (whole, or a part of it: a named list is partial, L12),
a visit that went ahead, an action that went ahead. False claims alter those facts: a made-up
sighting or visit, a sighting of an attempt that a block cancelled, a sighting of a visit the living
Illusionist's conceal hid. A line built on a false claim is never checked against it; a certain line
must hold whatever the claims say. Role claims (`random_role_claims`, slice 10) are true or made up,
and some are withdrawn.
"""

from __future__ import annotations

import random

from Agents.schemas.deduction import PublicRecord
from Agents.schemas.game_events import DayChannel, DaySummary, SpokenNightAction
from tests.factories.random_nights import RandomGame, _every_visit

VISITING = ("investigate", "protect", "watch", "follow", "shoot", "kill", "sigil", "block")


def random_claims(rng: random.Random, game: RandomGame, snapshot: PublicRecord) -> tuple[list[DayChannel], int]:
    """Today's lines (today is the day after the snapshot's last night) and today's number."""
    last_night = max((a.night for a in snapshot.announcements), default=0)
    today = last_night + 1
    living = list(snapshot.living)
    claims: list[tuple[str, SpokenNightAction]] = []
    for night in range(1, last_night + 1):
        if night in game.nights and living:
            claims += _true_claims(rng, game, night, living) + _false_claims(rng, game, night, living)
    rng.shuffle(claims)
    lines = [DayChannel(day=today, seq=seq, player=speaker, message="(a claim)", claimed_night_actions=[action])
             for seq, (speaker, action) in enumerate(claims)]
    return lines, today


def _claim(night: int, action: str, target: str, seen=(), result: str = "not_said") -> SpokenNightAction:
    return SpokenNightAction(night=night, action=action, target=target, result=result, seen=list(seen))


def _true_claims(rng, game: RandomGame, night: int, living: list[str]) -> list[tuple[str, SpokenNightAction]]:
    claims = []
    resolved = game.nights[night]
    for record in game.records:
        if record.day != night or record.actor not in living or game.roles[record.actor] == "necromancer":
            continue
        if record.action in ("watch", "follow") and record.result == "seen" and rng.random() < 0.7:
            seen = list(record.seen)
            if seen and rng.random() < 0.3:
                seen = rng.sample(seen, rng.randint(1, len(seen)))  # a part of the list
            if seen:
                claims.append((record.actor, _claim(night, record.action, record.target, seen)))
        elif record.action in VISITING and record.result != "roleblocked" and record.target and rng.random() < 0.3:
            claims.append((record.actor, _claim(night, record.action, record.target, result=record.result)))
    for visitor, target in _every_visit(resolved):
        if visitor in living and visitor != target and rng.random() < 0.4:
            claims.append((visitor, _claim(night, "visit", target)))
    return claims


def _false_claims(rng, game: RandomGame, night: int, living: list[str]) -> list[tuple[str, SpokenNightAction]]:
    resolved = game.nights[night]
    everyone = list(game.roles)
    claims = []
    for _ in range(rng.randint(0, 3)):
        speaker, target = rng.choice(living), rng.choice(everyone)
        kind = rng.choice(["watch", "follow", "visit"])
        seen = rng.sample(everyone, rng.randint(1, 2)) if kind != "visit" else []
        claims.append((speaker, _claim(night, kind, target, seen)))
    for choice in resolved.choices:
        # A sighting of an attempt a block cancelled: the visit never happened.
        if choice.actor in resolved.outcome.blocked and choice.target and rng.random() < 0.5:
            claims.append((rng.choice(living), _claim(night, "watch", choice.target, [choice.actor])))
    for visit in _every_visit(resolved):
        # A sighting of a visit the living Illusionist's conceal hid: no watch could have seen it.
        if visit not in resolved.outcome.visits:
            claims.append((rng.choice(living), _claim(night, "watch", visit[1], [visit[0]])))
    return claims


def random_role_claims(rng, game: RandomGame, snapshot: PublicRecord, today: int) -> tuple[list[DayChannel], list[DaySummary], dict[str, str]]:
    """Today's role claims (slice 10: the premises of F4 and F5), true and false, and now and then a
    withdrawal: yesterday's summary has the player claim a role and withdraw it (the claim ledger's
    only source of a withdrawal). Returns the lines, the summaries, and each player's current role
    claim as these were written (the oracle's own account of "the current role claims")."""
    roles = sorted(set(game.roles.values()))
    lines: list[DayChannel] = []
    withdrawals: list[dict] = []
    current: dict[str, str] = {}
    for player in snapshot.living:
        draw = rng.random()
        if draw < 0.45:
            role = game.roles[player]
        elif draw < 0.65:
            role = rng.choice(roles)
        else:
            if draw < 0.8:
                role = rng.choice([game.roles[player], rng.choice(roles)])
                withdrawals += [{"player": player, "claimed_role": role, "kind": "claimed"},
                                {"player": player, "claimed_role": role, "kind": "retracted"}]
            continue
        current[player] = role
        lines.append(DayChannel(day=today, seq=1000 + len(lines), player=player, message="(a role claim)", claim=role))
    summaries = [DaySummary(day=today - 1, summary="(yesterday)", structured={"role_claims": withdrawals})] if withdrawals else []
    return lines, summaries, current


# --- slice 11: claims of every kind Table E compares --------------------------------------------------

RESULT_OF_RECORD = {"suspicious": "suspicious", "not_suspicious": "not_suspicious", "saved": "saved_from_attack",
                    "no_attack": "no_attack", "killed": "died", "immune": "survived", "hit": "died",
                    "miss": "no_effect"}
"""A record's result as a claim's result word (a vigilante's or a sigil's "saved" is read below)."""
ACTIONS = ("investigate", "protect", "watch", "follow", "shoot", "kill", "sigil", "block", "visit")
RESULTS = ("not_said", "suspicious", "not_suspicious", "saved_from_attack", "no_attack", "died", "survived",
           "no_visitors", "no_effect", "roleblocked")


def random_comparison_claims(rng: random.Random, game: RandomGame, snapshot: PublicRecord
                             ) -> tuple[list[DayChannel], list[DaySummary], int]:
    """Today's lines and yesterday's summary for the comparisons (slice 11: catalogue Table E): the
    claims of `random_claims`, then for every living player now and then a claim read off its own
    night (an action with its true result, only chosen, roleblocked, a whole sighting, a denial when it
    went nowhere), a made-up one of any kind (any action, target, the dead included, result and
    sighting, "no one" included), and role claims, true, made up or withdrawn
    (`random_role_claims`). Some claims are said yesterday (in the summary), the rest today."""
    lines, today = random_claims(rng, game, snapshot)
    role_lines, summaries, _ = random_role_claims(rng, game, snapshot, today)
    living = list(snapshot.living)
    everyone = list(game.roles)
    last_night = today - 1
    said: list[tuple[str, SpokenNightAction]] = []
    for night in range(1, last_night + 1):
        resolved = game.nights.get(night)
        if resolved is None:
            continue
        for player in living:
            draw = rng.random()
            if draw < 0.35:
                claim = _from_own_night(rng, game, resolved, player)
                if claim is not None:
                    said.append((player, claim))
            elif draw < 0.6:
                action = rng.choice((*ACTIONS, "no_action", "no_action"))
                target = "" if action == "no_action" and rng.random() < 0.6 else rng.choice(everyone)
                result = rng.choice(RESULTS)
                seen = rng.sample(everyone, rng.randint(0, 2)) if action in ("watch", "follow") else []
                if result == "no_visitors":
                    seen = []
                said.append((player, _claim(night, action, target, seen, result)))
    rng.shuffle(said)
    yesterday = [(player, claim) for player, claim in said if rng.random() < 0.3 and today > 2]
    for seq, (player, claim) in enumerate(said):
        if (player, claim) in yesterday:
            continue
        lines.append(DayChannel(day=today, seq=2000 + seq, player=player, message="(a claim)",
                                claimed_night_actions=[claim]))
    entries = [{"player": player, "claimed_role": "none",
                "night_actions": [{**claim.model_dump(), "night": claim.night}]} for player, claim in yesterday]
    if entries:
        summary = next((s for s in summaries if s.day == today - 1), None)
        if summary is None:
            summaries.append(DaySummary(day=today - 1, summary="(yesterday)", structured={"role_claims": entries}))
        else:
            summary.structured["role_claims"] += entries
    return lines + role_lines, summaries, today


def _from_own_night(rng, game: RandomGame, resolved, player: str) -> SpokenNightAction | None:
    """A claim read off what the player really did that night (not the Necromancer's: through a body,
    its words and its visits do not match)."""
    if game.roles[player] == "necromancer":
        return None
    night = resolved.night
    records = [r for r in resolved.records if r.actor == player]
    choices = [c for c in resolved.choices if c.actor == player and c.via is None]
    visits = [t for v, t in _every_visit(resolved) if v == player]
    if not choices and not visits:
        return _claim(night, "no_action", "")
    if not visits and rng.random() < 0.5:
        return _claim(night, "no_action", "") if rng.random() < 0.6 else _claim(night, "no_action", rng.choice(list(game.roles)))
    if records:
        record = rng.choice(records)
        action = "shoot" if record.action == "shoot" else record.action
        if action not in (*ACTIONS, "bet") or not record.target:
            return None
        if record.result == "roleblocked":  # said, or left unsaid (only chosen, by its words)
            return _claim(night, action, record.target, result="roleblocked" if rng.random() < 0.5 else "not_said")
        if rng.random() < 0.3:
            return _claim(night, action, record.target)  # only chosen, by its words
        if action in ("watch", "follow"):
            seen = list(record.seen)
            return _claim(night, action, record.target, seen, "no_visitors" if not seen else "not_said")
        result = RESULT_OF_RECORD.get(record.result, "not_said")
        if record.result == "saved":
            result = "saved_from_attack" if action == "protect" else "survived"
        return _claim(night, action, record.target, result=result)
    if visits:
        return _claim(night, "visit", rng.choice(visits))
    return None
