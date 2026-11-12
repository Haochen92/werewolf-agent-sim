"""AsyncPostgresSaver (langgraph-checkpoint-postgres 3.1.0): does one saver serialize every game's
checkpoint writes, and does aput hold that lock while it waits for a default-executor thread?
No database: only the connection layer (aio._ainternal.get_connection) is faked; each statement
takes 0.2 s. Everything else is the installed saver."""
import asyncio, contextlib, time
from concurrent.futures import ThreadPoolExecutor
from langgraph.checkpoint.postgres import aio
from langgraph.checkpoint.base import empty_checkpoint

STMT = 0.2

class Cur:
    async def execute(self, *a, **k): await asyncio.sleep(STMT)
    async def executemany(self, *a, **k): await asyncio.sleep(STMT)

class Conn:
    @contextlib.asynccontextmanager
    async def pipeline(self): yield
    @contextlib.asynccontextmanager
    async def transaction(self): yield
    @contextlib.asynccontextmanager
    async def cursor(self, *a, **k): yield Cur()

@contextlib.asynccontextmanager
async def fake_conn(_):
    yield Conn()  # unlimited connections: any serialization comes from the saver itself

aio._ainternal.get_connection = fake_conn

def cfg(t, cid=None):
    c = {"configurable": {"thread_id": t, "checkpoint_ns": ""}}
    if cid: c["configurable"]["checkpoint_id"] = cid
    return c

async def put(saver, t):
    ck = empty_checkpoint(); ck["channel_values"] = {"log": [1, 2, 3]}
    await saver.aput(cfg(t), ck, {}, {"log": 1})

async def writes(saver, t):
    await saver.aput_writes(cfg(t, "c1"), [("log", [4])], task_id="task")

async def main():
    loop = asyncio.get_running_loop()
    saver = aio.AsyncPostgresSaver(object())

    # 1. eight games' checkpoint writes at once (each = 1 statement of 0.2 s under the lock)
    t0 = time.perf_counter()
    await asyncio.gather(*(writes(saver, f"game{i}") for i in range(8)))
    print(f"8 concurrent aput_writes (8 different games): {time.perf_counter()-t0:.2f} s "
          f"(0.2 s if parallel, 1.6 s if serial)")

    # 2. a full default executor: aput holds the lock while queued for a thread
    loop.set_default_executor(ThreadPoolExecutor(max_workers=2))
    for _ in range(2):
        loop.run_in_executor(None, time.sleep, 1.0)  # stand-ins for two busy graph nodes
    await asyncio.sleep(0.01)
    t0 = time.perf_counter()
    async def timed(coro, label):
        await coro; print(f"  {label} finished at {time.perf_counter()-t0:.2f} s")
    await asyncio.gather(timed(put(saver, "gameA"), "aput (game A, needs a pool thread)"),
                         timed(writes(saver, "gameB"), "aput_writes (game B, needs no thread)"))

asyncio.run(main())
