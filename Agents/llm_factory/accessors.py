"""Game model accessors + the model-config constants they resolve.

The chat models the game graph and pipelines run on. Model-config constants
(model id, default thinking level) live HERE, next to their accessor —
NOT in per-package ``config.py`` (those hold domain knobs). ``run_fingerprint``
imports the constants and ``_thinking_level_from_env`` to stamp the generation
bundle without drift.

Accessors are deliberately uncached: memoization lives in ``create_chat_model``,
whose cache key includes the per-game BYOK key (``backends.GAME_LLM``) — an
accessor-level ``lru_cache`` would freeze the first caller's client process-wide
and hand one game's credentials to every later game.
"""

from __future__ import annotations

import os

from . import catalog
from .backends import GAME_LLM, create_chat_model

DEFAULT_GAME_MODEL = "gemini-3.5-flash-lite"
# Different-backend rescue when a seat exhausts its structured-output retries (seen with
# DeepSeek's unconstrained tool-calling): one shot on this model beats a random action.
DEFAULT_GAME_FALLBACK_MODEL = "gemini-3.1-flash-lite"
# A model's own turn and summary levels are catalogue rows (catalog.py, columns turn_thinking and
# summary_thinking); a model with none takes these defaults. A rescued turn gets its rescue
# model's level.
DEFAULT_GAME_THINKING_LEVEL = "minimal"
# A game turn's request budget (2026-09-30): Vertex's shared pool for a new model can hold a
# request for minutes before answering or bouncing it with 429, and the SDK then re-sent each
# bounce up to five times, so one seat's turn took 2-5 minutes with nothing failing. Now a
# request waits GAME_LLM_TIMEOUT_S, is sent GAME_LLM_ATTEMPTS times in all, and then fails,
# which hands the turn to the rescue model (agent_player.run_agent) within about a minute.
# The day summary gets a longer wait: its failure path is the raw transcript.
DEFAULT_GAME_TIMEOUT_S = 30.0
DEFAULT_GAME_ATTEMPTS = 2
DEFAULT_SUMMARY_TIMEOUT_S = 90.0
DEFAULT_SUMMARY_THINKING_LEVEL = "medium"
# The post-game extraction model. gemini-3.8-flash since 2026-10-11: re-extracting two ten-seat pilot
# games, it cost about $0.34 a game against 2.5-pro's $1.17 (promo price, $0.75/$3.75 per 1M to
# 2026-12-31, then $1.50/$7.50), wrote fewer observations with no player IDs, and read as well
# grounded (evidence/memory_system/v8/experiment_log.md). 3.5-flash-lite was cheaper
# still but leaked player IDs into 41% of one game's observations.
DEFAULT_PRO_MODEL = "gemini-3.8-flash"
# Pinned, never a floating alias (Google retargets those silently — a reproducibility hazard). The
# backup only runs when the primary fails, so it is chosen for being a different model family and
# quota pool, a genuine fallback: gemini-2.5-pro, the extraction model before 2026-10-11.
DEFAULT_PRO_BACKUP_MODEL = "gemini-2.5-pro"
# Per-item downstream dedup — fixed cheap model (overridable via DEDUP_MODEL env).
DEFAULT_DEDUP_MODEL = "gemini-3.1-flash-lite"
DEFAULT_DEDUP_THINKING_LEVEL = "low"
VALID_THINKING_LEVELS = {"minimal", "low", "medium", "high"}


def _game_model() -> str:
    """The in-game model: a served game's BYOK selection wins; otherwise the env/default —
    which is what .env has always really been, the local-dev/CLI configuration."""
    return GAME_LLM.get().model or os.getenv("GOOGLE_GENAI_MODEL", DEFAULT_GAME_MODEL)


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


