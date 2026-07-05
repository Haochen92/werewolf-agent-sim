"""Prompt text for the evaluation judges, one module per judge type.

Re-exported here so callers can
``from evaluation.src.judges.prompts import X`` regardless of which
judge-type module a constant now lives in.
"""

from evaluation.src.judges.prompts.turn_pipeline import (
    JUDGE_SYSTEM_PROMPT,
    JUDGE_USER_PROMPT,
)
from evaluation.src.judges.prompts.retrieval import (
    RETRIEVAL_SYSTEM_PROMPT,
    RETRIEVAL_USER_PROMPT,
)
from evaluation.src.judges.prompts.turn_action import (
    APPLICATION_SYSTEM_PROMPT,
    APPLICATION_USER_PROMPT,
)
from evaluation.src.judges.prompts.situation_summary import (
    SUMMARY_RUBRIC_SYSTEM_PROMPT,
    SUMMARY_RUBRIC_USER_PROMPT,
    SUMMARY_RUBRIC,
)
from evaluation.src.judges.prompts.situation_summary_pairwise import (
    PAIRWISE_SUMMARY_SYSTEM_PROMPT,
    PAIRWISE_SUMMARY_USER_PROMPT,
)
from evaluation.src.judges.prompts.extraction import (
    EXTRACTION_SYSTEM_PROMPT,
    EXTRACTION_USER_PROMPT,
)
from evaluation.src.judges.prompts.batch_dedup import (
    BATCH_DEDUP_MERGE_SYSTEM_PROMPT,
    BATCH_DEDUP_MERGE_USER_PROMPT,
)
from evaluation.src.judges.prompts.dedup import (
    DEDUP_SYSTEM_PROMPT,
    DEDUP_USER_PROMPT,
)
from evaluation.src.judges.prompts.day_summary import (
    DAY_SUMMARY_JUDGE_SYSTEM_PROMPT,
    DAY_SUMMARY_JUDGE_USER_PROMPT,
    DAY_SUMMARY_RUBRIC,
)

__all__ = [
    "JUDGE_SYSTEM_PROMPT",
    "JUDGE_USER_PROMPT",
    "RETRIEVAL_SYSTEM_PROMPT",
    "RETRIEVAL_USER_PROMPT",
    "APPLICATION_SYSTEM_PROMPT",
    "APPLICATION_USER_PROMPT",
    "SUMMARY_RUBRIC_SYSTEM_PROMPT",
    "SUMMARY_RUBRIC_USER_PROMPT",
    "SUMMARY_RUBRIC",
    "PAIRWISE_SUMMARY_SYSTEM_PROMPT",
    "PAIRWISE_SUMMARY_USER_PROMPT",
    "EXTRACTION_SYSTEM_PROMPT",
    "EXTRACTION_USER_PROMPT",
    "BATCH_DEDUP_MERGE_SYSTEM_PROMPT",
    "BATCH_DEDUP_MERGE_USER_PROMPT",
    "DEDUP_SYSTEM_PROMPT",
    "DEDUP_USER_PROMPT",
    "DAY_SUMMARY_JUDGE_SYSTEM_PROMPT",
    "DAY_SUMMARY_JUDGE_USER_PROMPT",
    "DAY_SUMMARY_RUBRIC",
]
