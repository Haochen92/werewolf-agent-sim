"""SQLModel mapping for the evaluation cases a served game produced."""

from datetime import datetime

from sqlalchemy import TIMESTAMP, Boolean, Column, ForeignKey, Index, Integer, LargeBinary, Text, func, text
from sqlmodel import Field, SQLModel


class GameEvalCasesRow(SQLModel, table=True):
    """One finished game's evaluation cases, compressed. A table of its own, not a column on
    ``games``: the blob is large and the game listings read whole ``games`` rows. Rows are
    deleted after a shelf life (``EVAL_CASES_TTL_DAYS``), so the table does not grow forever."""

    __tablename__ = "game_eval_cases"
    __table_args__ = (
        # The retention pass and the export both select by when a row was saved.
        Index("game_eval_cases_saved_at_idx", "saved_at"),
    )

    game_id: str = Field(sa_column=Column(
        Text, ForeignKey("games.game_id", ondelete="CASCADE"), primary_key=True))
    saved_at: datetime | None = Field(
        default=None,
        sa_column=Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now()),
    )
    """When the game ended and its cases were written."""
    cases: bytes = Field(sa_column=Column(LargeBinary, nullable=False))
    """Gzip-compressed JSON lines, one case record per line (server/storage/eval_cases.py)."""
    n_cases: int = Field(default=0, sa_column=Column(Integer, nullable=False, server_default="0"))
    partial: bool = Field(
        default=False,
        sa_column=Column(Boolean, nullable=False, server_default=text("false")),
    )
    """The game resumed after a restart, so the cases from before it are missing."""
    record_format: str = Field(sa_column=Column(Text, nullable=False))
    """The layout of one line, so a reader does not misread a row written by older code."""
