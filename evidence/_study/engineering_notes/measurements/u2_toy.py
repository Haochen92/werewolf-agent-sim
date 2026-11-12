"""Toy: async parent (astream) -> sync node -> child.invoke(config) fanning out 10 Sends sleeping 0.5 s."""
import asyncio, operator, threading, time
from typing import Annotated, TypedDict
from langchain_core.runnables import RunnableLambda
from langchain_core.runnables.config import patch_config
from langgraph.graph import StateGraph, START, END
from langgraph.types import Send

N = 10
seen = {}

class C(TypedDict):
    done: Annotated[list, operator.add]

def fan(state):
    return [Send("seat", {"i": i}) for i in range(N)]

def seat(payload, config):
    seen["seat_cfg_maxc"] = config.get("max_concurrency")
    # a LangChain call inside the seat: what does it inherit?
    probe = RunnableLambda(lambda x, config: config.get("max_concurrency"))
    seen["inner_runnable_maxc"] = probe.invoke(None)  # ambient config only
    time.sleep(0.5)
    return {"done": [payload["i"]]}

cb = StateGraph(C); cb.add_node("seat", seat); cb.add_conditional_edges(START, fan, ["seat"]); cb.add_edge("seat", END)
child = cb.compile()

class P(TypedDict):
    t: float
    tag: str

def make_parent(child_maxc):
    def node(state, config):
        cfg = patch_config(config, max_concurrency=child_maxc) if child_maxc else patch_config(config)
        t0 = time.perf_counter(); child.invoke({"done": []}, cfg); return {"t": time.perf_counter() - t0}
    pb = StateGraph(P); pb.add_node("node", node); pb.add_edge(START, "node"); pb.add_edge("node", END)
    return pb.compile()

# top-level fan-out of 9 async parts to test a top-level max_concurrency
class T(TypedDict):
    done: Annotated[list, operator.add]
async def apart(payload):
    await asyncio.sleep(0.5); return {"done": [1]}
def spart(payload):
    time.sleep(0.5); return {"done": [1]}
def top_graph(fn):
    b = StateGraph(T); b.add_node("part", fn); b.add_conditional_edges(START, lambda s: [Send("part", {}) for _ in range(9)], ["part"]); b.add_edge("part", END)
    return b.compile()

async def main():
    for maxc in (None, 10, 12):
        seen.clear()
        g = make_parent(maxc)
        async for chunk in g.astream({"t": 0.0, "tag": ""}, {"recursion_limit": 50}, stream_mode="values"):
            last = chunk
        print(f"child max_concurrency={maxc}: child.invoke took {last['t']:.2f}s; seat sees {seen}")
    for name, fn in (("async parts", apart), ("sync parts", spart)):
        for maxc in (None, 3):
            g = top_graph(fn); cfg = {"max_concurrency": maxc} if maxc else {}
            t0 = time.perf_counter()
            async for _ in g.astream({"done": []}, cfg): pass
            print(f"TOP-level astream, 9 {name}, max_concurrency={maxc}: {time.perf_counter()-t0:.2f}s")

asyncio.run(main())
