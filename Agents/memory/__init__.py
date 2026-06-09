"""Memory subsystem: the vector store, retrieval, dedup, and persistence.

The six modules here were previously flat top-level modules (``Agents.memory``,
``Agents.memory.deduplication``, …); they were grouped into this package during
the pre-v5 refactor. Module-specific imports moved with them
(``Agents.memory.deduplication`` etc.), but the heavily-used ``Agents.memory``
namespace — the store singleton, embeddings, and the retrieval accessors — is
re-exported here so those call sites are unchanged.
"""

from Agents.memory.core import (
    RETRIEVAL_KEEP_PER_SITUATION,
    retrieve_observations_for_agent,
    retrieve_strategy_points_for_agent,
    store_strategy,
)
from Agents.memory.store import embeddings, store

__all__ = [
    "RETRIEVAL_KEEP_PER_SITUATION",
    "embeddings",
    "retrieve_observations_for_agent",
    "retrieve_strategy_points_for_agent",
    "store",
    "store_strategy",
]
