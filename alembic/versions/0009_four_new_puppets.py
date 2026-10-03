"""Four more puppets: the kitsune, the mushroom, the lion cub and the automaton.

A character exists in the catalogue exactly when its sprites ship, so these rows arrive
with the frontend's sprites for the four. Old games are untouched: they name only the
eleven seeded by 0008, and the client's legacy cast for games without stored casts
draws from that frozen eleven, never from this list.

Revision ID: 0009
Revises: 0008
Create Date: 2026-10-03
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0009"
down_revision: Union[str, None] = "0008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SEED = [
    ("kitsune", "Kitsune"),
    ("mushroom", "Mushroom"),
    ("lionCub", "Lion Cub"),
    ("automaton", "Automaton"),
]

characters = sa.table(
    "characters",
    sa.column("id", sa.Text()),
    sa.column("display_name", sa.Text()),
)


def upgrade() -> None:
    op.bulk_insert(characters, [{"id": i, "display_name": n} for i, n in SEED])


def downgrade() -> None:
    op.execute(characters.delete().where(characters.c.id.in_([i for i, _ in SEED])))
