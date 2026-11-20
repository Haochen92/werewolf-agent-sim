"""A real Postgres database for the integration tests, inside a container started for the run.

`postgres_container` starts one container for the whole test run, the first time a test asks for
a database, and stops it when the run ends. `postgres_dsn` gives each test a fresh, empty
database with a unique name inside that container, and drops it after the test.
`server_tables_dsn` is the same database with the server's own tables made in it.

Nothing here is autouse, so a run that selects no test needing a database starts no container.
(The model for this module is dota2pred's `tests/fixtures/database.py`; there the table-creating
fixture is autouse and starts a container on every run.)

Each test gets its own database rather than a transaction rolled back at its end, because the
code under test commits on connections of its own: the checkpoint saver and the lesson store
open their own pools, and the game repository opens a session per write. A rollback on the
test's connection would not undo any of that.

The image is production's: the server's database is the `ww-postgres` container, which runs
`pgvector/pgvector:pg17`. The lesson store (`Agents/memory/persistence/postgres.py`) needs the
pgvector extension, which the plain `postgres:17-alpine` image does not have.

No test reads the development database address (`WW_POSTGRES_DSN` in `.env`): every address
here is the container's.
"""

from __future__ import annotations

import uuid
from pathlib import Path

import psycopg
import pytest

IMAGE = "pgvector/pgvector:pg17"
MIGRATIONS = Path(__file__).resolve().parents[2] / "alembic"


@pytest.fixture(scope="session")
def postgres_container():
    """One Postgres container for the run. Fails, rather than skips, when Docker cannot be
    reached: a skipped integration test would look like a passing one."""
    from testcontainers.community.postgres import PostgresContainer
    from testcontainers.core.config import testcontainers_config

    # The reaper container (Ryuk) is not on this machine, and pulling it is a network call the
    # suite should not need. The `with` block below stops the container when the run ends; a run
    # killed outright leaves it running (find it with `docker ps --filter label=org.testcontainers.lang`).
    testcontainers_config.ryuk_disabled = True
    try:
        container = PostgresContainer(IMAGE, driver=None)  # connects to Docker here
        container.start()
    except Exception as exc:
        pytest.fail(
            "The integration tests need Docker, to start a Postgres container "
            f"({IMAGE}), and Docker could not be reached or could not start it: {exc!r}",
            pytrace=False)
    try:
        yield container
    finally:
        container.stop()


@pytest.fixture
def postgres_dsn(postgres_container):
    """The address of a fresh, empty database in the test container, in the form the server
    reads from `WW_POSTGRES_DSN` (`postgresql://user:password@host:port/name`). The database is
    dropped after the test, even if a connection to it is still open."""
    admin_dsn = postgres_container.get_connection_url(driver=None)
    name = f"ww_test_{uuid.uuid4().hex[:12]}"
    with psycopg.connect(admin_dsn, autocommit=True) as admin:
        admin.execute(f'CREATE DATABASE "{name}"')
    yield admin_dsn.rsplit("/", 1)[0] + f"/{name}"
    with psycopg.connect(admin_dsn, autocommit=True) as admin:
        admin.execute(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)')


@pytest.fixture
def server_tables_dsn(postgres_dsn):
    """`postgres_dsn` with the server's tables made in it, by the same migrations production runs
    (`alembic upgrade head`), so the seeded rows the tables depend on are there too: the puppet
    catalogue that the cast table's foreign key points at, and the model catalogue."""
    migrate_server_tables(postgres_dsn)
    return postgres_dsn


def sqlalchemy_url(dsn: str) -> str:
    """The DSN in the form the server's SQLAlchemy engine takes (`postgresql+psycopg://...`),
    converted by the server's own settings, as the server converts `WW_POSTGRES_DSN`."""
    from server.config import ServerSettings

    return ServerSettings(_env_file=None, WW_POSTGRES_DSN=dsn).replay_database_url


def migrate_server_tables(dsn: str) -> None:
    """Run the server's migrations on `dsn`.

    `alembic/env.py` takes its address from `server.config.server_settings`, which reads `.env`
    at import. So the address is set on that object for the length of the run and put back
    after, and the Alembic config is built without `alembic.ini`, whose logging section would
    reconfigure (and silence) the test run's loggers."""
    from alembic import command
    from alembic.config import Config

    from server.config import server_settings

    config = Config()
    config.set_main_option("script_location", str(MIGRATIONS))
    config.set_main_option("sqlalchemy.url", sqlalchemy_url(dsn))
    previous = server_settings.WW_POSTGRES_DSN
    server_settings.WW_POSTGRES_DSN = dsn
    try:
        command.upgrade(config, "head")
    finally:
        server_settings.WW_POSTGRES_DSN = previous
