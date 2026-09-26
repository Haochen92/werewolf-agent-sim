"""The phase a finished game ended in, kept on its row for the replay list.

A game ends in the day, at the vote, or at night. The replay list shows it next to the
day count ("ended on night 5"), and reading it off the row saves opening every game's
event log to find out. New games fill it in when they complete. This migration fills it
in for games that finished before the column existed, from the last phase change in
each one's stored events; a game with no phase change at all keeps it empty.

Revision ID: 0007
Revises: 0006
Create Date: 2026-09-26
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0007"
down_revision: Union[str, None] = "0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("games", sa.Column("ended_phase", sa.String(), nullable=True))
    op.execute("""
        UPDATE games AS game
        SET ended_phase = last_change.phase
        FROM (
            SELECT DISTINCT ON (game_id) game_id, payload ->> 'phase' AS phase
            FROM events
            WHERE payload ->> 'type' = 'phase_change'
            ORDER BY game_id, seq DESC
        ) AS last_change
        WHERE last_change.game_id = game.game_id
          AND game.status = 'completed'
    """)


def downgrade() -> None:
    op.drop_column("games", "ended_phase")
