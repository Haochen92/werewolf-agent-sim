"""Does the parent's get_state() (no subgraphs=True) show an interrupt raised inside an
imperatively invoked subgraph? This is what LiveGameRegistry._resume_from_checkpoint reads."""
import operator
from typing import Annotated, TypedDict
from langchain_core.runnables.config import patch_config
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, START, END
from langgraph.types import Send, interrupt, Command

class S(TypedDict, total=False):
    log: Annotated[list, operator.add]

def ai(s): return {"log": ["ai"]}
def human(s): return {"log": [f"h={interrupt({'player_id': 'player_3'})}"]}
inner = StateGraph(S); inner.add_node("HUB", lambda s: {}); inner.add_node("ai", ai); inner.add_node("human", human)
inner.add_edge(START, "HUB"); inner.add_conditional_edges("HUB", lambda s: [Send("ai", {}), Send("human", {})], ["ai", "human"])
inner.add_edge("ai", END); inner.add_edge("human", END); inner = inner.compile()
def wrap(s, config): return {"log": inner.invoke({"log": []}, config=patch_config(config))["log"]}
g = StateGraph(S); g.add_node("DAY_PHASE", wrap); g.add_edge(START, "DAY_PHASE"); g.add_edge("DAY_PHASE", END)
g = g.compile(checkpointer=MemorySaver()); cfg = {"configurable": {"thread_id": "t"}}
list(g.stream({"log": []}, cfg))
st = g.get_state(cfg)
print("next:", st.next)
print("top-level task interrupts:", [(t.name, [(i.id, i.value) for i in t.interrupts]) for t in st.tasks])
print("top-level StateSnapshot.interrupts:", [(i.id, i.value) for i in st.interrupts])
