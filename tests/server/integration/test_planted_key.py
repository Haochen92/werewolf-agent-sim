"""A player's own API key, and their backup key, are never written to the database.

A hosted game is played on a session started with two made-up keys, on the server's real pieces
and a real Postgres database in the test container (the checkpoint saver, the lesson store, the
game repository, the live game registry), with the seats' models passed in through the session's
graph context. Then the whole database is searched: every column of every table in every schema
of the test database, as bytes. Text and JSON columns are searched as their UTF-8 text; byte
columns as their raw bytes (the checkpoint blobs are msgpack, which holds a string as its plain
UTF-8 bytes), and a byte value that is gzip data (the stored prompt captures) is searched
decompressed as well.

Two games: one played to its end, and one whose seat model fails with an error that carries the
player's key, as a provider's refusal can, so the game dies with that error.

What this does not cover:
- what is sent to the tracing service: tracing is off in the test run (`tests/conftest.py`);
- the process log, and the crash report (`tests/server/test_byok.py` checks the error text and
  `tests/server/test_error_reporting.py` the report);
- anything outside this database, such as files or the browser.
"""

from __future__ import annotations

import asyncio
import gzip

import psycopg
from langchain_core.runnables import RunnableLambda
from psycopg import sql

from server.game.run_config import game_run_config
from tests.factories.scripted_model import FakeModels
from tests.factories.served_game import (
    GAME_TIMEOUT_S,
    accept_any_key,
    delegate_until_over,
    give_models,
    open_server,
    wait_for_question,
)

PRIMARY_KEY = "sk-planted-PRIMARY-0001"
BACKUP_KEY = "sk-planted-BACKUP-0002"
DEEPSEEK = "deepseek/deepseek-v4-pro"
HAIKU = "anthropic/claude-haiku-5-5"  # another company's model, so the backup key runs the rescue
HUMAN_TOKEN = "seat-token-of-the-human"

GZIP_MAGIC = b"\x1f\x8b"


async def test_a_players_keys_are_written_nowhere_in_the_database_after_a_whole_game(
        server_tables_dsn, scripted_model, refuse_real_models):
    """The keys live in the session's memory only. A game played to its end writes its row, its
    events, its cast, its checkpoints, its prompt capture and its evaluation cases; none of them may
    hold either key."""
    # Arrange: a server on the test database, and a game paid for with the player's two keys
    server = await open_server(server_tables_dsn, check_key=accept_any_key)
    try:
        session = await start_keyed_game(server)
        give_models(session, scripted_model(3))
        session.subscribe(HUMAN_TOKEN)
        assert session._secrets == (PRIMARY_KEY, BACKUP_KEY)  # both keys are in the game

        # Act: the game parks on the human's question, then plays to its end
        await wait_for_question(session, server.graph)
        await delegate_until_over(session)
        await asyncio.wait_for(session.wait_finished(), timeout=GAME_TIMEOUT_S)
    finally:
        await server.stop()
    searched = search_database(server_tables_dsn, [PRIMARY_KEY, BACKUP_KEY, session.game_id, "player_1"])

    # Assert: the game finished, and the search sees real content but neither key
    assert session.game_over and session.error is None
    assert searched.hits[PRIMARY_KEY] == []
    assert searched.hits[BACKUP_KEY] == []
    assert {"public.games.game_id", "public.events.game_id",
            "public.checkpoints.thread_id"} <= set(searched.hits[session.game_id])
    # A seat name inside the msgpack checkpoint blobs and inside the gzip prompt capture: the
    # search reads both kinds of byte column.
    assert {"public.checkpoint_blobs.blob", "public.prompt_captures.capture (gzip)",
            "public.game_eval_cases.cases (gzip)"} <= set(searched.hits["player_1"])
    assert {"checkpoints", "checkpoint_blobs", "checkpoint_writes", "games", "events",
            "game_cast", "prompt_captures", "game_eval_cases", "store"} <= {t.split(".")[1] for t in searched.tables}


async def test_a_players_key_in_a_providers_error_is_written_nowhere_in_the_database(
        server_tables_dsn, scripted_model, refuse_real_models):
    """A provider that refuses a key can quote it back in its error. The game then dies with that
    error, which is shown to the players and stored on the game's row: the key must be replaced
    there, and must not reach any other table either (the checkpoint's record of the failed step,
    for one)."""
    # Arrange: a game whose seats' model refuses the key, quoting it
    server = await open_server(server_tables_dsn, check_key=accept_any_key)
    try:
        session = await start_keyed_game(server)
        scripted_model(4)  # only for its replacements of the day summary, opening filter and echo check
        give_models(session, FakeModels(seat=KeyRefusingModel(PRIMARY_KEY)))
        session.subscribe(HUMAN_TOKEN)

        # Act: the game runs until the first seat's turn fails, answering any question meanwhile
        await delegate_until_over(session)
    finally:
        await server.stop()
    row_error = load_game_error(server_tables_dsn, session.game_id)
    searched = search_database(server_tables_dsn, [PRIMARY_KEY, BACKUP_KEY, session.game_id])

    # Assert: the game died with the error, the key replaced, and the key is nowhere
    assert session.error is not None and "***" in session.error
    assert PRIMARY_KEY not in session.error
    assert row_error == session.error
    # LangGraph stores each failed step's exception as an "__error__" write in checkpoint_writes.
    # Until 2026-11-18 ProviderKeyRejected (Agents/turn/agent_player.py) carried the provider's
    # complaint unredacted, so this test found the key there; the complaint is now scrubbed where
    # the error is caught.
    assert searched.hits[PRIMARY_KEY] == [], (
        f"the player's key was written to {searched.hits[PRIMARY_KEY]}")
    assert searched.hits[BACKUP_KEY] == []
    assert "public.games.game_id" in searched.hits[session.game_id]


