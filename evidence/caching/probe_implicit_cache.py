"""Find the implicit-cache minimum for the game model (gemini-3.1-flash-lite, Vertex).

For each target prefix size we send the SAME long prefix several times back-to-back
(only a tiny per-call suffix differs), then read usage_metadata.input_token_details.cache_read
on the later calls. The smallest input size at which cache_read turns nonzero ≈ the bar.
"""
import time
from Agents.llm_factory import create_chat_model, _use_vertex, DEFAULT_GAME_MODEL

llm = create_chat_model(DEFAULT_GAME_MODEL, temperature=0.0, thinking_level=None)
print(f"model={DEFAULT_GAME_MODEL} backend={'vertex' if _use_vertex() else 'google'}\n")

BASE = ("The werewolf game proceeds through alternating day and night phases where "
        "villagers debate, accuse, and vote while hidden wolves deceive the town. ")

def cache_read(msg):
    um = msg.usage_metadata or {}
    return (um.get("input_token_details") or {}).get("cache_read", 0), um.get("input_tokens", 0)

# repeat counts chosen to bracket the 2048 and 4096 bars
for reps in [70, 110, 150, 200, 260, 340, 440, 600]:
    prefix = BASE * reps
    reads = []
    in_tok = 0
    for i in range(4):  # call 1 warms; 2-4 probe
        msg = llm.invoke(prefix + f"\nReply with only the digit {i}.")
        cr, it = cache_read(msg)
        in_tok = it
        reads.append(cr)
        time.sleep(1.0)
    print(f"input_tokens≈{in_tok:>5}  cache_read per call={reads}")
