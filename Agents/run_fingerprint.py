"""Runtime fingerprint: stamp results with an execution-bundle provenance label.

A game result is only meaningful relative to the (code, prompts, models, params,
backend) bundle that generated it — model identity, prompt text, sampling params,
and even the API backend (Google AI vs Vertex differ at temp=0) all condition
outputs. Prompts here are code, versioned in git, so instead of an external
prompt registry the fingerprint records the git commit/dirty state plus a content
hash of the covered prompt modules, alongside principal model IDs and generation
params. A clean commit is reconstructable; a dirty stamp detects drift but does
not preserve the diff.

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
    """SHA-256 over top-level prompt modules (sorted), truncated to 16 hex chars.

    This is the prompt surface as content: it changes whenever any prompt text
    in a covered top-level file changes, including uncommitted edits the git SHA
    alone would miss. The bundle includes the top-level prompt strings and
    rendering layer (prompt_formatters.py / prompt_inputs.py). It currently does
    NOT recurse into ``prompts/extraction/`` or ``prompts/memory/``; that known
    coverage gap is documented in evidence/tracing/fingerprinting/report.md.

    Records stamped before the rendering layer joined the bundle, 2026-06-10,
    carry an older hash purely from the smaller glob, not a prompt change — see
    the companion experiment_log.md.
    """
    digest = hashlib.sha256()
    for path in sorted(_PROMPTS_DIR.glob("*.py")):
        digest.update(path.name.encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()[:16]


def runtime_fingerprint() -> dict:
    """Resolve the principal generation settings from env vars + factory defaults.

    Mirrors the original Google/Vertex accessors in ``Agents.llm_factory`` using
    the same env vars, defaults, and imported constants. Newer backend/per-call
    paths require separate coverage; see the report's known gaps. The import is
    lazy to keep ``tracing`` (which calls this) import-light.
    """
    from Agents.llm_factory import (
        DEFAULT_EMBEDDING_DIMS,
        DEFAULT_EMBEDDING_MODEL,
        DEFAULT_GAME_MODEL,
        DEFAULT_GAME_THINKING_LEVEL,
        DEFAULT_PRO_BACKUP_MODEL,
        DEFAULT_PRO_MODEL,
        DEFAULT_SUMMARY_THINKING_LEVEL,
        _thinking_level_from_env,
        _use_vertex,
    )

    backend = "vertex" if _use_vertex() else "google"
    fingerprint = {
        **git_revision(),
        "prompt_bundle_hash": prompt_bundle_hash(),
        "llm_backend": backend,
        "game_model": os.getenv("GOOGLE_GENAI_MODEL", DEFAULT_GAME_MODEL),
        "temperature": float(os.getenv("GOOGLE_GENAI_TEMPERATURE", "1.0")),
        "game_thinking_level": _thinking_level_from_env(
            "GOOGLE_GENAI_THINKING_LEVEL", DEFAULT_GAME_THINKING_LEVEL
        ),
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
