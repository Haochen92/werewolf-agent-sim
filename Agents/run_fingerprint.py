"""Runtime fingerprint: stamp results with an execution-bundle provenance label.

A game result is only meaningful relative to the (code, prompts, models, params,
backend) bundle that generated it — model identity, prompt text, sampling params,
and even the API backend (Google AI vs Vertex differ at temp=0) all condition
outputs. Prompts here are code, versioned in git, so instead of an external
prompt registry the fingerprint records the git commit/dirty state plus a content
hash of every prompt source file under ``Agents/prompts/``, alongside principal
model IDs and generation params. A clean commit is reconstructable; a dirty stamp
detects drift but does not preserve the diff.

Consumed by ``Agents.tracing`` (trace metadata + Langfuse release field) and
``scripts/run_batch.py`` (per-game JSONL records). See
``evidence/tracing/fingerprinting/report.md`` for the current contract and
``experiment_log.md`` beside it for the build journey.
"""

from __future__ import annotations

import hashlib
import os
import subprocess
from functools import lru_cache
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
_PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"

# Bump when the fingerprint's definition changes, so a change of definition is not read as a
# change of setup. A record with no such field is schema 1: the prompt hash covered top-level
# files only. Schema 2 widened the hash to every prompt file. Schema 3 reads ``llm_backend``
# from the game model's id; before it the field said vertex or google whatever the model was.
FINGERPRINT_SCHEMA = 3


def _git(*args: str) -> str | None:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=_REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except Exception:
        return None
    if result.returncode != 0:
        return None
    return result.stdout.strip()


@lru_cache(maxsize=1)
def git_revision() -> dict:
    """Current commit SHA plus whether tracked files are modified.

    Untracked files (evidence/ artifacts, logs) don't count as dirty — only
    modified *tracked* files make a stamped SHA unreliable as a code version.
    Cached per process: a mid-run commit shouldn't change the stamp.
    """
    sha = _git("rev-parse", "HEAD")
    status = _git("status", "--porcelain", "--untracked-files=no")
    return {
        "git_commit": sha or "unknown",
        "git_dirty": bool(status) if status is not None else None,
    }


@lru_cache(maxsize=1)
def prompt_bundle_hash() -> str:
    """SHA-256 over every prompt source file under ``Agents/prompts/``, truncated to 16 hex chars.

    It changes whenever prompt source changes, including uncommitted edits the git SHA alone would
    miss. Each file is keyed by its path inside the prompts folder, so a role card and a top-level
    module with the same name, or a file moved between folders, give different hashes.

    Records with no ``fingerprint_schema`` field (before 2026-11-16) carry a hash over the
    top-level files only, so an old and a new hash differ for that reason alone. See the
    companion experiment_log.md.
    """
    digest = hashlib.sha256()
    for path in _prompt_source_files():
        digest.update(path.relative_to(_PROMPTS_DIR).as_posix().encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()[:16]


def _prompt_source_files() -> list[Path]:
    return sorted(
        path
        for path in _PROMPTS_DIR.rglob("*.py")
        if "__pycache__" not in path.parts
        # goldens/ holds a snapshot test's stored texts and their renderer; no game code reads it.
        and path.relative_to(_PROMPTS_DIR).parts[0] != "goldens"
    )


def runtime_fingerprint(game_model: str | None = None) -> dict:
    """Resolve the principal generation settings from env vars + factory defaults.

    ``game_model`` is the model a game was started on, when its starter chose one (a served
    game); None reads the environment's, which is what a command-line or batch game runs on.

    Mirrors the original Google/Vertex accessors in ``Agents.llm_factory`` using
    the same env vars, defaults, and imported constants. Newer backend/per-call
    paths require separate coverage; see the report's known gaps. The import is
    lazy to keep ``tracing`` (which calls this) import-light.
    """
    from Agents.llm_factory import (
        DEFAULT_EMBEDDING_DIMS,
        DEFAULT_EMBEDDING_MODEL,
        DEFAULT_GAME_MODEL,
        DEFAULT_PRO_BACKUP_MODEL,
        DEFAULT_PRO_MODEL,
        DEFAULT_SUMMARY_THINKING_LEVEL,
        _thinking_level_from_env,
        game_thinking_level,
    )

    game_model = game_model or os.getenv("GOOGLE_GENAI_MODEL", DEFAULT_GAME_MODEL)
    backend = _llm_backend(game_model)
    fingerprint = {
        "fingerprint_schema": FINGERPRINT_SCHEMA,
        **git_revision(),
        "prompt_bundle_hash": prompt_bundle_hash(),
        "llm_backend": backend,
        "game_model": game_model,
        "temperature": float(os.getenv("GOOGLE_GENAI_TEMPERATURE", "1.0")),
        "game_thinking_level": game_thinking_level(game_model),
        "summary_thinking_level": _thinking_level_from_env(
            "GOOGLE_GENAI_SUMMARY_THINKING_LEVEL", DEFAULT_SUMMARY_THINKING_LEVEL
        ),
        "judge_thinking_level": _thinking_level_from_env(
            "GOOGLE_GENAI_JUDGE_THINKING_LEVEL", "minimal"
        ),
        "pro_model": os.getenv("GOOGLE_GENAI_PRO_MODEL", DEFAULT_PRO_MODEL),
        "pro_backup_model": os.getenv(
            "GOOGLE_GENAI_PRO_BACKUP_MODEL", DEFAULT_PRO_BACKUP_MODEL
        ),
        "embedding_model": DEFAULT_EMBEDDING_MODEL,
        "embedding_dims": DEFAULT_EMBEDDING_DIMS,
    }
    if backend == "vertex":
        fingerprint["vertex_location"] = os.getenv("VERTEX_LOCATION", "global")
    return fingerprint


def _llm_backend(game_model: str) -> str:
    """The service that answers the game model's calls, read from its id the way the model
    factory routes it: the id's prefix (anthropic, deepseek, openrouter…), or for a bare Gemini
    id, vertex or google."""
    from Agents.llm_factory import _use_vertex
    from Agents.llm_factory.chat import provider_family

    family = provider_family(game_model)
    if family != "google":
        return family
    return "vertex" if _use_vertex() else "google"
