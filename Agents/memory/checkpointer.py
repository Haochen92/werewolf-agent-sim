"""The shared LangGraph checkpointer singleton (in-memory for now).

Instantiated at import as a module-level singleton so the compiled parent graph shares one
checkpointer across the process. In-memory = per-process, non-durable: fine for local/dev HITL
runs; swap for PostgresSaver(WW_POSTGRES_DSN) when checkpoints must survive a restart.
"""


from dotenv import load_dotenv
from langgraph.checkpoint.memory import MemorySaver

load_dotenv()

checkpointer = MemorySaver()