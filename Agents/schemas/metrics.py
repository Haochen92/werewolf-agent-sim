from __future__ import annotations

from dataclasses import dataclass
from typing import TypedDict

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Raw metric accumulators — populated during the game
# ---------------------------------------------------------------------------


class DayResolutionMetric(BaseModel):
    day: int
    votes: list[dict[str, str]]
    voted_player: str | None
    voted_player_role: str | None
    vote_counts: dict[str, int]
    tied_players: list[str]
    no_vote: bool


class NightResolutionMetric(BaseModel):
    day: int
    wolves_target: str | None
    wolf_target_role: str | None
    healer_target: str | None
    investigator_target: str | None
    investigator_target_role: str | None
    kill_successful: bool
    healer_saved: bool


class Metrics(BaseModel):
    day_resolutions: list[DayResolutionMetric] = Field(default_factory=list)
    night_resolutions: list[NightResolutionMetric] = Field(default_factory=list)


class GraphContext(TypedDict):
    metrics: Metrics


# ---------------------------------------------------------------------------
# Internal intermediate models — used by the computation pipeline
# ---------------------------------------------------------------------------


class BaseGameMetrics(BaseModel):
    winner: str
    game_length: int

    mislynches: int
    total_eliminations: int
    wolf_eliminations: int
    tie_count: int
    no_vote_count: int

    healer_save_count: int
    healer_nights_alive: int
    healer_exit_method: str

    investigator_found_wolf_day: int | None
    investigator_wolves_found: int
    investigator_investigations_total: int
    investigator_exit_method: str

    wolf_killed_healer_day: int | None
    wolf_killed_investigator_day: int | None
    power_roles_killed_by_wolves: int
    wolf_power_role_target_nights: int
    wolf_kill_nights_total: int

    mislynch_days_total: int
    mislynch_days_steered: int
    wolf_elim_days_total: int
    wolf_elim_days_blended: int
    wolf_elim_days_dissented: int


class DerivedGameMetrics(BaseModel):
    correct_elimination_rate: float | None = None
    healer_save_rate: float | None = None
    investigator_accuracy: float | None = None
    wolf_steering_rate: float | None = None
    wolf_blending_rate: float | None = None
    wolf_dissent_rate: float | None = None
    wolf_power_role_targeting_rate: float | None = None


# ---------------------------------------------------------------------------
# Public output model — the self-contained analysis artifact
# ---------------------------------------------------------------------------


class ComputedGameMetrics(DerivedGameMetrics):
    # Always present
    winner: str
    game_length: int
    mislynches: int
    healer_save_count: int
    healer_exit_method: str
    investigator_exit_method: str
    investigator_wolves_found: int
    power_roles_killed_by_wolves: int
    tie_count: int
    no_vote_count: int

    # Nullable (non-derived)
    investigator_found_wolf_day: int | None = None
    wolf_killed_healer_day: int | None = None
    wolf_killed_investigator_day: int | None = None


@dataclass
class GameOutcome:
    result: dict
    game_metrics: ComputedGameMetrics
