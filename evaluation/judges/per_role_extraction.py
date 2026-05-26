"""Per-role extraction judge — evaluates each role's items separately."""

from __future__ import annotations

from Agents.schemas.evaluation import ExtractionCase
from evaluation.core.schemas import (
    PerRoleExtractionResult,
    PerRoleExtractionScores,
)
from evaluation.judges.extraction import DEFAULT_JUDGE_MODEL, run_extraction_judge

ROLES = ["wolf", "villager", "healer", "investigator"]


def filter_items_by_role(items: list[dict], role: str) -> list[dict]:
    return [item for item in items if item.get("perspective") == role]


def run_per_role_extraction_judge(
    case: ExtractionCase,
    model: str = DEFAULT_JUDGE_MODEL,
    roles: list[str] | None = None,
    max_retries: int = 1,
) -> PerRoleExtractionScores:
    roles = roles or ROLES
    results: list[PerRoleExtractionResult] = []
    for role in roles:
        filtered_obs = filter_items_by_role(case.observations, role)
        filtered_sp = filter_items_by_role(case.strategy_points, role)
        if not filtered_obs and not filtered_sp:
            continue
        filtered_case = ExtractionCase(
            game_id=case.game_id,
            game_outcome=case.game_outcome,
            roles=case.roles,
            formatted_discussions=case.formatted_discussions,
            formatted_strategy_notes=case.formatted_strategy_notes,
            observations=filtered_obs,
            strategy_points=filtered_sp,
            model_used=case.model_used,
        )
        scores = run_extraction_judge(
            filtered_case, model=model, max_retries=max_retries
        )
        results.append(
            PerRoleExtractionResult(
                role=role,
                observation_count=len(filtered_obs),
                strategy_point_count=len(filtered_sp),
                scores=scores,
            )
        )
    return PerRoleExtractionScores(role_results=results)
