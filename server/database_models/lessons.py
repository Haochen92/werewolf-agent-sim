"""The lessons the offline extraction job wrote from a served game."""

from datetime import datetime

from sqlalchemy import TIMESTAMP, Column, ForeignKey, Integer, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel


class GameLessonsRow(SQLModel, table=True):
    """One served game's extracted lessons: written by the owner's offline batch run
    (``scripts/extract_batch.py --from-db``), read by the game's replay and by the learning tick."""

    __tablename__ = "game_lessons"

    game_id: str = Field(sa_column=Column(
        Text, ForeignKey("games.game_id", ondelete="CASCADE"), primary_key=True))
    run_name: str = Field(sa_column=Column(Text, nullable=False))
    """The extraction run that wrote these lessons (its folder under batch_results/extraction_runs/)."""
    extraction_case: dict = Field(sa_column=Column(JSONB, nullable=False))
    """The game's extraction case with its observations filled in, verdicts as de-halo left them:
    what the learning tick folds into the store."""
    dehalo: dict | None = Field(default=None, sa_column=Column(JSONB, nullable=True))
    """The de-halo pass's record for the game; null when the pass was skipped or failed."""
    replay: dict = Field(sa_column=Column(JSONB, nullable=False))
    """What the game taught, as the replay shows it (a ``memory_extracted`` event's payload)."""
    model_used: str = Field(default="", sa_column=Column(Text, nullable=False, server_default=""))
    extracted_at: datetime = Field(sa_column=Column(
        TIMESTAMP(timezone=True), nullable=False, server_default=func.now()))
    folded_in_gen: int | None = Field(default=None, sa_column=Column(Integer, nullable=True))
    """The learning tick generation that folded these observations into the store; null until then,
    so a game is never folded twice."""
