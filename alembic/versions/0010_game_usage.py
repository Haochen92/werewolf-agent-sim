"""The tokens a game spent and how long its model calls took, per model and UTC hour.

Saved as the game runs, so a replay can show what the game cost and how long the AI took
per call. The cost itself is not stored: it is worked out from these counts and the price
table when the replay is read. Games recorded before this column have no counts.

Revision ID: 0010
Revises: 0009
Create Date: 2026-10-04
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "0010"
down_revision: Union[str, None] = "0009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("games", sa.Column("usage", JSONB(), nullable=True))


def downgrade() -> None:
    op.drop_column("games", "usage")
