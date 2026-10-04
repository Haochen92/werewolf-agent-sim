"""Read completed games and their normalized event logs as public replay DTOs."""

from sqlalchemy import func
from sqlmodel import select

from server.database_models.cast import GameCastRow
from server.database_models.game import COMPLETED, EventRow, GameRow
from server.db import Database
from server.game.cast import seat_number
from server.game.usage import average_call_seconds, game_cost
from server.schemas.replays import ReplayBase, ReplayGame


# What makes a game show up in the replay list: it finished cleanly and every summary
# field the list shows was written. The list and its total count use the same test.
_LISTED = (
    GameRow.status == COMPLETED,
    GameRow.finished_at.is_not(None),
    GameRow.winner.is_not(None),
    GameRow.days.is_not(None),
    GameRow.n_events.is_not(None),
    GameRow.n_humans.is_not(None),
    GameRow.cast_role_counts.is_not(None),
)


def _summary(row: GameRow) -> ReplayBase:
    """The row's public fields, plus the cost and call time worked out from its usage."""
    return ReplayBase.model_validate(row).model_copy(update={
        "cost_usd": game_cost(row.usage),
        "avg_call_seconds": average_call_seconds(row.usage, row.model),
    })


def average_costs(rows: list[tuple[str, dict | None]]) -> dict[str, tuple[float, int]]:
    """Per model, the mean cost of the games that have one, and how many that is. A game with
    no usage, or with a model the price table cannot price, is left out rather than counted."""
    costs: dict[str, list[float]] = {}
    for model, usage in rows:
        cost = game_cost(usage)
        if model and cost is not None:
            costs.setdefault(model, []).append(cost)
    return {m: (round(sum(c) / len(c), 4), len(c)) for m, c in costs.items()}


class ReplayArchiveNotConfigured(RuntimeError):
    """Raised when replay storage is disabled for this server process."""


class ReplayNotFound(LookupError):
    """Raised when no completed game is visible under the requested ID."""


class IncompleteReplay(RuntimeError):
    """Raised when completion metadata and the persisted event log disagree."""


class ReplayService:
    """Map private completed game rows into public replay DTOs."""

    def __init__(self, database: Database) -> None:
        self._database = database

    def _require_configured(self) -> None:
        if not self._database.configured:
            raise ReplayArchiveNotConfigured

    async def list_replays(self, *, limit: int, offset: int) -> list[ReplayBase]:
        self._require_configured()
        stmt = (
            select(GameRow)
            .where(*_LISTED)
            .order_by(GameRow.finished_at.desc())
            .limit(min(limit, 200))
            .offset(offset)
        )
        async with self._database.session() as session:
            rows = (await session.execute(stmt)).scalars().all()
        return [_summary(row) for row in rows]

    async def average_costs(self, recent: int = 500) -> dict[str, tuple[float, int]]:
        """Mean game cost per model over the most recent ``recent`` completed games with usage
        recorded (the model menu shows it). Empty when storage is off."""
        if not self._database.configured:
            return {}
        stmt = (
            select(GameRow.model, GameRow.usage)
            .where(*_LISTED, GameRow.usage.is_not(None))
            .order_by(GameRow.finished_at.desc())
            .limit(recent)
        )
        async with self._database.session() as session:
            rows = (await session.execute(stmt)).all()
        return average_costs([(model, usage) for model, usage in rows])

    async def count_replays(self) -> int:
        """How many games the list holds in all, across every page: the "N games" a
        browser shows under a page of them."""
        self._require_configured()
        stmt = select(func.count()).select_from(GameRow).where(*_LISTED)
        async with self._database.session() as session:
            return (await session.execute(stmt)).scalar_one()

    async def get_replay(self, game_id: str) -> ReplayGame:
        self._require_configured()
        async with self._database.session() as session:
            row = (
                await session.execute(
                    select(GameRow).where(
                        GameRow.game_id == game_id,
                        GameRow.status == COMPLETED,
                        GameRow.finished_at.is_not(None),
                        GameRow.winner.is_not(None),
                        GameRow.days.is_not(None),
                        GameRow.n_events.is_not(None),
                        GameRow.n_humans.is_not(None),
                        GameRow.cast_role_counts.is_not(None),
                    )
                )
            ).scalar_one_or_none()
            if row is None:
                raise ReplayNotFound(game_id)
            event_rows = (
                await session.execute(
                    select(EventRow)
                    .where(EventRow.game_id == game_id)
                    .order_by(EventRow.seq)
                )
            ).scalars().all()
            cast_rows = (
                await session.execute(
                    select(GameCastRow).where(GameCastRow.game_id == game_id)
                )
            ).scalars().all()
        # Count and contiguity: seq runs from 1 with no gaps, so the last must equal
        # the count. The write side checks the same at completion; this is the net
        # for rows completed before it did, or touched since.
        if len(event_rows) != row.n_events or (
                event_rows and event_rows[-1].seq != row.n_events):
            raise IncompleteReplay(game_id)
        summary = _summary(row)
        return ReplayGame(
            **summary.model_dump(),
            events=[event.payload for event in event_rows],
            cast=[r.character_id for r in sorted(cast_rows, key=lambda r: seat_number(r.seat))],
        )
