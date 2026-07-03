"""Promote a keeper eval run from scratch into the durable ``evidence/`` record.

``evaluation/eval_results/`` is throwaway staging; the run that is worth keeping
graduates here into ``evidence/<experiment>/``, co-located with the exact config
that produced it and a lineage manifest. Lineage is stamped *at this step* (not in
the runner) so scratch stays cheap and only keepers pay the cost — the two-zone
model in ``evaluation/README.md`` → Data plane.

The manifest content-hashes the inputs the config named (the frozen eval set, the
store snapshots) so the evidence copy stays identifiable after those inputs drift
or move — the failure mode a bare config reference cannot survive. A referenced
input that is missing is recorded as such rather than silently dropped: a broken
chain is a finding, not a crash.

The graduated result file is copied byte-for-byte and the manifest rides as a
``<name>.manifest.json`` sidecar, so the preserved artifact is exactly what ran.
"""
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any

from evaluation.src.core.manifest import build_manifest, write_sidecar
from evaluation.src.core.settings import REPO_ROOT


def referenced_inputs(config: dict[str, Any]) -> list[str]:
    """Path-valued config entries that name a data file — ``dataset`` and any
    ``*_path`` (e.g. ``observations_path``). These are what get content-hashed."""
    found: list[str] = []

    def walk(obj: Any) -> None:
        if isinstance(obj, dict):
            for key, value in obj.items():
                if isinstance(value, str) and (key == "dataset" or key.endswith("_path")):
                    found.append(value)
                else:
                    walk(value)
        elif isinstance(obj, list):
            for item in obj:
                walk(item)

    walk(config)
    seen: set[str] = set()
    ordered: list[str] = []
    for path in found:
        if path not in seen:
            seen.add(path)
            ordered.append(path)
    return ordered


def referenced_models(config: dict[str, Any]) -> list[str]:
    """Model aliases the config names (``model`` / ``*_model``). Aliases only —
    the server-side version they resolved to is not knowable offline."""
    aliases: set[str] = set()

    def walk(obj: Any) -> None:
        if isinstance(obj, dict):
            for key, value in obj.items():
                if isinstance(value, str) and (key == "model" or key.endswith("_model")):
                    aliases.add(value)
                else:
                    walk(value)
        elif isinstance(obj, list):
            for item in obj:
                walk(item)

    walk(config)
    return sorted(aliases)


def _resolve(path: str) -> Path:
    """Config paths are repo-relative; resolve against the repo root so graduation
    works regardless of the caller's cwd."""
    candidate = Path(path)
    return candidate if candidate.is_absolute() else REPO_ROOT / candidate


def _rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path.resolve())


def _evidence_dir(experiment: str) -> Path:
    """A path-like value is used as-is (under the repo root); a bare name maps to
    ``evidence/<name>``."""
    if "/" in experiment or experiment.startswith("evidence"):
        return _resolve(experiment)
    return REPO_ROOT / "evidence" / experiment


def graduate(
    *,
    result: Path,
    config_path: Path,
    experiment: str,
    created_from: str | None = None,
    force: bool = False,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Copy a keeper result + its config into ``evidence/<experiment>/`` and write
    the lineage manifest. Returns a summary of what was (or would be) written."""
    if not result.is_file():
        raise FileNotFoundError(f"result not found: {result}")
    if not config_path.is_file():
        raise FileNotFoundError(f"config not found: {config_path}")

    config = json.loads(config_path.read_text(encoding="utf-8"))

    target_dir = _evidence_dir(experiment)
    dest_result = target_dir / "eval_results" / result.name
    dest_config = target_dir / "eval_configs" / config_path.name

    if dest_result.exists() and not force and not dry_run:
        raise FileExistsError(
            f"{_rel(dest_result)} already exists — pass --force to overwrite a graduated record"
        )

    present: list[Path] = []
    missing: list[str] = []
    for ref in referenced_inputs(config):
        resolved = _resolve(ref)
        if resolved.is_file():
            present.append(resolved)
        else:
            reason = "is a directory" if resolved.is_dir() else "not found"
            missing.append(f"{ref} ({reason})")

    extra: dict[str, Any] = {
        "graduated_from": _rel(result),
        "config_source": _rel(config_path),
        "models": referenced_models(config),
    }
    if missing:
        extra["missing_inputs"] = missing

    manifest = build_manifest(
        artifact=dest_result,
        config=config,
        inputs=present,
        created_from=created_from,
        extra=extra,
    )

    summary = {
        "result": _rel(dest_result),
        "config": _rel(dest_config),
        "manifest": _rel(dest_result.with_suffix(".manifest.json")),
        "git_commit": manifest.get("git_commit"),
        "config_sha256": manifest.get("config_sha256"),
        "inputs_hashed": [fp["path"] for fp in manifest["inputs"]],
        "missing_inputs": missing,
        "models": extra["models"],
        "dry_run": dry_run,
    }

    if dry_run:
        return summary

    dest_result.parent.mkdir(parents=True, exist_ok=True)
    dest_config.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(result, dest_result)
    shutil.copy2(config_path, dest_config)
    write_sidecar(
        dest_result,
        config=config,
        inputs=present,
        created_from=created_from,
        extra=extra,
    )
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Graduate a keeper eval run from eval_results/ into evidence/<experiment>/."
    )
    parser.add_argument("--result", type=Path, required=True, help="the keeper result file in eval_results/")
    parser.add_argument("--config", type=Path, required=True, help="the config that produced it")
    parser.add_argument("--experiment", required=True, help="evidence experiment name or path (e.g. retrieval/store_dedup)")
    parser.add_argument("--created-from", default=None, help="optional human note on the source run")
    parser.add_argument("--force", action="store_true", help="overwrite an already-graduated record")
    parser.add_argument("--dry-run", action="store_true", help="show what would be written, write nothing")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = graduate(
        result=args.result,
        config_path=args.config,
        experiment=args.experiment,
        created_from=args.created_from,
        force=args.force,
        dry_run=args.dry_run,
    )
    print(("DRY RUN — would graduate:" if summary["dry_run"] else "Graduated:"))
    print(f"  result   -> {summary['result']}")
    print(f"  config   -> {summary['config']}")
    print(f"  manifest -> {summary['manifest']}")
    print(f"  git      {summary['git_commit']}")
    print(f"  config_sha256 {summary['config_sha256']}")
    print(f"  inputs hashed: {summary['inputs_hashed'] or '(none)'}")
    print(f"  models (aliases): {summary['models'] or '(none)'}")
    if summary["missing_inputs"]:
        print(f"  ⚠ MISSING inputs (broken chain): {summary['missing_inputs']}")
    if not summary["dry_run"]:
        print("  reminder: if this config was a one-shot (not a reusable template),")
        print("            delete its source from evaluation/config/ — git history keeps it.")


if __name__ == "__main__":
    main()
