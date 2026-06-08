"""Does IMPLICIT caching fire for gemini-2.5-flash on Vertex? Same method as the
flash-lite probe: repeat an identical prefix, check input_token_details.cache_read."""
import time
from Agents.llm_factory import create_chat_model, _use_vertex

MODEL = "gemini-2.5-flash"
llm = create_chat_model(MODEL, temperature=0.0, thinking_level=None)
print(f"model={MODEL} backend={'vertex' if _use_vertex() else 'google'}\n")

BASE = ("The werewolf game proceeds through alternating day and night phases where "
        "villagers debate, accuse, and vote while hidden wolves deceive the town. ")

def cr(msg):
    um = msg.usage_metadata or {}
    return (um.get("input_token_details") or {}).get("cache_read", 0), um.get("input_tokens", 0)

# (a) rapid burst at a few sizes bracketing the 2048 min
print("-- rapid burst (4 identical calls each) --")
for reps in [70, 110, 200, 350]:
    prefix = BASE * reps
    reads, it = [], 0
    for i in range(4):
        m = llm.invoke(prefix + f"\nReply only: {i}")
        c, it = cr(m); reads.append(c); time.sleep(0.5)
    print(f"input≈{it:>5}  cache_read={reads}")

# (b) warm + 30s delay + probe x3 at ~8k (give the server time to populate)
print("\n-- warm, sleep 30s, probe x3 (~8k identical) --")
prefix = BASE * 350
llm.invoke(prefix + "\nReply only: w"); time.sleep(30)
for i in range(3):
    m = llm.invoke(prefix + f"\nReply only: p{i}")
    c, it = cr(m); print(f"probe{i}: input={it} cache_read={c}"); time.sleep(5)
