"""Unify live sessions and completed replays under one game identity.

The migration is data-preserving:

* ``sessions`` becomes ``games`` and gains completion metadata.
* archived replay metadata is merged into the corresponding game row;
* replay JSON arrays are expanded into the normalized ``events`` table;
* every event log is given a parent before the foreign key is installed;
* only then is the redundant ``replays`` table removed.

Revision ID: 0004
Revises: 0003
Create Date: 2026-08-22
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.rename_table("sessions", "games")
    op.alter_column("games", "phase", new_column_name="status")
    op.execute("ALTER INDEX sessions_phase_idx RENAME TO games_status_idx")

    op.add_column("games", sa.Column(
        "finished_at", sa.TIMESTAMP(timezone=True), nullable=True,
    ))
    op.add_column("games", sa.Column("winner", sa.String(), nullable=True))
    op.add_column("games", sa.Column("days", sa.Integer(), nullable=True))
    op.add_column("games", sa.Column("n_events", sa.Integer(), nullable=True))
    op.add_column("games", sa.Column("n_humans", sa.Integer(), nullable=True))
    op.add_column("games", sa.Column("cast_role_counts", JSONB(), nullable=True))

    op.execute("""
        UPDATE games
        SET status = CASE status
            WHEN 'finished' THEN 'completed'
            WHEN 'dead' THEN 'dropped'
            ELSE status
        END,
        finished_at = CASE
            WHEN status = 'finished' THEN updated_at
            ELSE finished_at
        END
    """)

    # A replay can predate live-session durability, so insert any missing parent
    # before merging metadata into rows that already exist.
    op.execute("""
        INSERT INTO games (
            game_id, status, finished_at, winner, days, n_events,
            n_humans, cast_role_counts
        )
        SELECT
            game_id, 'completed', finished_at, winner, days, n_events,
            n_humans, cast_role_counts
        FROM replays
        ON CONFLICT (game_id) DO UPDATE SET
            status = 'completed',
            finished_at = EXCLUDED.finished_at,
            winner = EXCLUDED.winner,
            days = EXCLUDED.days,
            n_events = EXCLUDED.n_events,
            n_humans = EXCLUDED.n_humans,
            cast_role_counts = EXCLUDED.cast_role_counts
    """)

    # The payload already contains the canonical seq. ON CONFLICT preserves the
    # incrementally-written EventRow if both durability paths saw the same game.
    op.execute("""
        INSERT INTO events (game_id, seq, payload)
        SELECT
            replay.game_id,
            (event.payload ->> 'seq')::integer,
            event.payload
        FROM replays AS replay
        CROSS JOIN LATERAL jsonb_array_elements(replay.events) AS event(payload)
        ON CONFLICT (game_id, seq) DO NOTHING
    """)

    # Defensive preservation for any pre-FK event rows whose session write failed.
    op.execute("""
        INSERT INTO games (game_id, status, error)
        SELECT DISTINCT event.game_id, 'dropped',
               'orphaned event log discovered during schema migration'
        FROM events AS event
        LEFT JOIN games AS game ON game.game_id = event.game_id
        WHERE game.game_id IS NULL
        ON CONFLICT (game_id) DO NOTHING
    """)

    op.create_check_constraint(
        "games_status_check",
        "games",
        "status IN ('waiting', 'running', 'completed', 'dropped')",
    )
    op.create_foreign_key(
        "events_game_id_fkey",
        "events",
        "games",
        ["game_id"],
        ["game_id"],
        ondelete="CASCADE",
    )
    op.create_index(
        "games_completed_at_idx",
        "games",
        [sa.text("finished_at DESC")],
        postgresql_where=sa.text("status = 'completed'"),
    )
    op.drop_table("replays")


def downgrade() -> None:
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
    op.create_index(
        "replays_finished_at_idx", "replays", [sa.text("finished_at DESC")],
    )
    op.execute("""
        INSERT INTO replays (
            game_id, finished_at, winner, days, n_events,
            n_humans, cast_role_counts, events
        )
        SELECT
            game.game_id,
            game.finished_at,
            game.winner,
            game.days,
            game.n_events,
            game.n_humans,
            game.cast_role_counts,
            COALESCE(
                jsonb_agg(event.payload ORDER BY event.seq)
                    FILTER (WHERE event.seq IS NOT NULL),
                '[]'::jsonb
            )
        FROM games AS game
        LEFT JOIN events AS event ON event.game_id = game.game_id
        WHERE game.status = 'completed'
          AND game.finished_at IS NOT NULL
          AND game.winner IS NOT NULL
          AND game.days IS NOT NULL
          AND game.n_events IS NOT NULL
          AND game.n_humans IS NOT NULL
          AND game.cast_role_counts IS NOT NULL
        GROUP BY game.game_id
    """)

    op.drop_index("games_completed_at_idx", table_name="games")
    op.drop_constraint("events_game_id_fkey", "events", type_="foreignkey")
    op.drop_constraint("games_status_check", "games", type_="check")
    op.execute("""
        UPDATE games
        SET status = CASE status
            WHEN 'completed' THEN 'finished'
            WHEN 'dropped' THEN 'dead'
            ELSE status
        END
    """)
    op.drop_column("games", "cast_role_counts")
    op.drop_column("games", "n_humans")
    op.drop_column("games", "n_events")
    op.drop_column("games", "days")
    op.drop_column("games", "winner")
    op.drop_column("games", "finished_at")
    op.alter_column("games", "status", new_column_name="phase")
    op.rename_table("games", "sessions")
    op.execute("ALTER INDEX games_status_idx RENAME TO sessions_phase_idx")
