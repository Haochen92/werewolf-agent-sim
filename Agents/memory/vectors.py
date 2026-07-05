"""Shared low-level vector primitives — embedding I/O + cosine similarity.

Used across the memory subsystem (read-path retrieval-filtering, dedup pre-filters) and the eval
harness, so they live here rather than inside any one consumer. Pure/stateless.
"""
from __future__ import annotations

import time
from logging import getLogger

import numpy as np
from numpy.typing import NDArray

from langchain_google_genai import GoogleGenerativeAIEmbeddings

logger = getLogger(__name__)

RETRY_ATTEMPTS = 3
RETRY_DELAY_SECONDS = 5


def embed_texts(
    texts: list[str],
    embedding_model: GoogleGenerativeAIEmbeddings,
    task_type: str | None = None,
) -> list[NDArray[np.float64]]:
    for attempt in range(1, RETRY_ATTEMPTS + 1):
        try:
            kwargs: dict = {}
            if task_type:
                kwargs["task_type"] = task_type
            raw = embedding_model.embed_documents(texts, **kwargs)
            return [np.asarray(v, dtype=np.float64) for v in raw]
        except Exception as exc:
            if attempt == RETRY_ATTEMPTS:
                raise
            logger.warning(
                "embed_texts failed (attempt %d/%d): %s — retrying in %ds",
                attempt, RETRY_ATTEMPTS, exc, RETRY_DELAY_SECONDS,
            )
            time.sleep(RETRY_DELAY_SECONDS)
    return []


def cosine_similarity(a: NDArray[np.float64], b: NDArray[np.float64]) -> float:
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))
