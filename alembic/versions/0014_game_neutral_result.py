"""How a finished game's neutral fared, kept on its row for the replay list.

A ten-seat game deals one neutral (the speculator or the fortune teller), which wins or loses
beside whichever side wins the game. The replay list filters and marks games by it, and reading
it off the row saves opening every game's event log. New games fill it in when they complete.
This migration fills it in for games that finished before the column existed, from the result
their game-over event already carries; a nine-seat game dealt no neutral and keeps it empty.

Revision ID: 0014
Revises: 0013
Create Date: 2026-10-15
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0014"
down_revision: Union[str, None] = "0013"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("games", sa.Column("neutral_result", sa.Text(), nullable=True))
    op.execute("""
        UPDATE games AS game
        SET neutral_result = over.payload ->> 'neutral_result'
        FROM events AS over
        WHERE over.game_id = game.game_id
          AND over.payload ->> 'type' = 'game_over'
          AND game.status = 'completed'
    """)


def downgrade() -> None:
    op.drop_column("games", "neutral_result")
