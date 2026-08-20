"""Create the replay archive table.

Hand-written first revision (no live DB needed to author it); later revisions may use
--autogenerate against server.replays models — env.py's include_object keeps the shared
database's other tables (memory tick, LangGraph checkpoints) out of alembic's reach.

Revision ID: 0001
Revises:
Create Date: 2026-08-20
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "replays",
        sa.Column("game_id", sa.Text(), primary_key=True),
        sa.Column("finished_at", sa.TIMESTAMP(timezone=True), nullable=False,
                  server_default=sa.func.now()),
        sa.Column("winner", sa.String(), nullable=False),
        sa.Column("days", sa.Integer(), nullable=False),
        sa.Column("n_events", sa.Integer(), nullable=False),
        sa.Column("n_humans", sa.Integer(), nullable=False),
        sa.Column("cast_role_counts", JSONB(), nullable=False),
        sa.Column("events", JSONB(), nullable=False),
    )
    # The browse endpoint's exact ordering.
    op.create_index("replays_finished_at_idx", "replays", [sa.text("finished_at DESC")])


def downgrade() -> None:
    op.drop_index("replays_finished_at_idx", table_name="replays")
    op.drop_table("replays")
