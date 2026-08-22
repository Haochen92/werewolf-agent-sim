"""SQLModel mappings for the unified game lifecycle and its event log."""

from datetime import datetime
from typing import Literal

from sqlalchemy import (
    TIMESTAMP,
    CheckConstraint,
    Column,
    ForeignKey,
    Index,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel

GameStatus = Literal["waiting", "running", "completed", "dropped"]

WAITING: GameStatus = "waiting"
RUNNING: GameStatus = "running"
COMPLETED: GameStatus = "completed"
DROPPED: GameStatus = "dropped"
RECOVERABLE_STATUSES: tuple[GameStatus, GameStatus] = (WAITING, RUNNING)


class GameRow(SQLModel, table=True):
    """One game identity from waiting room through permanent completed replay."""

    __tablename__ = "games"
    __table_args__ = (
        CheckConstraint(
            "status IN ('waiting', 'running', 'completed', 'dropped')",
            name="games_status_check",
        ),
        Index("games_status_idx", "status"),
        # Partial index for completed-game listing; live/dropped rows do not enter it.
        Index(
            "games_completed_at_idx",
            text("finished_at DESC"),
            postgresql_where=text("status = 'completed'"),
        ),
    )

    game_id: str = Field(sa_column=Column(Text, primary_key=True))
    status: GameStatus = Field(
        default=WAITING,
        sa_column=Column(String, nullable=False),
    )

    # Operational/recovery fields. They remain private because public DTOs never
    # expose them; the provider API key itself is never stored here.
    host_key: str = ""
    model: str = ""
    byok: bool = False
    seats: list[dict] = Field(
        default_factory=list,
        sa_column=Column(
            JSONB,
            nullable=False,
            server_default=text("'[]'::jsonb"),
        ),
    )
    human_players: list[str] = Field(default_factory=list,
                                     sa_column=Column(
                                         JSONB,
                                         nullable=False,
                                         server_default=text("'[]'::jsonb"),
                                     ))
    room_name: str = Field(
        default="",
        sa_column=Column(Text, nullable=False, server_default=""),
    )
    locked: bool = False
    error: str | None = Field(default=None, sa_column=Column(Text, nullable=True))

    created_at: datetime | None = Field(
        default=None,
        sa_column=Column(TIMESTAMP(timezone=True), nullable=False,
                         server_default=func.now()),
    )
    updated_at: datetime | None = Field(
        default=None,
        sa_column=Column(TIMESTAMP(timezone=True), nullable=False,
                         server_default=func.now()),
    )

    # Completion metadata. Null while waiting/running/dropped; populated in the
    # same operation that transitions a clean game to ``completed``.
    finished_at: datetime | None = Field(
        default=None,
        sa_column=Column(TIMESTAMP(timezone=True), nullable=True),
    )
    winner: str | None = None
    days: int | None = None
    n_events: int | None = None
    n_humans: int | None = None
    cast_role_counts: dict[str, int] | None = Field(
        default=None,
        sa_column=Column(JSONB, nullable=True),
    )


class EventRow(SQLModel, table=True):
    """One durable wire event in a game's ordered, permanent event log."""

    __tablename__ = "events"

    game_id: str = Field(sa_column=Column(
        Text,
        ForeignKey("games.game_id", ondelete="CASCADE"),
        primary_key=True,
    ))
    seq: int = Field(primary_key=True)
    payload: dict = Field(sa_column=Column(JSONB, nullable=False))
