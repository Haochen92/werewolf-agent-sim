"""The shared LangGraph checkpointer singleton (in-memory for now).

Instantiated at import as a module-level singleton so the compiled parent graph shares one
checkpointer across the process. In-memory = per-process, non-durable: fine for local/dev HITL
runs; swap for PostgresSaver(WW_POSTGRES_DSN) when checkpoints must survive a restart.

The serializer allowlists the Pydantic models that ride graph state (every HITL resume
deserializes them from the checkpoint): LangGraph's default permissive msgpack warns on each
unregistered custom type and will refuse them entirely once strict mode becomes the default,
so the allowlist is stated explicitly. A new model class added to graph state must be added
here too, or resumes will warn (later: fail).
"""


from dotenv import load_dotenv
from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer

from Agents.schemas import game_events

load_dotenv()

_STATE_MODEL_ALLOWLIST = [
    game_events.AddressedTarget,
    game_events.FiringReason,
    game_events.DiscussionPassReason,  # str-Enum inside DayChannel (pass markers)
    game_events.DayChannel,
    game_events.DaySummary,
    game_events.WolfChannel,
    game_events.InvestigatorResult,
    game_events.DayVote,
    game_events.DeathRecord,
]

checkpointer = MemorySaver(
    serde=JsonPlusSerializer(allowed_msgpack_modules=_STATE_MODEL_ALLOWLIST)
)
