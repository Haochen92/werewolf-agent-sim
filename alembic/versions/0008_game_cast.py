"""The puppet cast, written down with each game.

Which plush character stands at which seat used to be recomputed by the browser from a
hash of the game id over a fixed list, so adding a character would have re-dealt every
old replay. Now the server draws the cast when the engine deals the seats and stores it:
``characters`` is the catalogue (the slug the sprites are filed under, a display name
that may change, and a retired flag), and ``game_cast`` holds one row per seat per game.
A game names each character at most once, and only characters the catalogue knows.
Games recorded before this migration have no cast rows; the client keeps its old
deterministic cast for them, over the eleven characters seeded here.

Revision ID: 0008
Revises: 0007
Create Date: 2026-10-03
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0008"
down_revision: Union[str, None] = "0007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# The eleven puppets that existed before casts were stored. Later characters are seeded
# by their own migrations, so this list stays as it was on the day.
SEED = [
    ("owl", "Owl"),
    ("hare", "Hare"),
    ("cat", "Cat"),
    ("badger", "Badger"),
    ("cyclops", "Cyclops"),
    ("threeEyes", "Three-Eyes"),
    ("dragon", "Dragon"),
    ("onion", "Onion"),
    ("whale", "Whale"),
    ("polarBear", "Polar Bear"),
    ("shade", "Songbird"),
]


def upgrade() -> None:
    characters = op.create_table(
        "characters",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column("display_name", sa.Text(), nullable=False),
        sa.Column("retired", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("added_at", sa.TIMESTAMP(timezone=True), nullable=False,
                  server_default=sa.func.now()),
    )
    op.bulk_insert(characters, [{"id": i, "display_name": n} for i, n in SEED])
    op.create_table(
        "game_cast",
        sa.Column("game_id", sa.Text(),
                  sa.ForeignKey("games.game_id", ondelete="CASCADE"), primary_key=True),
        sa.Column("seat", sa.Text(), primary_key=True),
        sa.Column("character_id", sa.Text(), sa.ForeignKey("characters.id"), nullable=False),
        sa.Column("chosen", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.UniqueConstraint("game_id", "character_id", name="game_cast_one_puppet_each"),
    )


def downgrade() -> None:
    op.drop_table("game_cast")
    op.drop_table("characters")
