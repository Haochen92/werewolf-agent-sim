"""What a game can teach, kept for the offline extraction job, and when its lessons were written.

Lessons are no longer extracted while a game runs (owner's ruling 2026-10-12): the game saves its
extraction input when it completes and an offline batch job writes the lessons later, recording
when. Games recorded before these columns have neither.

Revision ID: 0012
Revises: 0011
Create Date: 2026-10-12
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "0012"
down_revision: Union[str, None] = "0011"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("games", sa.Column("extraction_input", JSONB(), nullable=True))
    op.add_column("games", sa.Column("lessons_extracted_at", sa.TIMESTAMP(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("games", "lessons_extracted_at")
    op.drop_column("games", "extraction_input")
