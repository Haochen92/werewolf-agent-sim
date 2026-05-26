"""Read and write local frozen evaluation datasets as JSONL."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel

from Agents.schemas.evaluation import DedupCase, EvalCase, ExtractionCase


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
    records: list[EvalDatasetRecord] = []
    with path.open(encoding="utf-8") as file:
        for line_number, line in enumerate(file, 1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                records.append(EvalDatasetRecord.model_validate_json(stripped))
            except Exception as exc:
                raise ValueError(
                    f"Invalid eval dataset record on line {line_number} of {path}: {exc}"
                ) from exc
    return records


def write_eval_dataset(path: Path, records: list[EvalDatasetRecord]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        for record in records:
            file.write(record.model_dump_json() + "\n")


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
    records: list[ExtractionDatasetRecord] = []
    with path.open(encoding="utf-8") as file:
        for line_number, line in enumerate(file, 1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                records.append(
                    ExtractionDatasetRecord.model_validate_json(stripped)
                )
            except Exception as exc:
                raise ValueError(
                    f"Invalid extraction record on line {line_number} of {path}: {exc}"
                ) from exc
    return records


def write_extraction_dataset(
    path: Path, records: list[ExtractionDatasetRecord]
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        for record in records:
            file.write(record.model_dump_json() + "\n")


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
    records: list[DedupDatasetRecord] = []
    with path.open(encoding="utf-8") as file:
        for line_number, line in enumerate(file, 1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                records.append(DedupDatasetRecord.model_validate_json(stripped))
            except Exception as exc:
                raise ValueError(
                    f"Invalid dedup record on line {line_number} of {path}: {exc}"
                ) from exc
    return records


def write_dedup_dataset(path: Path, records: list[DedupDatasetRecord]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        for record in records:
            file.write(record.model_dump_json() + "\n")


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
    records: list[AutoDedupRecord] = []
    with path.open(encoding="utf-8") as file:
        for line_number, line in enumerate(file, 1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                records.append(AutoDedupRecord.model_validate_json(stripped))
            except Exception as exc:
                raise ValueError(
                    f"Invalid auto-dedup record on line {line_number} of {path}: {exc}"
                ) from exc
    return records


def write_auto_dedup_dataset(path: Path, records: list[AutoDedupRecord]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        for record in records:
            file.write(record.model_dump_json() + "\n")
