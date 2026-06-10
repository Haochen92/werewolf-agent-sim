"""
Downstream per-extraction dedup for memory entries.

After each game's extraction, each new observation or strategy point is compared
against the most similar existing entries via LLM judgment. The LLM decides
whether to DISCARD, REPLACE, DIFFERENTIATE, or KEEP the new entry.
"""

from .schemas import (
    DedupAction,
    DedupResult,
    DedupStats,
    ObservationDedupDecisionOutput,
    ObservationDiscard,
    ObservationKeep,
    StrategyDedupDecisionOutput,
    StrategyDiscard,
    StrategyKeep,
)
from .config import (
    DEDUP_MAX_RETRIES,
    DEDUP_MODEL,
    DEDUP_SIMILARITY_THRESHOLD,
    DEDUP_THINKING_LEVEL,
    DEDUP_TOP_N,
    OBS_CONTENT_DISCARD_THRESHOLD,
    OBS_CONTENT_KEEP_THRESHOLD,
    SP_ACTION_DISCARD_THRESHOLD,
    SP_ACTION_KEEP_THRESHOLD,
    _get_dedup_llm,
)
from .formatting import (
    _format_existing_entries,
    _format_existing_observations,
    _serialize_candidates,
)
from .prefilter import (
    _embedding_prefilter_observation,
    _embedding_prefilter_strategy_point,
)
from .store_ops import (
    _apply_decision,
    _apply_observation_decision,
    _bump_observation_count,
    _item_for_candidate,
    _store_new_observation,
    _store_new_point,
    _update_auto_duplicate,
    _update_auto_observation_duplicate,
)
from .llm import (
    _call_dedup_llm,
    _call_observation_dedup_llm,
    _candidate_validation_error,
)
from .pipeline import (
    _emit_dedup_span,
    dedup_single_observation,
    dedup_single_strategy_point,
    run_downstream_observation_dedup,
    run_downstream_strategy_dedup,
)

__all__ = [
    # schemas
    "DedupAction",
    "DedupResult",
    "DedupStats",
    "ObservationDedupDecisionOutput",
    "ObservationDiscard",
    "ObservationKeep",
    "StrategyDedupDecisionOutput",
    "StrategyDiscard",
    "StrategyKeep",
    # config
    "DEDUP_MAX_RETRIES",
    "DEDUP_MODEL",
    "DEDUP_SIMILARITY_THRESHOLD",
    "DEDUP_THINKING_LEVEL",
    "DEDUP_TOP_N",
    "OBS_CONTENT_DISCARD_THRESHOLD",
    "OBS_CONTENT_KEEP_THRESHOLD",
    "SP_ACTION_DISCARD_THRESHOLD",
    "SP_ACTION_KEEP_THRESHOLD",
    "_get_dedup_llm",
    # formatting
    "_format_existing_entries",
    "_format_existing_observations",
    "_serialize_candidates",
    # prefilter
    "_embedding_prefilter_observation",
    "_embedding_prefilter_strategy_point",
    # store_ops
    "_apply_decision",
    "_apply_observation_decision",
    "_bump_observation_count",
    "_item_for_candidate",
    "_store_new_observation",
    "_store_new_point",
    "_update_auto_duplicate",
    "_update_auto_observation_duplicate",
    # llm
    "_call_dedup_llm",
    "_call_observation_dedup_llm",
    "_candidate_validation_error",
    # pipeline
    "_emit_dedup_span",
    "dedup_single_observation",
    "dedup_single_strategy_point",
    "run_downstream_observation_dedup",
    "run_downstream_strategy_dedup",
]
