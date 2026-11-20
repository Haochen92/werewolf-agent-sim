"""Toy: what re-runs after a process kill, and after an interrupt, on the installed LangGraph.
No network, no database: MemorySaver; a 'kill' = copy the saver's storage at a moment
while a node is blocked, then resume a freshly compiled graph on the copy."""
import copy, threading, time, operator
from collections import Counter
from typing import Annotated, TypedDict
from langchain_core.runnables.config import patch_config
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, START, END
from langgraph.types import Send, interrupt, Command

RUNS = Counter()
CTR = {'c': RUNS}
GATE = {"event": None, "blocked_node": None, "started": threading.Event()}

class S(TypedDict, total=False):
    log: Annotated[list, operator.add]

def node(name):
    def f(state):
        CTR['c'][name] += 1
        if GATE["blocked_node"] == name and GATE["event"] is not None:
            GATE["started"].set()
            GATE["event"].wait()
        return {"log": [name]}
    return f

def human(state):
    CTR["c"]["H"] += 1
    v = interrupt("q")
    return {"log": [f"H={v}"]}

def fan(names):
    return lambda s: [Send(n, {}) for n in names]

# inner graph: SEQ1 -> SEQ2 -> (parallel P_AI, P_X) -> END
CACHE = {'on': False}
from langgraph.types import CachePolicy
from langgraph.cache.memory import InMemoryCache
def build_inner(par):
    g = StateGraph(S)
    g.add_node("SEQ1", node("SEQ1")); g.add_node("SEQ2", node("SEQ2"))
    g.add_node("HUB", lambda s: {})
    for n in par:
        if n == 'H': g.add_node(n, human)
        elif CACHE['on']: g.add_node(n, node(n), cache_policy=CachePolicy(key_func=lambda p, n=n: n.encode()))
        else: g.add_node(n, node(n))
    g.add_edge(START, "SEQ1"); g.add_edge("SEQ1", "SEQ2"); g.add_edge("SEQ2", "HUB")
    g.add_conditional_edges("HUB", fan(par), par)
    for n in par: g.add_edge(n, END)
    return g.compile(cache=InMemoryCache()) if CACHE['on'] else g.compile()

def build_parent(saver, par_root, inner_par):
    inner = build_inner(inner_par)
    def wrap(state, config):
        CTR["c"]["WRAP"] += 1
        out = inner.invoke({"log": []}, config=patch_config(config))
        return {"log": ["WRAP:" + ",".join(out["log"])]}
    g = StateGraph(S)
    g.add_node("A", node("A")); g.add_node("HUB0", lambda s: {})
    for n in par_root:
        g.add_node(n, human if n == "H" else node(n))
    g.add_node("WRAP", wrap); g.add_node("Z", node("Z"))
    g.add_edge(START, "A"); g.add_edge("A", "HUB0")
    g.add_conditional_edges("HUB0", fan(par_root), par_root)
    for n in par_root: g.add_edge(n, "WRAP")
    g.add_edge("WRAP", "Z"); g.add_edge("Z", END)
    return g.compile(checkpointer=saver)

def clone(saver):
    new = MemorySaver()
    new.storage = copy.deepcopy(saver.storage); new.writes = copy.deepcopy(saver.writes)
    new.blobs = copy.deepcopy(saver.blobs)
    return new

def kill_and_resume(label, par_root, inner_par, blocked):
    CTR['c'] = Counter()
    GATE.update(event=threading.Event(), blocked_node=blocked, started=threading.Event())
    saver = MemorySaver(); cfg = {"configurable": {"thread_id": "t"}}
    g = build_parent(saver, par_root, inner_par)
    first = []
    th = threading.Thread(target=lambda: [first.append(c) for c in g.stream(
        {"log": []}, cfg, stream_mode="updates", subgraphs=True)], daemon=True)
    th.start(); GATE["started"].wait(5); time.sleep(0.5)
    before = dict(CTR['c']); disk = clone(saver)
    GATE["blocked_node"] = None  # the new process does not block
    CTR['c'] = Counter()
    g2 = build_parent(disk, par_root, inner_par)
    chunks = list(g2.stream(None, cfg, stream_mode="updates", subgraphs=True))
    cached = [(ns, list(d)) for ns, d in chunks if isinstance(d, dict) and (d.get("__metadata__") or {}).get("cached")]
    final = g2.get_state(cfg).values["log"]
    print(f"--- {label}: kill while {blocked} runs")
    print("  runs before kill:", before)
    print("  runs after restart:", dict(CTR['c']))
    print("  chunks tagged cached on restart:", cached)
    print("  final log:", final)

def interrupt_resume(label, par_root, inner_par):
    CTR['c'] = Counter(); GATE.update(event=None, blocked_node=None)
    saver = MemorySaver(); cfg = {"configurable": {"thread_id": "t"}}
    g = build_parent(saver, par_root, inner_par)
    list(g.stream({"log": []}, cfg, stream_mode="updates", subgraphs=True))
    before = dict(CTR['c']); CTR['c'] = Counter()
    chunks = list(g.stream(Command(resume="yes"), cfg, stream_mode="updates", subgraphs=True))
    cached = [(ns, list(d)) for ns, d in chunks if isinstance(d, dict) and (d.get("__metadata__") or {}).get("cached")]
    print(f"--- {label}: interrupt then resume (same process)")
    print("  runs to the interrupt:", before)
    print("  runs on resume:", dict(CTR['c']))
    print("  chunks tagged cached on resume:", cached)
    print("  final log:", g.get_state(cfg).values["log"])

if __name__ == "__main__":
    import langgraph, importlib.metadata as m; print("langgraph", m.version("langgraph"))
    # 1. parent parallel step: P1 finished, P2 blocked when the process dies
    kill_and_resume("root parallel step", ["P1", "P2"], ["Q1"], "P2")
    # 2. inside the imperatively invoked subgraph: SEQ1, SEQ2 done, parallel Q1 done, Q2 blocked
    kill_and_resume("nested subgraph, parallel step", ["P1"], ["Q1", "Q2"], "Q2")
    # 3. inside the subgraph, during the second sequential node
    kill_and_resume("nested subgraph, sequential step", ["P1"], ["Q1"], "SEQ2")
    # 4. interrupts
    interrupt_resume("root parallel step with a human", ["P1", "H"], ["Q1"])
    interrupt_resume("nested subgraph parallel step with a human", ["P1"], ["Q1", "H"])
    CACHE["on"] = True
    interrupt_resume("CACHED nested Q1, with a human", ["P1"], ["Q1", "H"])
    kill_and_resume("CACHED nested Q1, kill (fresh cache in the new process)", ["P1"], ["Q1", "Q2"], "Q2")