def game_thinking_level(model: str) -> str | None:
    """A game turn's thinking level on ``model``: GOOGLE_GENAI_THINKING_LEVEL when set (a bench arm
    pins it), else the model's own level, else the default."""
    return _thinking_level_from_env(
        "GOOGLE_GENAI_THINKING_LEVEL",
        (row.turn_thinking if (row := catalog.entry(model)) else None) or DEFAULT_GAME_THINKING_LEVEL,
    )


def _request_budget(timeout_env: str, default_timeout: float) -> dict[str, float | int]:
    """The client's per-request timeout (seconds) and attempts, both counted by the SDK:
    ``max_retries`` here is the SDK's attempt count, so 1 means a single request."""
    return {
        "timeout": float(os.getenv(timeout_env, default_timeout)),
        "max_retries": max(1, int(os.getenv("GAME_LLM_ATTEMPTS", DEFAULT_GAME_ATTEMPTS))),
    }


def get_llm():
    model = _game_model()
    return create_chat_model(
        model,
        temperature=float(os.getenv("GOOGLE_GENAI_TEMPERATURE", "1.0")),
        thinking_level=game_thinking_level(model),
        **_request_budget("GAME_LLM_TIMEOUT_S", DEFAULT_GAME_TIMEOUT_S),
    )


def get_llm_game_fallback():
    """The retry-exhaustion rescue seat model, or None when no rescue applies.

    A served game uses its registry-assigned rescue on the same credential path as the
    primary: house-funded stays on the server backend and BYOK stays on the player's key.
    None = no tested compatible rescue, so the typed technical-pass path absorbs failures.
    Otherwise the env pair (``GAME_FALLBACK_MODEL``), or None when it would equal the
    primary — a re-roll on the identical model isn't a rescue."""
    override = GAME_LLM.get()
    if override.model or override.api_key:
        if not override.rescue_model:
            return None
        return create_chat_model(
            override.rescue_model,
            temperature=float(os.getenv("GOOGLE_GENAI_TEMPERATURE", "1.0")),
            thinking_level=game_thinking_level(override.rescue_model),
            **_request_budget("GAME_LLM_TIMEOUT_S", DEFAULT_GAME_TIMEOUT_S),
        )
    model = os.getenv("GAME_FALLBACK_MODEL", DEFAULT_GAME_FALLBACK_MODEL)
    if model == os.getenv("GOOGLE_GENAI_MODEL", DEFAULT_GAME_MODEL):
        return None
    return create_chat_model(
        model,
        temperature=float(os.getenv("GOOGLE_GENAI_TEMPERATURE", "1.0")),
        thinking_level=game_thinking_level(model),
        **_request_budget("GAME_LLM_TIMEOUT_S", DEFAULT_GAME_TIMEOUT_S),
    )


def get_llm_summary():
    model = _game_model()
    return create_chat_model(
        model,
        temperature=float(os.getenv("GOOGLE_GENAI_TEMPERATURE", "1.0")),
        thinking_level=_thinking_level_from_env(
            "GOOGLE_GENAI_SUMMARY_THINKING_LEVEL",
            (row.summary_thinking if (row := catalog.entry(model)) else None)
            or DEFAULT_SUMMARY_THINKING_LEVEL,
        ),
        **_request_budget("GAME_SUMMARY_TIMEOUT_S", DEFAULT_SUMMARY_TIMEOUT_S),
    )


def get_llm_judge():
    """Cheap model for binary judgments (e.g. the proactive novelty gate) — minimal thinking."""
    return create_chat_model(
        _game_model(),
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
        _game_model(),
        temperature=0.0,
        thinking_level=_thinking_level_from_env(
            "GOOGLE_GENAI_EXTRACTOR_THINKING_LEVEL",
            "minimal",
        ),
    )


def get_llm_pro():
    return create_chat_model(
        os.getenv("GOOGLE_GENAI_PRO_MODEL", DEFAULT_PRO_MODEL),
        temperature=float(os.getenv("GOOGLE_GENAI_TEMPERATURE", "1.0")),
    )


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
