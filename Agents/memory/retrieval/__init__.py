"""Memory read path: retrieve candidates from the store, narrow/diversify them, rerank.

The three stages an agent's memory lookup flows through:
  accessors    fetch observations / strategy points for an agent from the store
  filters      MMR diversification, per-situation capping, near-duplicate gating
  rerank_agent LLM reorder of the surviving candidates by relevance (bi-encoder fallback)

The orchestrator over these stages is ``Agents.memory.enrichment`` (which also does
situation generation + gating). ``__init__`` re-exports the full surface so existing
``Agents.memory.retrieval`` imports resolve unchanged.
"""

from Agents.memory.retrieval.accessors import (  # noqa: F401
    RETRIEVAL_KEEP_PER_SITUATION,
    retrieve_observations_for_agent,
    retrieve_strategy_points_for_agent,
)
from Agents.memory.retrieval.filters import (  # noqa: F401
    cap_per_situation,
    dedup_gate,
    mmr_filter,
)
from Agents.memory.retrieval.rerank_agent import (  # noqa: F401
    RERANK_KEEP,
    RERANK_TOP_K,
    rerank_observations,
    rerank_strategy_points,
)

__all__ = [
    "RETRIEVAL_KEEP_PER_SITUATION",
    "retrieve_observations_for_agent",
    "retrieve_strategy_points_for_agent",
    "cap_per_situation",
    "dedup_gate",
    "mmr_filter",
    "RERANK_KEEP",
    "RERANK_TOP_K",
    "rerank_observations",
    "rerank_strategy_points",
]
