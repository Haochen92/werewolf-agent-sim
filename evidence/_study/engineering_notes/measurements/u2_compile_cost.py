import logging, time, tracemalloc, gc
logging.disable(logging.CRITICAL)
from langgraph.checkpoint.memory import InMemorySaver
from Agents.graphs.parent import parent_graph, parent_graph_compiled

N = 50
# time
t = time.perf_counter(); gs = [parent_graph.compile(checkpointer=InMemorySaver()) for _ in range(N)]
print(f"compile: {(time.perf_counter()-t)/N*1000:.2f} ms each")
t = time.perf_counter(); cs = [parent_graph_compiled.copy({"checkpointer": InMemorySaver()}) for _ in range(N)]
print(f"copy:    {(time.perf_counter()-t)/N*1000:.3f} ms each")
del gs, cs; gc.collect()
# memory
for label, make in [("compile", lambda: parent_graph.compile(checkpointer=InMemorySaver())),
                    ("copy", lambda: parent_graph_compiled.copy({"checkpointer": InMemorySaver()})),
                    ("saver alone", lambda: InMemorySaver())]:
    gc.collect(); tracemalloc.start(); keep = [make() for _ in range(N)]
    cur, _ = tracemalloc.get_traced_memory(); tracemalloc.stop()
    print(f"{label}: {cur/N/1024:.1f} KiB each"); del keep

# does a copy really save through its own saver? toy graph
from typing import TypedDict
from langgraph.graph import StateGraph, START, END
class S(TypedDict): x: int
g = StateGraph(S); g.add_node("a", lambda s: {"x": s["x"] + 1}); g.add_edge(START, "a"); g.add_edge("a", END)
s0, s1 = InMemorySaver(), InMemorySaver()
base = g.compile(checkpointer=s0); twin = base.copy({"checkpointer": s1})
cfg = {"configurable": {"thread_id": "t"}}
twin.invoke({"x": 1}, cfg)
print("toy: saved in base saver:", len(list(s0.list(cfg))), "| saved in copy's saver:", len(list(s1.list(cfg))),
      "| shares nodes object:", twin.nodes is base.nodes)
