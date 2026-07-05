"""Memory read path: the whole pipeline that turns an agent's payload into retrieved memory.

The stages a turn's memory lookup flows through, in order:
  gate               plan_gating decides whether/what to retrieve this turn (RetrievalPlan)
  situation-summary  situation_agent generates the retrieval query (+ its structured dimensions)
  embedding search   accessors fetch observations / strategy points from the store
  filter             filters — MMR diversification, per-situation capping, near-duplicate gating
  rerank             rerank_agent — LLM reorder of survivors by relevance (bi-encoder fallback)
  dimension reweight dimension_gating soft-reweights by query↔stored dimension alignment
  cap                keep the top-N per situation

``pipeline.py`` is the orchestrator over these stages (``enrich_payload_with_memory``); it owns the
single retriever span while the stage helpers stay pure. ``__init__`` re-exports the full surface so
both ``Agents.memory.retrieval`` audiences (the low-level stages and the pipeline/gating entry
points) resolve unchanged.
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
from Agents.memory.retrieval.plan_gating import (  # noqa: F401
    _filtering_enabled_for_role,
    _memory_enabled_for_role,
    _reranking_enabled_for_memory_kind,
    _retrieval_type_enabled,
    _store_dir_from_config,
)
from Agents.memory.retrieval.situation_agent import _generate_situations_for_agent  # noqa: F401
from Agents.memory.retrieval.pipeline import enrich_payload_with_memory  # noqa: F401

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
    "enrich_payload_with_memory",
    "_generate_situations_for_agent",
    "_filtering_enabled_for_role",
    "_memory_enabled_for_role",
    "_reranking_enabled_for_memory_kind",
    "_retrieval_type_enabled",
    "_store_dir_from_config",
]
