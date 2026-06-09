"""Config constants and LLM factory for the downstream dedup pipeline."""

from Agents.llm_factory import create_chat_model

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

DEDUP_SIMILARITY_THRESHOLD = 0.55  # Lower than rule-based to cast a wider net
DEDUP_TOP_N = 5
DEDUP_MAX_RETRIES = 2
DEDUP_MODEL = "gemini-3.1-flash-lite"
DEDUP_THINKING_LEVEL = "low"

# Embedding pre-filter thresholds — calibrated against dedup_v2 golden labels
# (25 SP, 40 obs human-labeled), validated on 232-case cross-game set (zero errors).
SP_ACTION_DISCARD_THRESHOLD = 0.93
SP_ACTION_KEEP_THRESHOLD = 0.81
OBS_CONTENT_DISCARD_THRESHOLD = 0.96
OBS_CONTENT_KEEP_THRESHOLD = 0.935


def _get_dedup_llm():
    return create_chat_model(
        DEDUP_MODEL,
        temperature=0.0,
        thinking_level=DEDUP_THINKING_LEVEL,
    )
