"""SQLModel mapping for the prompts a served game sent, kept for the offline leak audit."""

from datetime import datetime

from sqlalchemy import (
    TIMESTAMP,
    Boolean,
    Column,
    ForeignKey,
    Index,
    Integer,
    LargeBinary,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel


class PromptCaptureRow(SQLModel, table=True):
    """One finished game's prompts, private reads and final state, compressed, with the leak
    audit's verdict once it has run. A table of its own, not columns on ``games``: the blob is
    large and the game listings read whole ``games`` rows."""

    __tablename__ = "prompt_captures"
    __table_args__ = (
        # The audit's default pass reads only what it has not audited yet.
        Index("prompt_captures_unaudited_idx", "captured_at",
              postgresql_where=text("audited_at IS NULL")),
    )

    game_id: str = Field(sa_column=Column(
        Text, ForeignKey("games.game_id", ondelete="CASCADE"), primary_key=True))
    captured_at: datetime | None = Field(
        default=None,
        sa_column=Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now()),
    )
    """When the game ended and its capture was written."""
    capture: bytes = Field(sa_column=Column(LargeBinary, nullable=False))
    """A gzip-compressed JSON ``GameCapture`` (server/schemas/leak_audit.py)."""
    n_prompts: int = Field(default=0, sa_column=Column(Integer, nullable=False, server_default="0"))
    partial: bool = Field(
        default=False,
        sa_column=Column(Boolean, nullable=False, server_default=text("false")),
    )
    """The game resumed after a restart, so the prompts before it are missing."""
    audited_at: datetime | None = Field(
        default=None, sa_column=Column(TIMESTAMP(timezone=True), nullable=True))
    """When the leak audit last checked this game; null until it has."""
    leaks: list[str] | None = Field(default=None, sa_column=Column(JSONB, nullable=True))
    """The audit's findings, one line per leak; an empty list is a clean game."""
