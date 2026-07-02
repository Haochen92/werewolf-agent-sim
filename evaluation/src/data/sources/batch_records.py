"""Batch-record source: read repo-root ``batch_results/*.jsonl`` game-run logs.

The read side for the whole-game run records that ``run_batch`` writes (one JSONL line per game,
``status``/``winner``/``day_resolutions``/… — the game outcome, not per-turn eval cases). Distinct
from ``sources/sidecar.py``, which reads the per-game eval-case sidecars nested under
``batch_results/eval_cases/``: this module reads the top-level game logs, sidecar reads the cases.

Extracted because the deterministic $0 audits (``audits/`` + ``audits/metrics_common``) and the
``studies/investigator_transmission`` runner each hand-rolled the same
glob → read lines → ``json.loads`` → filter ``status == "success"`` loop; kept in one place so the
"what counts as a loadable record" rule can't silently drift between them.
"""

from __future__ import annotations

import json
from pathlib import Path

from evaluation.src.core.settings import REPO_ROOT


def read_records_file(path: Path | str, *, require_success: bool = True) -> list[dict]:
    """Parse one ``batch_results`` JSONL file → list of record dicts.

    Skips blank lines; with ``require_success`` (default) keeps only ``status == "success"`` records.
    Reads the file directly (raises ``FileNotFoundError`` if it is missing — callers that name an
    explicit file rely on that).
    """
    records: list[dict] = []
    for line in Path(path).read_text().splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        if require_success and record.get("status") != "success":
            continue
        records.append(record)
    return records


def load_batch_records(glob_pattern: str, *, require_success: bool = True) -> list[dict]:
    """All records across the ``batch_results`` files matching ``glob_pattern`` (repo-root-relative).

    Files are read in sorted-path order and concatenated into one flat list. Missing matches simply
    contribute nothing (glob only yields existing files).
    """
    records: list[dict] = []
    for path in sorted(REPO_ROOT.glob(glob_pattern)):
        records.extend(read_records_file(path, require_success=require_success))
    return records
