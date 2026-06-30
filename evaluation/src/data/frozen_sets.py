"""Read and write local frozen evaluation datasets as JSONL.

Every case type freezes into its own record (``*DatasetRecord``) that wraps the
case with a stable ``case_id`` + dataset/provenance fields. The JSONL read/write
mechanics are identical across types, so they live in two generic helpers
(``_read_jsonl_records`` / ``_write_jsonl_records``); the per-type ``read_*`` /
``write_*`` functions stay as thin, typed wrappers so callers keep a precise
return type and a stable import surface.
"""

from __future__ import annotations

from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel

from Agents.schemas.evaluation import (
    DaySummaryCase,
    DedupCase,
    EvalCase,
    ExtractionCase,
)

_RecordT = TypeVar("_RecordT", bound=BaseModel)


def _read_jsonl_records(
    path: Path, model: type[_RecordT], label: str
) -> list[_RecordT]:
    """Parse a JSONL file into validated *model* records; *label* names the type
    in the error raised on a malformed line."""
    records: list[_RecordT] = []
    with path.open(encoding="utf-8") as file:
        for line_number, line in enumerate(file, 1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                records.append(model.model_validate_json(stripped))
            except Exception as exc:
                raise ValueError(
                    f"Invalid {label} on line {line_number} of {path}: {exc}"
                ) from exc
    return records


def _write_jsonl_records(path: Path, records: list[BaseModel]) -> None:
    """Write Pydantic records to JSONL, creating parent dirs as needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        for record in records:
            file.write(record.model_dump_json() + "\n")


# ---------------------------------------------------------------------------
# Agent-decision (EvalCase) dataset records
# ---------------------------------------------------------------------------


class EvalDatasetRecord(BaseModel):
    eval_set_id: str
    case_id: str
    trace_id: str
    observation_id: str
    span_name: str
    player_id: str
    player_role: str
    day: int
    round: int
    action_phase: str
    created_from: str | None = None
    eval_case: EvalCase


def case_id(case: EvalCase) -> str:
    return f"{case.trace_id}:{case.observation_id}"


def record_from_case(
    case: EvalCase,
    eval_set_id: str,
    created_from: str | None = None,
) -> EvalDatasetRecord:
    return EvalDatasetRecord(
        eval_set_id=eval_set_id,
        case_id=case_id(case),
        trace_id=case.trace_id,
        observation_id=case.observation_id,
        span_name=case.span_name,
        player_id=case.player_id,
        player_role=case.player_role,
        day=case.day,
        round=case.round,
        action_phase=case.action_phase,
        created_from=created_from,
        eval_case=case,
    )


def read_eval_dataset(path: Path) -> list[EvalDatasetRecord]:
    return _read_jsonl_records(path, EvalDatasetRecord, "eval dataset record")


def write_eval_dataset(path: Path, records: list[EvalDatasetRecord]) -> None:
    _write_jsonl_records(path, records)


# ---------------------------------------------------------------------------
# Extraction dataset records
# ---------------------------------------------------------------------------


class ExtractionDatasetRecord(BaseModel):
    eval_set_id: str
    case_id: str
    trace_id: str
    observation_id: str
    span_name: str
    game_id: str
    game_outcome: str
    created_from: str | None = None
    extraction_case: ExtractionCase


def extraction_record_from_case(
    case: ExtractionCase,
    eval_set_id: str,
    created_from: str | None = None,
) -> ExtractionDatasetRecord:
    return ExtractionDatasetRecord(
        eval_set_id=eval_set_id,
        case_id=f"{case.trace_id}:{case.observation_id}",
        trace_id=case.trace_id,
        observation_id=case.observation_id,
        span_name=case.span_name,
        game_id=case.game_id,
        game_outcome=case.game_outcome,
        created_from=created_from,
        extraction_case=case,
    )


def read_extraction_dataset(path: Path) -> list[ExtractionDatasetRecord]:
    return _read_jsonl_records(path, ExtractionDatasetRecord, "extraction record")


def write_extraction_dataset(
    path: Path, records: list[ExtractionDatasetRecord]
) -> None:
    _write_jsonl_records(path, records)


# ---------------------------------------------------------------------------
# Day-summary dataset records
# ---------------------------------------------------------------------------


class DaySummaryDatasetRecord(BaseModel):
    eval_set_id: str
    case_id: str
    trace_id: str
    observation_id: str
    span_name: str
    game_id: str
    day: int
    created_from: str | None = None
    day_summary_case: DaySummaryCase


def day_summary_record_from_case(
    case: DaySummaryCase,
    eval_set_id: str,
    created_from: str | None = None,
) -> DaySummaryDatasetRecord:
    return DaySummaryDatasetRecord(
        eval_set_id=eval_set_id,
        case_id=f"{case.trace_id}:{case.observation_id}",
        trace_id=case.trace_id,
        observation_id=case.observation_id,
        span_name=case.span_name,
        game_id=case.game_id,
        day=case.day,
        created_from=created_from,
        day_summary_case=case,
    )


def read_day_summary_dataset(path: Path) -> list[DaySummaryDatasetRecord]:
    return _read_jsonl_records(
        path, DaySummaryDatasetRecord, "day-summary record"
    )


def write_day_summary_dataset(
    path: Path, records: list[DaySummaryDatasetRecord]
) -> None:
    _write_jsonl_records(path, records)


# ---------------------------------------------------------------------------
# Dedup dataset records
# ---------------------------------------------------------------------------


class DedupDatasetRecord(BaseModel):
    eval_set_id: str
    case_id: str
    trace_id: str
    observation_id: str
    span_name: str
    game_id: str
    item_type: str
    perspective: str
    action_phase: str
    decision: str
    auto: bool
    created_from: str | None = None
    dedup_case: DedupCase


def dedup_record_from_case(
    case: DedupCase,
    eval_set_id: str,
    created_from: str | None = None,
) -> DedupDatasetRecord:
    return DedupDatasetRecord(
        eval_set_id=eval_set_id,
        case_id=f"{case.trace_id}:{case.observation_id}",
        trace_id=case.trace_id,
        observation_id=case.observation_id,
        span_name=case.span_name,
        game_id=case.game_id,
        item_type=case.item_type,
        perspective=case.perspective,
        action_phase=case.action_phase,
        decision=case.decision,
        auto=case.auto,
        created_from=created_from,
        dedup_case=case,
    )


def read_dedup_dataset(path: Path) -> list[DedupDatasetRecord]:
    return _read_jsonl_records(path, DedupDatasetRecord, "dedup record")


def write_dedup_dataset(path: Path, records: list[DedupDatasetRecord]) -> None:
    _write_jsonl_records(path, records)


# ---------------------------------------------------------------------------
# Auto-dedup calibration dataset records
# ---------------------------------------------------------------------------


class AutoDedupRecord(BaseModel):
    eval_set_id: str
    case_index: int
    game_id: str
    item_type: str
    perspective: str
    action_phase: str
    new_entry: dict
    candidates: list[dict]
    situation_sim: float
    embedding_scores: dict[str, float] | None = None


def read_auto_dedup_dataset(path: Path) -> list[AutoDedupRecord]:
    return _read_jsonl_records(path, AutoDedupRecord, "auto-dedup record")


def write_auto_dedup_dataset(path: Path, records: list[AutoDedupRecord]) -> None:
    _write_jsonl_records(path, records)
