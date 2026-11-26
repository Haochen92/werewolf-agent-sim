"""Do concurrent PostgresStore.search calls overlap? No database, no network.

Only the connection layer is faked (langgraph.store.postgres.base._pg_internal.get_connection):
a fake pool of 4 connections whose cursors return no rows. Everything else is the installed
PostgresStore: its _cursor(), its self.lock, batch(), _batch_search_ops(). The embedder sleeps
1.0 s per call and returns a fixed vector of the right size.
"""
import contextlib
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor

from langchain_core.embeddings import Embeddings
from langgraph.store.postgres import base as pg_base
from langgraph.store.postgres import PostgresStore

DIMS = 8
SLEEP = 1.0
N = 4


class SleepyEmbeddings(Embeddings):
    def embed_documents(self, texts):
        time.sleep(SLEEP)
        return [[0.1] * DIMS for _ in texts]

    def embed_query(self, text):
        time.sleep(SLEEP)
        return [0.1] * DIMS


class FakeCursor:
    def execute(self, query, params=None):
        return self

    def fetchall(self):
        return []

    def __iter__(self):
        return iter(())


class FakeConn:
    @contextlib.contextmanager
    def pipeline(self):
        yield

    @contextlib.contextmanager
    def transaction(self):
        yield

    @contextlib.contextmanager
    def cursor(self, *a, **k):
        yield FakeCursor()


_pool = threading.BoundedSemaphore(4)  # a pool of 4, like open_store's max_size


@contextlib.contextmanager
def fake_get_connection(conn):
    with _pool:
        yield FakeConn()


pg_base._pg_internal.get_connection = fake_get_connection


def run(store, label):
    def one(i):
        t0 = time.perf_counter()
        store.search(("strategy_points", "seer", "day_vote"), query="x", limit=3)
        return time.perf_counter() - t0

    t0 = time.perf_counter()
    with ThreadPoolExecutor(max_workers=N) as ex:
        each = list(ex.map(one, range(N)))
    total = time.perf_counter() - t0
    print(f"{label}: {N} concurrent searches, total {total:.2f} s; each "
          + ", ".join(f"{e:.2f}" for e in sorted(each)))


store = PostgresStore(object(), index={"dims": DIMS, "embed": SleepyEmbeddings(), "fields": ["situation"]})
print("store.lock type:", type(store.lock).__name__, "| supports_pipeline:", store.supports_pipeline)
run(store, "as installed (store.lock held)")
store.lock = contextlib.nullcontext()  # control: same code with the lock removed
run(store, "control (lock replaced by a no-op)")
