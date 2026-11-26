"""Each hosted game saves and looks lessons up through objects of its own, so one game's slow
save or lookup does not hold up another game.

The Postgres checkpoint saver and the lesson store each hold a lock of their own for a whole
operation. With one saver and one store for the server, every game waited behind every other
game's operation. `GraphRuntime.graph_for_game` gives each game a copy of the compiled graph with
its own saver and store on the two shared connection pools.

These tests use the server's real pieces on the Postgres database in the test container. They
show that the games' operations are independent. They do not measure how much faster a loaded
server becomes: that needs many games and a slow database, which a test does not have.
"""

from __future__ import annotations

import asyncio
import threading

from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from Agents.memory.persistence.postgres import LessonStore
from server.game.run_config import game_run_config
from tests.factories.served_game import delegate_until_over, give_models, open_server

DIMS = 4


async def test_a_game_whose_saves_are_held_up_does_not_hold_up_another_game(
        server_tables_dsn, scripted_model, refuse_real_models):
    # Arrange: two solo games on one server, and the first game's saver made unable to save
    server = await open_server(server_tables_dsn)
    try:
        held = await _start_solo_game(server, scripted_model(1), "token-of-the-held-game")
        free = await _start_solo_game(server, scripted_model(2), "token-of-the-free-game")
        held_saver, free_saver = held._graph.checkpointer, free._graph.checkpointer
        saver_pool, store_pool = server.runtime._pool, server.runtime._memory_pool
        await held_saver.lock.acquire()  # every save of the held game now waits

        # Act: the free game is played to its end while the held game cannot save
        try:
            await delegate_until_over(free)
            held_ended_meanwhile = held.ended
        finally:
            held_saver.lock.release()
        await delegate_until_over(held)
    finally:
        await server.stop()

    # Assert: each game had its own saver and store on the shared pools, the free game finished
    # while the other was held, and the held game finished once released
    assert held_saver is not free_saver
    assert held_saver.conn is free_saver.conn is saver_pool
    assert held._graph.store is not free._graph.store
    assert held._graph.store.conn is free._graph.store.conn is store_pool
    assert free.game_over and free.error is None
    assert not held_ended_meanwhile
    assert held.game_over and held.error is None


def test_a_lesson_lookup_fetches_its_embedding_before_it_takes_the_stores_lock(postgres_dsn):
    """The seats of one game look lessons up in the same step. The embedding is a network call,
    so if it ran under the store's lock those lookups would run one after another."""
    # Arrange: a store with one lesson, and an embedder that records whether the lock is held
    lock_held_during_embedding: list[bool] = []
    embedded: list[list[str]] = []

    def embed(texts: list[str]) -> list[list[float]]:
        lock_held_during_embedding.append(store.lock.locked())
        embedded.append(list(texts))
        return [[1.0, 0.0, 0.0, 0.0] for _ in texts]

    pool = ConnectionPool(postgres_dsn, open=True, min_size=1, max_size=2,
                          kwargs={"autocommit": True, "prepare_threshold": 0, "row_factory": dict_row})
    try:
        store = LessonStore(pool, index={"dims": DIMS, "embed": embed, "fields": ["situation"]})
        store.setup()
        store.put(("strategy_points", "villager"), "lesson-1", {"situation": "two players claim one role"})
        lock_held_during_embedding.clear()
        embedded.clear()

        # Act: one lookup
        found = store.search(("strategy_points", "villager"), query="a counter-claim", limit=3)
    finally:
        pool.close()

    # Assert: the lesson is found, the query was embedded once, and with the lock free
    assert [item.key for item in found] == ["lesson-1"]
    assert embedded == [["a counter-claim"]]
    assert lock_held_during_embedding == [False]


def test_two_lookups_on_one_store_embed_at_the_same_time(postgres_dsn):
    # Arrange: an embedder that waits until two lookups are inside it at once
    both_inside = threading.Barrier(2, timeout=10)

    def embed(texts: list[str]) -> list[list[float]]:
        both_inside.wait()  # raises BrokenBarrierError if the second lookup never arrives
        return [[1.0, 0.0, 0.0, 0.0] for _ in texts]

    pool = ConnectionPool(postgres_dsn, open=True, min_size=1, max_size=2,
                          kwargs={"autocommit": True, "prepare_threshold": 0, "row_factory": dict_row})
    try:
        store = LessonStore(pool, index={"dims": DIMS, "embed": embed, "fields": ["situation"]})
        store.setup()
        results: list[list] = []

        def look_up(query: str) -> None:
            results.append(store.search(("strategy_points", "villager"), query=query, limit=3))

        # Act: two seats look a lesson up at once
        seats = [threading.Thread(target=look_up, args=(query,)) for query in ("first", "second")]
        for seat in seats:
            seat.start()
        for seat in seats:
            seat.join(timeout=20)
    finally:
        pool.close()

    # Assert: both lookups returned, which they can only do if both were embedding together
    assert results == [[], []]


async def _start_solo_game(server, models, token: str):
    """A solo game with one human seat whose page is open, on the test's scripted models."""
    session = await server.registry.start_instant(
        game_run_config(memory=False, human_player=1), api_key="", model="", seat_tokens=[token])
    give_models(session, models)
    session.subscribe(token)
    return session
