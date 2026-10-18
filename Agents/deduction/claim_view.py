"""The claims, typed for the engine (slice 9a; catalogue Table E's preamble): every role claim,
withdrawal and claimed night action so far, from the claim ledger (Agents/rules/claim_ledger.py), so
the engine reads the same fold the seats read (corrections kept as history, a night said before it
happened read as not said, the speaker's own field ahead of the summariser's transcription).

Public: built from the transcript and the day summaries, which every seat has. Today's claims come
from the speakers' own fields; the summary of a day exists only once it is over.
"""

from __future__ import annotations

from typing import Any, Iterable

from Agents.rules.claim_ledger import ClaimedAction, build_claim_ledger
from Agents.schemas.deduction import ActionClaim, PlayerClaimView, RoleClaim
from Agents.schemas.game_events import DayChannel, DaySummary

# Results that state an outcome, so the action went ahead (L13). A check's role result (an old
# summary) counts too.
_NOT_AN_OUTCOME = {"not_said", "roleblocked", ""}


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
        views.append(PlayerClaimView(
            player=player,
            roles=tuple(RoleClaim(day, role, kind == "retracted") for day, role, kind in p.roles),
            current_role=p.current_role,
            withdrawn_roles=tuple(role for _, role, kind in p.roles if kind == "retracted"),
            actions=tuple(actions),
        ))
    return views


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
