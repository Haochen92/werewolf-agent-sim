"""Module-level config constants + singletons for the batch (cluster) dedup pipeline.

Env-driven defaults, the cluster-mode/linkage type aliases, TwoPassConfig (which defaults to
these constants), and the LLM/Langfuse factory helpers. ``load_dotenv()`` runs here so the
env-driven constants resolve before anything imports them.
"""

from __future__ import annotations

import os
from typing import Literal

from dotenv import load_dotenv
from Agents.llm_factory import create_chat_model
from pydantic import BaseModel

load_dotenv()

ClusterMode = Literal["bounded", "connected", "agglomerative"]
LinkageMethod = Literal["complete", "average"]

DEFAULT_BATCH_MODEL = os.getenv("MEMORY_BATCH_DEDUP_MODEL", "gemini-2.5-pro")
DEFAULT_BATCH_THINKING_LEVEL = os.getenv("MEMORY_BATCH_DEDUP_THINKING_LEVEL", "")
DEFAULT_BATCH_EMBEDDING_MODEL = os.getenv(
    "MEMORY_BATCH_EMBEDDING_MODEL",
    "gemini-embedding-001",
)
DEFAULT_BATCH_EMBEDDING_DIMS = int(os.getenv("MEMORY_BATCH_EMBEDDING_DIMS", "1536"))
DEFAULT_BATCH_SIMILARITY_THRESHOLD = 0.70
DEFAULT_MAX_CLUSTER_SIZE = 15
DEFAULT_MEMORY_STORE_RETRY_ATTEMPTS = 5
DEFAULT_MEMORY_STORE_RETRY_INITIAL_DELAY = 1.0
DEFAULT_MEMORY_STORE_RETRY_MAX_DELAY = 30.0

DEFAULT_TRIAGE_MODEL = "gemini-3.1-flash-lite"
DEFAULT_TRIAGE_THINKING_LEVEL = "low"

DEDUP_TIMESTAMP_FILE = ".last_dedup_at"


class TwoPassConfig(BaseModel):
    """Configuration for two-pass batch dedup: fast triage + targeted verification.

    Pass 1 (triage): cheap/fast model classifies all entries. KEEP and DISCARD
    decisions are trusted. MERGE decisions are escalated to pass 2.

    Pass 2 (verify): slower/smarter model re-evaluates only the MERGE-flagged
    entries and writes merge text where appropriate.
    """

    triage_model: str = DEFAULT_TRIAGE_MODEL
    triage_thinking_level: str | None = DEFAULT_TRIAGE_THINKING_LEVEL
    verify_model: str = DEFAULT_BATCH_MODEL
    verify_thinking_level: str | None = DEFAULT_BATCH_THINKING_LEVEL or None


def _langfuse_handler():
    from langfuse.langchain import CallbackHandler
    return CallbackHandler()


def _get_batch_llm(model: str, thinking_level: str | None):
    return create_chat_model(
        model,
        temperature=0.0,
        thinking_level=thinking_level,
    )
