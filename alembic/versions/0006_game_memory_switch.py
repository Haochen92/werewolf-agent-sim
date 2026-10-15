"""The per-game AI-memory switch: whether the AI seats consulted past-game lessons.

Recorded on the row so a game rebuilt after a restart keeps the setting it was started
with, and so a replay can say whether memory was on. Games recorded before this column
existed ran memory-off, which is what the default says.

Revision ID: 0006
Revises: 0005
Create Date: 2026-09-17
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0006"
down_revision: Union[str, None] = "0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "games",
        sa.Column("memory", sa.Boolean(), nullable=False, server_default=sa.false()),
    )


def downgrade() -> None:
    op.drop_column("games", "memory")
