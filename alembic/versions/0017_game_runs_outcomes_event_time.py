"""What ran a game, which of its turns were not its model's own, and when each event was saved.

Three additions that let a served game be explained from its own rows:

- ``games.runs``: one entry per run of the game's task (a game resumed after a restart has
  several), each with the trace id, the start time, whether it was a recovery, and the runtime
  fingerprint: the code version, the prompt hash and the models. Before this, a served game
  stored neither its trace id nor the build that played it.
- ``games.turn_outcomes``: the turns decided by the rescue model or given a default by the
  engine, with counts, and how many cached engine steps were replayed. In the events such a
  move looks like any other.
- ``events.saved_at``: when the event's row was written. The log had order and no time. Rows
  from before this migration keep null: their time is not known.

Revision ID: 0017
Revises: 0016
Create Date: 2026-11-20
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "0017"
down_revision: Union[str, None] = "0016"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("games", sa.Column("runs", JSONB(), nullable=True))
    op.add_column("games", sa.Column("turn_outcomes", JSONB(), nullable=True))
    # Added without a default so existing rows stay null, then given one for new rows.
    op.add_column("events", sa.Column("saved_at", sa.TIMESTAMP(timezone=True), nullable=True))
    op.alter_column("events", "saved_at", server_default=sa.func.now())


def downgrade() -> None:
    op.drop_column("events", "saved_at")
    op.drop_column("games", "turn_outcomes")
    op.drop_column("games", "runs")
