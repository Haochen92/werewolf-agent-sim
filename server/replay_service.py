"""Read completed games and their normalized event logs as public replay DTOs."""

from sqlmodel import select

from server.database_models.game import COMPLETED, EventRow, GameRow
from server.db import Database
from server.schemas.replays import ReplayBase, ReplayGame


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
            .where(
                GameRow.status == COMPLETED,
                GameRow.finished_at.is_not(None),
                GameRow.winner.is_not(None),
                GameRow.days.is_not(None),
                GameRow.n_events.is_not(None),
                GameRow.n_humans.is_not(None),
                GameRow.cast_role_counts.is_not(None),
            )
            .order_by(GameRow.finished_at.desc())
            .limit(min(limit, 200))
            .offset(offset)
        )
        async with self._database.session() as session:
            rows = (await session.execute(stmt)).scalars().all()
        return [ReplayBase.model_validate(row) for row in rows]

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
        if len(event_rows) != row.n_events:
            raise IncompleteReplay(game_id)
        summary = ReplayBase.model_validate(row)
        return ReplayGame(
            **summary.model_dump(),
            events=[event.payload for event in event_rows],
        )
