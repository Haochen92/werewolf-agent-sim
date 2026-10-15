"""The prompts a served game sent, kept so an offline job can check them for leaks.

The batch runner checks every game's prompts for private information reaching the wrong player;
the website's games were never checked. A finished game now saves its prompts, its players' private
reads and its final state here, compressed, and the leak audit (server/housekeeping/leak_audit.py)
records its verdict on the same row. Games before this migration have no row.

Revision ID: 0013
Revises: 0012
Create Date: 2026-10-14
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "0013"
down_revision: Union[str, None] = "0012"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "prompt_captures",
        sa.Column("game_id", sa.Text(),
                  sa.ForeignKey("games.game_id", ondelete="CASCADE"), primary_key=True),
        sa.Column("captured_at", sa.TIMESTAMP(timezone=True), nullable=False,
                  server_default=sa.func.now()),
        sa.Column("capture", sa.LargeBinary(), nullable=False),
        sa.Column("n_prompts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("partial", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("audited_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("leaks", JSONB(), nullable=True),
    )
    op.create_index("prompt_captures_unaudited_idx", "prompt_captures", ["captured_at"],
                    postgresql_where=sa.text("audited_at IS NULL"))


def downgrade() -> None:
    op.drop_index("prompt_captures_unaudited_idx", table_name="prompt_captures")
    op.drop_table("prompt_captures")
