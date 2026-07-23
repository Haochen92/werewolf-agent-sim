"""Game model accessors + the model-config constants they resolve.

The cached chat models the game graph and pipelines run on. Model-config
constants (model id, default thinking level) live HERE, next to their accessor —
NOT in per-package ``config.py`` (those hold domain knobs). ``run_fingerprint``
imports the constants and ``_thinking_level_from_env`` to stamp the generation
bundle without drift.
"""

from __future__ import annotations

import os
from functools import lru_cache

from .backends import create_chat_model

DEFAULT_GAME_MODEL = "gemini-3.1-flash-lite"
DEFAULT_GAME_THINKING_LEVEL = "minimal"
DEFAULT_SUMMARY_THINKING_LEVEL = "medium"
DEFAULT_PRO_MODEL = "gemini-2.5-pro"
# Pinned (was the floating alias "gemini-pro-latest", which Google retargets
# silently — a reproducibility hazard for the extraction pipeline that
# conditions gold labels). gemini-3.5-flash: stable GA, pro-comparable quality,
# and a different model family/quota pool than the primary, so it remains a
# genuine fallback. (3.1-pro-preview rejected: preview tier = no SLA +
# retirement risk.)
DEFAULT_PRO_BACKUP_MODEL = "gemini-3.5-flash"
# Per-item downstream dedup — fixed cheap model (overridable via DEDUP_MODEL env).
DEFAULT_DEDUP_MODEL = "gemini-3.1-flash-lite"
DEFAULT_DEDUP_THINKING_LEVEL = "low"
VALID_THINKING_LEVELS = {"minimal", "low", "medium", "high"}


def _thinking_level_from_env(
    env_var: str,
    default: str | None = None,
) -> str | None:
    value = os.getenv(env_var, default)
    if value is None:
        return None

    normalized = value.strip().lower()
    if normalized in {"", "none", "default"}:
        return None
    if normalized not in VALID_THINKING_LEVELS:
        valid = ", ".join(sorted(VALID_THINKING_LEVELS))
        raise ValueError(f"{env_var} must be one of: {valid}")
    return normalized


@lru_cache(maxsize=1)
def get_llm():
    return create_chat_model(
        os.getenv("GOOGLE_GENAI_MODEL", DEFAULT_GAME_MODEL),
        temperature=float(os.getenv("GOOGLE_GENAI_TEMPERATURE", "1.0")),
        thinking_level=_thinking_level_from_env(
            "GOOGLE_GENAI_THINKING_LEVEL",
            DEFAULT_GAME_THINKING_LEVEL,
        ),
    )


@lru_cache(maxsize=1)
def get_llm_summary():
    return create_chat_model(
        os.getenv("GOOGLE_GENAI_MODEL", DEFAULT_GAME_MODEL),
        temperature=float(os.getenv("GOOGLE_GENAI_TEMPERATURE", "1.0")),
        thinking_level=_thinking_level_from_env(
            "GOOGLE_GENAI_SUMMARY_THINKING_LEVEL",
            DEFAULT_SUMMARY_THINKING_LEVEL,
        ),
    )


@lru_cache(maxsize=1)
def get_llm_judge():
    """Cheap model for binary judgments (e.g. the proactive novelty gate) — minimal thinking."""
    return create_chat_model(
        os.getenv("GOOGLE_GENAI_MODEL", DEFAULT_GAME_MODEL),
        temperature=float(os.getenv("GOOGLE_GENAI_TEMPERATURE", "1.0")),
        thinking_level=_thinking_level_from_env(
            "GOOGLE_GENAI_JUDGE_THINKING_LEVEL",
            "minimal",
        ),
    )


def get_llm_extractor():
    """Cheap, deterministic flash-lite for post-hoc tagging (e.g. addressed-target extraction on a
    human turn). Classification, not generation — temp 0 so the same message tags identically every
    run; a non-deterministic tag would make the reactive scheduler non-reproducible."""
    return create_chat_model(
        os.getenv("GOOGLE_GENAI_MODEL", DEFAULT_GAME_MODEL),
        temperature=0.0,
        thinking_level=_thinking_level_from_env(
            "GOOGLE_GENAI_EXTRACTOR_THINKING_LEVEL",
            "minimal",
        ),
    )


@lru_cache(maxsize=1)
def get_llm_pro():
    return create_chat_model(
        os.getenv("GOOGLE_GENAI_PRO_MODEL", DEFAULT_PRO_MODEL),
        temperature=float(os.getenv("GOOGLE_GENAI_TEMPERATURE", "1.0")),
    )


@lru_cache(maxsize=1)
def get_llm_pro_backup():
    return create_chat_model(
        os.getenv("GOOGLE_GENAI_PRO_BACKUP_MODEL", DEFAULT_PRO_BACKUP_MODEL),
        temperature=float(os.getenv("GOOGLE_GENAI_TEMPERATURE", "1.0")),
        thinking_level=_thinking_level_from_env(
            "GOOGLE_GENAI_PRO_BACKUP_THINKING_LEVEL",
        ),
    )


def get_llm_dedup():
    """Cheap, deterministic model for the per-item downstream dedup agent."""
    return create_chat_model(
        os.getenv("DEDUP_MODEL", DEFAULT_DEDUP_MODEL),
        temperature=0.0,
        thinking_level=_thinking_level_from_env(
            "DEDUP_THINKING_LEVEL",
            DEFAULT_DEDUP_THINKING_LEVEL,
        ),
    )


def get_llm_batch_dedup(model: str, thinking_level: str | None):
    """Deterministic model for the batch (cluster) dedup agent. Model/thinking are
    per-run choices (single-pass model, or two-pass triage/verify), so the caller
    passes them; the factory owns only the temperature=0 dedup policy."""
    return create_chat_model(
        model,
        temperature=0.0,
        thinking_level=thinking_level,
    )
