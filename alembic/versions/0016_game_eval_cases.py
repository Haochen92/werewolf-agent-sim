"""The evaluation cases a served game produced, kept so served play can be evaluated later.

A batch game writes its evaluation cases to a file; a served game built the same cases in memory
and discarded them when it ended, so the only copy was the one attached to its trace. A finished
game now saves them here, compressed, one row per game. The server deletes a row after its shelf
life (``EVAL_CASES_TTL_DAYS``). Games before this migration have no row.

Revision ID: 0016
Revises: 0015
Create Date: 2026-11-20
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0016"
down_revision: Union[str, None] = "0015"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "game_eval_cases",
        sa.Column("game_id", sa.Text(),
                  sa.ForeignKey("games.game_id", ondelete="CASCADE"), primary_key=True),
        sa.Column("saved_at", sa.TIMESTAMP(timezone=True), nullable=False,
                  server_default=sa.func.now()),
        sa.Column("cases", sa.LargeBinary(), nullable=False),
        sa.Column("n_cases", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("partial", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("record_format", sa.Text(), nullable=False),
    )
    op.create_index("game_eval_cases_saved_at_idx", "game_eval_cases", ["saved_at"])


def downgrade() -> None:
    op.drop_index("game_eval_cases_saved_at_idx", table_name="game_eval_cases")
    op.drop_table("game_eval_cases")
