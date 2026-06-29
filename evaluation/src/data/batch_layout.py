"""Output layout for ``batch_results/`` — one self-describing folder per experiment.

A run launched with ``--experiment <id>`` lands everything for that experiment under
``batch_results/<id>/`` instead of scattering a flat game-record file plus a shared
``eval_cases/`` sibling (the legacy layout, which left the two halves of a run in two
places with nothing tying them together — see the ``batch_results`` README).

    batch_results/<experiment>/
      config.json                              resolved-config mirror + runtime fingerprint (re-runnable)
      summary.json                             per-run outcome/status, merged across invocations
      games/<session_prefix>.jsonl             game records (one line per game)
      eval_cases/<session_id>/<game_id>.jsonl  per-game eval-case sidecars

The folder name is a human slug; the *structured truth* (store version, models, factions,
git sha) lives inside ``config.json`` — so runs are discoverable by querying manifests
rather than by hoping a token is in the filename.

Legacy (no ``--experiment``) keeps the historical flat layout byte-for-byte; nothing here
changes a run that doesn't opt in.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
BATCH_ROOT = REPO_ROOT / "batch_results"


def experiment_dir(experiment: str) -> Path:
    return BATCH_ROOT / experiment


def games_dir(experiment: str) -> Path:
    return experiment_dir(experiment) / "games"


def eval_cases_dir(experiment: str) -> Path:
    return experiment_dir(experiment) / "eval_cases"


def game_records_path(experiment: str, session_prefix: str) -> Path:
    return games_dir(experiment) / f"{session_prefix}.jsonl"


def eval_cases_path(experiment: str, session_id: str, game_id: str) -> Path:
    return eval_cases_dir(experiment) / session_id / f"{game_id}.jsonl"


def config_path(experiment: str) -> Path:
    return experiment_dir(experiment) / "config.json"


def summary_path(experiment: str) -> Path:
    return experiment_dir(experiment) / "summary.json"


def config_overview(
    resolved_config: dict[str, Any], runtime_fingerprint: Any = None
) -> dict[str, Any]:
    """An at-a-glance block hoisted to the top of ``config.json`` — the gist a
    reader needs (store, arms, scale, model) without descending into the full
    ``resolved_config``.

    Arms are summarised as the *enabled factions* per arm, so an arms-race slip
    (an arm enabling more roles than the experiment intended — the v2_full trap)
    is visible at the top of the file instead of buried in per-role flag maps.
    """
    fp = runtime_fingerprint
    if hasattr(fp, "model_dump"):  # accept a pydantic fingerprint or a plain dict
        fp = fp.model_dump()
    fp = fp or {}

    memory_configs = resolved_config.get("memory_configs") or {}
    arms = {
        name: sorted(role for role, enabled in (flags or {}).items() if enabled)
        for name, flags in memory_configs.items()
    }
    pinned = resolved_config.get("game_ids_pinned")
    persistence = resolved_config.get("memory_persistence_config") or {}
    return {
        "store": persistence.get("seed_store_dir"),
        "arms": arms,
        "n_games_per_arm": (
            len(pinned) if pinned else resolved_config.get("runs_per_config")
        ),
        "paired": bool(pinned),
        "model": fp.get("game_model"),
        "backend": fp.get("llm_backend"),
        "git": fp.get("git_commit"),
    }


def build_loop_descriptor(
    experiment: str,
    loop_config: dict[str, Any],
    *,
    base_store: str | None,
    configs: str,
    created_at: str,
    argv: list[str],
    run_dir: str,
) -> dict[str, Any]:
    """The loop campaign's config.json mirror — echoes the standalone shape (a scannable
    ``overview`` first, then the full config) but sourced from ``asdict(LoopConfig)``.

    Pure intent: the DECLARED ``expect_factions`` lives here; the ACTUAL per-gen enabled
    factions + runtime fingerprint are recorded by the driver in loop_history.json /
    run_meta.json, so declared-vs-actual is inspectable across the campaign folder.
    """
    return {
        "experiment": experiment,
        "kind": "loop",
        "overview": {
            "store": base_store,
            "arm_config": configs,
            "expect_factions": loop_config.get("expect_factions"),
            "model": loop_config.get("model"),
            "generations": loop_config.get("generations"),
            "games_per_generation": loop_config.get("games_per_generation"),
            "off_baseline": loop_config.get("off_baseline"),
            "discussion_mode": loop_config.get("discussion_mode"),
        },
        "created_at": created_at,
        "source": {"argv": argv, "run_dir": run_dir},
        "loop_config": loop_config,
    }


def write_run_config(experiment: str, config: dict[str, Any]) -> Path:
    """Write the experiment's config mirror, **write-if-absent**.

    The first writer wins: a loop driver that pre-stamps the richer ``LoopConfig``
    is not clobbered by the per-(gen, arm) ``run_batch`` calls underneath it, and a
    re-run that reuses the same experiment id keeps the original recipe.
    """
    path = config_path(experiment)
    if path.exists():
        return path
    path.parent.mkdir(parents=True, exist_ok=True)
    # No sort_keys: preserve insertion order so the at-a-glance keys (experiment,
    # description, overview) stay at the top where a reader scans first.
    path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    return path


def merge_run_summary(
    experiment: str, session_prefix: str, outcome: dict[str, Any]
) -> Path:
    """Merge one invocation's outcome into ``summary.json`` keyed by ``session_prefix``.

    Keyed-merge (not overwrite) so a multi-invocation loop campaign accumulates a
    per-(gen, arm) breakdown instead of each call clobbering the last.
    """
    path = summary_path(experiment)
    path.parent.mkdir(parents=True, exist_ok=True)
    data: dict[str, Any] = {"runs": {}}
    if path.exists():
        try:
            loaded = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                data = loaded
        except (json.JSONDecodeError, OSError):
            data = {"runs": {}}
    data.setdefault("runs", {})[session_prefix] = outcome
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path
