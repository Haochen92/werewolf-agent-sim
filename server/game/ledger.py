"""The claim ledger as the agents read it each morning, rebuilt from a game's event log.

Agents never see a past day's discussion; they read the day summaries, and in them the claim
ledger: every role claim and claimed night action, checked against the game master's record
(Agents/rules/claim_ledger.py). The engine rebuilds it for every prompt and never stores it, so
the browser gets it here, rebuilt the same way from the same public facts: the structured day
summaries, the game master's night announcements, the deaths and the cast census. Every input
is public, so anyone may ask for it, mid-game too.
"""

from __future__ import annotations

from Agents.rules.claim_ledger import LedgerPlayer, entry_text, ledger_rows, role_history
from Agents.schemas.game_events import DaySummary, DeathRecord
from server.schemas import events as ev
from server.schemas.ledger import LedgerCheck, LedgerDay, LedgerEntryView, LedgerPlayerView


def ledger_days(events: list[ev.DurableEvent]) -> list[LedgerDay]:
    """The ledger agents read on each morning that followed a summarised day, oldest first. The
    ledger of day N holds the claims of days before N, checked against the deaths announced by
    the morning of day N."""
    cast: dict[str, int] = {}
    summaries: list[DaySummary] = []
    deaths: list[DeathRecord] = []
    mornings: set[int] = set()
    for e in events:
        if e.type == "phase_change" and e.phase == "day":
            mornings.add(e.day)
        elif e.type == "game_started":
            cast = dict(e.cast_role_counts)
        elif e.type == "gm_message":
            summaries.append(DaySummary(day=e.day, summary=e.text.strip(), source="game_master"))
        elif e.type == "day_summary_structured":
            summaries.append(DaySummary(day=e.day, summary="", structured=e.data))
        elif e.type == "night_result":
            deaths += [DeathRecord(player=d.player, role=d.role, day=e.day, phase="night") for d in e.deaths]
        elif e.type == "lynch_result" and e.player:
            deaths.append(DeathRecord(player=e.player, role=e.role or "", day=e.day, phase="day"))
    # The summary of the day the game ended on is never read: no morning follows it.
    days = sorted({s.day + 1 for s in summaries if s.source != "game_master"} & mornings)
    out = []
    for day in days:
        before = [s for s in summaries if s.day < day]
        dead = [d for d in deaths if d.day < day]
        rows = ledger_rows(before, dead, cast)
        out.append(LedgerDay(day=day, players=[_player_view(r) for r in rows]))
    return out


def _player_view(row: LedgerPlayer) -> LedgerPlayerView:
    return LedgerPlayerView(
        player=row.player,
        history=role_history(row.claims),
        roles=[{"day": day, "role": role, "kind": kind} for day, role, kind in row.claims.roles],
        checks=[LedgerCheck(text=c.text, fits=c.fits) for c in row.checks],
        entries=[
            LedgerEntryView(
                night=e.night,
                action=e.action,
                target=e.target,
                result=e.claim.result if e.claim else "",
                said_on_day=e.claim.day if e.claim else e.night,
                reported=e.claim is not None,
                earlier=list(e.claim.earlier) if e.claim else [],
                also=list(e.claim.also) if e.claim else [],
                planned=e.planned,
                reason=e.claim.reason if e.claim else "",
                text=entry_text(e),
                checks=[LedgerCheck(text=c.text, fits=c.fits) for c in e.checks],
            )
            for e in row.entries
        ],
    )
