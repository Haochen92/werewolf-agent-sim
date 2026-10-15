"""SQLModel mappings for the puppet cast: the character catalogue, and which character
stood at each seat of a game."""

from datetime import datetime

from sqlalchemy import (
    TIMESTAMP,
    Boolean,
    Column,
    ForeignKey,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlmodel import Field, SQLModel


class CharacterRow(SQLModel, table=True):
    """One puppet in the catalogue. The id is the slug the sprites are filed under and
    never changes; the display name may. A retired character keeps its row, since the
    games it stood in still name it."""

    __tablename__ = "characters"

    id: str = Field(sa_column=Column(Text, primary_key=True))
    display_name: str = Field(sa_column=Column(Text, nullable=False))
    retired: bool = Field(
        default=False,
        sa_column=Column(Boolean, nullable=False, server_default=text("false")),
    )
    added_at: datetime | None = Field(
        default=None,
        sa_column=Column(TIMESTAMP(timezone=True), nullable=False,
                         server_default=func.now()),
    )


class GameCastRow(SQLModel, table=True):
    """One seat's puppet in one game, written when the engine deals the seats. A game
    names each character at most once, which the unique constraint enforces, and only
    characters the catalogue knows, which the foreign key enforces. Games recorded
    before this table existed have no rows here; the client falls back to its old
    deterministic cast for them."""

    __tablename__ = "game_cast"
    __table_args__ = (
        UniqueConstraint("game_id", "character_id", name="game_cast_one_puppet_each"),
    )

    game_id: str = Field(sa_column=Column(
        Text, ForeignKey("games.game_id", ondelete="CASCADE"), primary_key=True))
    seat: str = Field(sa_column=Column(Text, primary_key=True))
    """The engine seat, ``player_1`` to ``player_9``."""
    character_id: str = Field(sa_column=Column(
        Text, ForeignKey("characters.id"), nullable=False))
    chosen: bool = Field(
        default=False,
        sa_column=Column(Boolean, nullable=False, server_default=text("false")),
    )
    """True when a player picked this puppet, False when the house drew it."""
