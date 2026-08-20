"""Live-session durability: the sessions and events tables.

The third fact source — the LangGraph checkpoint tables — is owned and created by
AsyncPostgresSaver.setup(), deliberately outside alembic (env.py's include_object
already ignores foreign tables).

Revision ID: 0002
Revises: 0001
Create Date: 2026-08-20
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "sessions",
        sa.Column("game_id", sa.Text(), primary_key=True),
        sa.Column("phase", sa.String(), nullable=False),
        sa.Column("host_key", sa.String(), nullable=False, server_default=""),
        sa.Column("model", sa.String(), nullable=False, server_default=""),
        sa.Column("byok", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("seats", JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("human_players", JSONB(), nullable=False,
                  server_default=sa.text("'[]'::jsonb")),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False,
                  server_default=sa.func.now()),
    )
    # Boot recovery's exact query: the open rows.
    op.create_index("sessions_phase_idx", "sessions", ["phase"])
    op.create_table(
        "events",
        sa.Column("game_id", sa.Text(), primary_key=True),
        sa.Column("seq", sa.Integer(), primary_key=True),
        sa.Column("payload", JSONB(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("events")
    op.drop_index("sessions_phase_idx", table_name="sessions")
    op.drop_table("sessions")
