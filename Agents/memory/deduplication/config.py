"""Domain config (thresholds, retry/search limits) for the downstream dedup pipeline.

The model config (which model, temperature, thinking) lives in llm_factory.get_llm_dedup —
this file holds only the dedup-domain knobs.
"""

from Agents.llm_factory import similarity_threshold

DEDUP_SIMILARITY_THRESHOLD = similarity_threshold("dedup_candidate")  # Lower than rule-based to cast a wider net
DEDUP_TOP_N = 5
DEDUP_MAX_RETRIES = 2

# Embedding pre-filter thresholds — calibrated against dedup_v2 golden labels
# (25 SP, 40 obs human-labeled), validated on 232-case cross-game set (zero errors); per embedding
# model in llm_factory.embeddings.SIMILARITY_THRESHOLDS.
SP_ACTION_DISCARD_THRESHOLD = similarity_threshold("sp_action_discard")
SP_ACTION_KEEP_THRESHOLD = similarity_threshold("sp_action_keep")
OBS_CONTENT_DISCARD_THRESHOLD = similarity_threshold("obs_content_discard")
OBS_CONTENT_KEEP_THRESHOLD = similarity_threshold("obs_content_keep")
