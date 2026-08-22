"""Alembic environment for the server-owned tables (SQLModel metadata = the authority).

Two departures from the stock scaffold, both load-bearing:

- The URL comes from WW_POSTGRES_DSN (via server.config) at runtime — alembic.ini
  carries no credentials. python-dotenv semantics ride pydantic-settings, so the
  project .env works for local runs.
- include_object scopes alembic to tables it OWNS (present in SQLModel.metadata).
  The database is shared: the memory tick's raw-psycopg tables and LangGraph's
  checkpoint tables live alongside, and without this filter ``--autogenerate``
  would propose dropping every table it doesn't recognize.
"""

import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool
from sqlmodel import SQLModel

# The repo isn't an installed package: put its root on the path (pytest gets this
# from pyproject's pythonpath; the alembic CLI does not).
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# Imported for the side effect of registering every app-owned table on SQLModel.metadata.
import server.database_models  # noqa: F401,E402

from server.config import server_settings

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

if server_settings.WW_POSTGRES_DSN:
    config.set_main_option("sqlalchemy.url", server_settings.replay_database_url)

target_metadata = SQLModel.metadata


def include_object(obj, name, type_, reflected, compare_to):
    """Own only what the metadata declares; never touch cohabiting tables."""
    if type_ == "table" and reflected and compare_to is None:
        return False
    return True


def run_migrations_offline() -> None:
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_object=include_object,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata,
                          include_object=include_object)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
