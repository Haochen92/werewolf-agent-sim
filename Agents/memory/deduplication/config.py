"""Domain config (thresholds, retry/search limits) for the downstream dedup pipeline.

The model config (which model, temperature, thinking) lives in llm_factory.get_llm_dedup —
this file holds only the dedup-domain knobs.
"""

DEDUP_SIMILARITY_THRESHOLD = 0.55  # Lower than rule-based to cast a wider net
DEDUP_TOP_N = 5
DEDUP_MAX_RETRIES = 2

# Embedding pre-filter thresholds — calibrated against dedup_v2 golden labels
# (25 SP, 40 obs human-labeled), validated on 232-case cross-game set (zero errors).
SP_ACTION_DISCARD_THRESHOLD = 0.93
SP_ACTION_KEEP_THRESHOLD = 0.81
OBS_CONTENT_DISCARD_THRESHOLD = 0.96
OBS_CONTENT_KEEP_THRESHOLD = 0.935
