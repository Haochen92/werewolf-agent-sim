"""Room browser (slice 7): title, lock flag, and listing-TTL anchor on sessions.

All three are additive with server defaults, so pre-existing rows (solo games,
already-started rooms) backfill safely: unnamed, unlocked, stamped at migration time
— created_at only drives the GET /rooms browse filter, never correctness.

Revision ID: 0003
Revises: 0002
Create Date: 2026-08-20
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("sessions", sa.Column("room_name", sa.Text(), nullable=False,
                                        server_default=""))
    op.add_column("sessions", sa.Column("locked", sa.Boolean(), nullable=False,
                                        server_default=sa.false()))
    op.add_column("sessions", sa.Column("created_at", sa.TIMESTAMP(timezone=True),
                                        nullable=False, server_default=sa.func.now()))


def downgrade() -> None:
    op.drop_column("sessions", "created_at")
    op.drop_column("sessions", "locked")
    op.drop_column("sessions", "room_name")
