"""Run manifest — the reproducibility record for a training run.

Captures everything needed to understand and reproduce a run: the config, the
adapter, a fingerprint of the exact training data, the git commit, and the final
metrics. Written next to the saved model as ``manifest.json``.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from .config import TrainConfig


def _git_sha() -> str | None:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True, text=True, timeout=5,
        )
        return out.stdout.strip() or None
    except Exception:
        return None


def _fingerprint(raw: dict) -> str:
    """Stable content hash of the raw training payload."""
    blob = json.dumps(raw, sort_keys=True, default=str).encode()
    return hashlib.sha256(blob).hexdigest()[:16]


def build_manifest(config: TrainConfig, adapter_name: str, raw: dict,
                   result: dict[str, Any]) -> dict[str, Any]:
    return {
        "adapter": adapter_name,
        "config": json.loads(config.model_dump_json()),
        "git_sha": _git_sha(),
        "data_fingerprint": _fingerprint(raw),
        "data_stats": result.get("stats", {}),
        "metrics": result.get("metrics", {}),
    }


def write_manifest(config: TrainConfig, adapter_name: str, raw: dict,
                   result: dict[str, Any], output_dir: str | Path) -> dict[str, Any]:
    manifest = build_manifest(config, adapter_name, raw, result)
    path = Path(output_dir) / "manifest.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2))
    return manifest
