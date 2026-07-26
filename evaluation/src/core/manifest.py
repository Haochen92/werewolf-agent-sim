"""Provenance manifests for eval artifacts — the lineage record.

One writer for the whole eval data plane. A manifest answers "what produced
this?": the git commit, the literal config, and the input datasets by content
hash — so silent drift (an input regenerated under the same name) is detectable.
Current contract and build journey: ``evidence/tracing/fingerprinting/``;
the layer rule (where lineage lives): ``CLAUDE.md`` → Eval Architecture.

Two carriers, chosen by the artifact's shape:
- JSON-object artifacts (``eval_results``) embed the manifest under a top-level
  ``_manifest`` key — they already have an envelope (see ``embed``).
- Envelope-less JSONL artifacts (``frozen_eval_sets``) get a sidecar
  ``<name>.manifest.json`` — a header line would force every reader to skip line 0
  (see ``write_sidecar``).

Inputs are referenced by content hash + a repo-relative path, mirroring the
``frozen_artifacts {path, sha256, count}`` shape the ``evidence/`` golden labels
already use. Config is embedded literally (paths drift) plus a hash of its
canonical JSON, so a result can be re-run from its own recipe.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

from pydantic import BaseModel

from evaluation.src.core.settings import REPO_ROOT


def _rel(path: str | Path) -> str:
    """Repo-relative path when possible — absolute paths drift across machines."""
    resolved = Path(path).resolve()
    try:
        return str(resolved.relative_to(REPO_ROOT))
    except ValueError:
        return str(resolved)


def sha256_of(path: str | Path) -> str:
    """Streaming SHA-256 of a file's bytes."""
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _record_count(path: Path) -> int | None:
    """Best-effort record count: JSONL lines, or a top-level JSON list length."""
    if path.suffix == ".jsonl":
        with path.open(encoding="utf-8") as handle:
            return sum(1 for line in handle if line.strip())
    if path.suffix == ".json":
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (ValueError, OSError):
            return None
        return len(data) if isinstance(data, list) else None
    return None


def fingerprint_input(path: str | Path) -> dict[str, Any]:
    """Content-fingerprint one upstream artifact: ``{path, sha256, count}``."""
    resolved = Path(path)
    return {
        "path": _rel(resolved),
        "sha256": sha256_of(resolved),
        "count": _record_count(resolved),
    }


def _config_dict(config: Any) -> dict[str, Any]:
    if config is None:
        return {}
    if isinstance(config, BaseModel):
        return json.loads(config.model_dump_json())
    if isinstance(config, dict):
        return json.loads(json.dumps(config, sort_keys=True, default=str))
    raise TypeError(f"config must be a pydantic model or dict, got {type(config)!r}")


def _git() -> dict[str, Any]:
    # evaluation -> Agents is the normal dependency direction; reuse the canonical
    # git stamp rather than reimplementing it.
    from Agents.run_fingerprint import git_revision

    return git_revision()


def build_manifest(
    *,
    artifact: str | Path,
    config: Any = None,
    inputs: Iterable[str | Path] = (),
    created_from: str | None = None,
    case_count: int | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Assemble the lineage record for ``artifact``.

    ``inputs`` are upstream artifacts (the eval_set a result consumed, the stores
    a build read) — each content-hashed. ``config`` is embedded literally plus a
    hash over its canonical JSON. ``created_from`` (a human note, e.g. the source
    session) and ``case_count`` are optional carry-overs from the old builder
    manifests. ``extra`` merges in domain-specific top-level keys.
    """
    cfg = _config_dict(config)
    manifest: dict[str, Any] = {
        "artifact": _rel(artifact),
        "created_at": datetime.now().isoformat(),
        **_git(),
        "config": cfg,
        "config_sha256": (
            hashlib.sha256(json.dumps(cfg, sort_keys=True).encode()).hexdigest()
            if cfg
            else None
        ),
        "inputs": [fingerprint_input(p) for p in inputs],
    }
    if created_from is not None:
        manifest["created_from"] = created_from
    if case_count is not None:
        manifest["case_count"] = case_count
    if extra:
        manifest.update(extra)
    return manifest


def write_sidecar(artifact_path: str | Path, **kwargs: Any) -> Path:
    """Write ``<artifact>.manifest.json`` beside an envelope-less JSONL artifact."""
    artifact_path = Path(artifact_path)
    manifest = build_manifest(artifact=artifact_path, **kwargs)
    sidecar = artifact_path.with_suffix(".manifest.json")
    sidecar.parent.mkdir(parents=True, exist_ok=True)
    sidecar.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return sidecar


def embed(record: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
    """Attach the manifest under ``_manifest`` for a JSON-object artifact.

    Mutates and returns ``record``. ``kwargs`` are the ``build_manifest`` args
    (including ``artifact`` — the result file the record will be written to).
    """
    record["_manifest"] = build_manifest(**kwargs)
    return record