# ---- the game ---------------------------------------------------------------------------------


async def start_keyed_game(server):
    """A solo game with one human seat, started through the solo door with the player's key for
    the game's model and a backup key for the rescue model of another company."""
    return await server.registry.start_instant(
        game_run_config(memory=False, human_player=1), api_key=PRIMARY_KEY, model=DEEPSEEK,
        backup_model=HAIKU, backup_key=BACKUP_KEY, seat_tokens=[HUMAN_TOKEN])


class FakeKeyRefusedError(Exception):
    """A provider's refusal of a key, shaped like the Anthropic and OpenAI SDK errors: a status
    code and a body whose message quotes the key."""

    def __init__(self, key: str):
        self.status_code = 401
        self.body = {"error": {"message": f"invalid x-api-key: {key}"}}
        super().__init__(f"Error code: 401 - invalid x-api-key: {key}")


class KeyRefusingModel:
    """A seat model whose every call is refused by the provider, the error quoting the key."""

    model = "fake"

    def __init__(self, key: str):
        self.key = key

    def with_structured_output(self, schema, **kwargs):
        def refuse(prompt):
            raise FakeKeyRefusedError(self.key)

        return RunnableLambda(refuse)


def load_game_error(dsn: str, game_id: str) -> str | None:
    with psycopg.connect(dsn) as conn:
        return conn.execute("SELECT error FROM games WHERE game_id = %s", (game_id,)).fetchone()[0]


# ---- the search -------------------------------------------------------------------------------


class Searched:
    """What `search_database` looked at and found: `tables` is every table searched, as
    "schema.table"; `hits[needle]` is every column holding that needle, as
    "schema.table.column", with " (gzip)" when it was found inside decompressed gzip data."""

    def __init__(self, tables: list[str], hits: dict[str, list[str]]):
        self.tables, self.hits = tables, hits


def search_database(dsn: str, needles: list[str]) -> Searched:
    """Search every column of every table in every schema of the database for each needle.

    The tables are listed from `pg_class` (ordinary and partitioned tables, in every schema but
    the system catalogues), so a table added later is searched without changing this. A byte
    column is searched as its raw bytes, and also decompressed when the value is gzip data; any
    other column as its value cast to text, encoded as UTF-8."""
    targets = [needle.encode("utf-8") for needle in needles]
    hits: dict[str, list[str]] = {needle: [] for needle in needles}
    with psycopg.connect(dsn) as conn:
        tables = conn.execute("""
            SELECT c.oid, n.nspname, c.relname
            FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE c.relkind IN ('r', 'p')
              AND n.nspname NOT IN ('pg_catalog', 'information_schema')
              AND n.nspname NOT LIKE 'pg_toast%%'
            ORDER BY n.nspname, c.relname""").fetchall()
        for oid, schema, table in tables:
            columns = conn.execute("""
                SELECT a.attname, t.typname
                FROM pg_attribute a JOIN pg_type t ON t.oid = a.atttypid
                WHERE a.attrelid = %s AND a.attnum > 0 AND NOT a.attisdropped
                ORDER BY a.attnum""", (oid,)).fetchall()
            for column, type_name in columns:
                place = f"{schema}.{table}.{column}"
                for value in column_values(conn, schema, table, column, as_bytes=type_name == "bytea"):
                    for needle, target in zip(needles, targets):
                        if target in value and place not in hits[needle]:
                            hits[needle].append(place)
                    if value.startswith(GZIP_MAGIC):
                        inflated = gzip.decompress(value)
                        for needle, target in zip(needles, targets):
                            if target in inflated and f"{place} (gzip)" not in hits[needle]:
                                hits[needle].append(f"{place} (gzip)")
    return Searched([f"{schema}.{table}" for _oid, schema, table in tables], hits)


def column_values(conn, schema: str, table: str, column: str, *, as_bytes: bool):
    """Every non-null value of one column, as bytes."""
    name = sql.Identifier(column)
    selected = name if as_bytes else sql.SQL("{}::text").format(name)
    query = sql.SQL("SELECT {} FROM {} WHERE {} IS NOT NULL").format(
        selected, sql.Identifier(schema, table), name)
    for (value,) in conn.execute(query):
        yield bytes(value) if as_bytes else value.encode("utf-8")
