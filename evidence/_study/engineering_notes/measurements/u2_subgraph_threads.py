"""Where do a sync subgraph's parallel Sends run when the parent is driven by astream()?
Mirrors the engine's shape (a sync parent node calling subgraph.invoke(); the subgraph fans out
10 Sends) with the server's default executor (64 threads, prefix "graph"). No network, no DB."""
import asyncio, os, threading, time
from concurrent.futures import ThreadPoolExecutor
from typing import Annotated, TypedDict
import operator
from langgraph.graph import StateGraph, START, END
from langgraph.types import Send

lock = threading.Lock(); running = 0; peak = 0; names = set()

class S(TypedDict):
    out: Annotated[list, operator.add]

def seat(arg):
    global running, peak
    with lock:
        running += 1; peak = max(peak, running); names.add(threading.current_thread().name)
    time.sleep(0.5)
    with lock:
        running -= 1
    return {"out": [arg["i"]]}

sub = StateGraph(S)
sub.add_node("seat", seat)
sub.add_conditional_edges(START, lambda s: [Send("seat", {"i": i}) for i in range(10)], ["seat"])
sub.add_edge("seat", END)
sub = sub.compile()

outer_thread = []
def outer(state, config):
    outer_thread.append(threading.current_thread().name)
    return {"out": sub.invoke({"out": []}, config=config)["out"]}

def solo(state):
    outer_thread.append(threading.current_thread().name)
    return {}

parent = StateGraph(S)
parent.add_node("outer", outer); parent.add_node("solo1", solo); parent.add_node("solo2", solo)
parent.add_edge(START, "outer"); parent.add_edge(START, "solo1"); parent.add_edge(START, "solo2")
parent = parent.compile()

async def main():
    asyncio.get_running_loop().set_default_executor(ThreadPoolExecutor(64, thread_name_prefix="graph"))
    t0 = time.perf_counter()
    async for _ in parent.astream({"out": []}, stream_mode="updates", subgraphs=True):
        pass
    print(f"os.cpu_count={os.cpu_count()}  wall={time.perf_counter()-t0:.2f}s for 10 x 0.5 s seats")
    print("parent nodes ran on:", sorted(outer_thread))
    print(f"seat nodes: peak concurrent={peak}, thread names={sorted(names)}")

asyncio.run(main())
