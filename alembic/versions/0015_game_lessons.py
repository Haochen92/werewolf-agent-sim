"""The lessons the offline extraction job writes back for a served game.

The owner's batch run reads served games' saved extraction inputs from the database and writes what
it extracted back (v8 decisions §16): the filled extraction case, which the learning tick folds into
the store, the de-halo record, and the payload the game's replay shows. ``games.lessons_extracted_at``
(0012) is set in the same transaction. A game is folded into the store at most once
(``folded_in_gen``).

Revision ID: 0015
Revises: 0014
Create Date: 2026-10-26
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "0015"
down_revision: Union[str, None] = "0014"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "game_lessons",
        sa.Column("game_id", sa.Text(), sa.ForeignKey("games.game_id", ondelete="CASCADE"), primary_key=True),
        sa.Column("run_name", sa.Text(), nullable=False),
        sa.Column("extraction_case", JSONB(), nullable=False),
        sa.Column("dehalo", JSONB(), nullable=True),
        sa.Column("replay", JSONB(), nullable=False),
        sa.Column("model_used", sa.Text(), nullable=False, server_default=""),
        sa.Column("extracted_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("folded_in_gen", sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("game_lessons")
