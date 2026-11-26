"""The claims, typed for the engine (slice 9a; catalogue Table E's preamble): every role claim,
withdrawal and claimed night action so far, from the claim ledger (Agents/rules/claim_ledger.py), so
the engine reads the same fold the seats read (corrections kept as history, a night said before it
happened read as not said, the speaker's own field ahead of the summariser's transcription).

Public: built from the transcript and the day summaries, which every seat has. Today's claims come
from the speakers' own fields; the summary of a day exists only once it is over.

A player who names no role but claims actions only one role takes ("I held fire") gets that role as
an implied claim (catalogue slice 13b), so every row reads it as a claim.
"""

from __future__ import annotations

from typing import Any, Iterable

from Agents.rules.claim_ledger import ClaimedAction, build_claim_ledger
from Agents.schemas.deduction import ActionClaim, PlayerClaimView, RoleClaim
from Agents.schemas.game_events import DayChannel, DaySummary

# Results that state an outcome, so the action went ahead (L13). A check's role result (an old
# summary) counts too.
_NOT_AN_OUTCOME = {"not_said", "roleblocked", ""}

ACTION_ROLE = {"investigate": "investigator", "protect": "healer", "watch": "sentinel", "follow": "trailseer",
               "shoot": "vigilante", "sigil": "sigilist", "block": "chanteuse"}
"""The role an action claim implies, when the claimant names none."""
KEPT_ROLE = {"held_fire": "vigilante", "kept_check": "investigator", "kept_watch": "sentinel", "kept_sigil": "sigilist"}
"""The role a held-back action implies: only the Vigilante holds fire (owner, 2026-10-18: a vigilante
who said it held fire was read as unclaimed, and the conditional on the role claims named it)."""


def implied_role(claim: ActionClaim) -> str | None:
    """The role this one claimed action implies, or None (a bare visit, an attack, a plain denial)."""
    if claim.action == "no_action":
        return KEPT_ROLE.get(claim.result)
    return ACTION_ROLE.get(claim.action)


def claims_view(day_channel: Iterable[DayChannel | dict], day_summaries: Iterable[DaySummary | dict]) -> list[PlayerClaimView]:
    """Every player who has claimed, in the order they first claimed. A stored game carries the
    transcript and the summaries as plain dicts, a live game as models."""
    messages = [m if isinstance(m, DayChannel) else DayChannel.model_validate(m) for m in day_channel]
    summaries = [s if isinstance(s, DaySummary) else DaySummary.model_validate(s) for s in day_summaries]
    ledger = build_claim_ledger([s for s in summaries if s.source != "game_master"], messages)
    views = []
    for player, p in ledger.items():
        actions = []
        for a in p.actions.values():
            history = tuple(_action(player, old, latest=False) for old in a.earlier_claims)
            actions += [*history, _action(player, a, latest=True, history=history)]
            actions += [_action(player, also, latest=True) for also in a.also_claims]
        actions.sort(key=lambda c: (c.night or 99, c.day))
        roles = tuple(RoleClaim(day, role, kind == "retracted") for day, role, kind in p.roles)
        withdrawn = tuple(role for _, role, kind in p.roles if kind == "retracted")
        current = p.current_role
        implied = _implied_claim(actions, withdrawn) if current is None else None
        if implied is not None:
            roles, current = (*roles, implied), implied.role
        views.append(PlayerClaimView(
            player=player,
            roles=roles,
            current_role=current,
            withdrawn_roles=withdrawn,
            actions=tuple(actions),
        ))
    return views


def _implied_claim(actions: list[ActionClaim], withdrawn: tuple[str, ...]) -> RoleClaim | None:
    """The role claim a player's current action claims make when it names no role: every one that
    implies a role implies the same one, and the player has not withdrawn it."""
    implying = [a for a in actions if a.latest and implied_role(a) is not None]
    roles = {implied_role(a) for a in implying}
    if len(roles) != 1:
        return None
    role = roles.pop()
    if role in withdrawn:
        return None
    return RoleClaim(min(a.day for a in implying), role, False, implied_by=tuple(implying))


def _action(player: str, a: ClaimedAction, latest: bool, history: tuple[ActionClaim, ...] = ()) -> ActionClaim:
    return ActionClaim(
        claimant=player,
        day=a.day,
        night=a.night,
        action=a.action,
        target=a.target,
        result=a.result,
        seen=tuple(a.seen),
        latest=latest,
        blocked=a.result == "roleblocked",
        # A claimed visit says it went ahead (owner 2026-10-17), with what was done unknown.
        completed=(a.action == "visit" and a.result != "roleblocked")
        or (a.action not in ("", "no_action") and a.result not in _NOT_AN_OUTCOME),
        seen_complete=a.action in ("watch", "follow") and a.result == "no_visitors",
        source="summary" if a.said_in is None else "speaker",
        history=history,
    )


def claims_from_payload(payload: dict[str, Any]) -> list[PlayerClaimView]:
    """The claims on a seat's payload (day and night payloads both carry the transcript and the
    summaries)."""
    return claims_view(payload.get("day_channel", []), payload.get("day_summaries", []))
