from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel

from Agents.schemas.evaluation import EvalCase


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
    action_type: str
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
        action_type=case.action_type,
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
