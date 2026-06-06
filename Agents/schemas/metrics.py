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
    serial_killer_target: str | None = None
    serial_killer_target_role: str | None = None
    vigilante_target: str | None = None
    vigilante_target_role: str | None = None
    # Resolved at the night-resolution node (single source of truth for heal + SK
    # night-immunity), so downstream metrics never re-derive the kill rules.
    serial_killer_kill_landed: bool = False
    vigilante_kill_landed: bool = False
    deaths: list[str] = Field(default_factory=list)
    # Faction sizes entering the night (after any day lynch, before night deaths).
    wolves_before: int = 0
    town_before: int = 0
    sk_before: int = 0


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

    # Day eliminations. Town perspective: BOTH wolf and SK are enemies (the SK can
    # only be removed by a day-vote), so "correct" = wolf+SK; a mislynch = a town member.
    total_eliminations: int
    wolf_eliminations: int
    sk_eliminations: int
    anti_town_eliminations: int      # wolf + SK lynched
    town_mislynches: int             # town-aligned (villager/healer/investigator/vigilante) lynched
    serial_killer_lynched: int       # 0/1 — the village's key success vs the 3rd faction
    tie_count: int
    no_vote_count: int

    # Town voting, per individual vote (denser than the group elimination outcome).
    town_votes_total: int            # non-abstain votes cast by town-aligned players
    town_votes_on_threat: int        # ... that targeted a wolf or the SK

    # Healer — intercepts of ANY attacker (wolf/SK/vigilante), classified by the saved
    # player's faction. A save is good iff the saved player is town; saving a wolf is
    # counterproductive ("friendly-fire"). Denominator = action-nights (attacks always
    # happen when attackers are alive, so this is already opportunity-normalized).
    healer_action_nights: int
    healer_saves_total: int
    healer_town_saves: int
    healer_ff_saves: int             # saved a wolf
    healer_wolf_blocks: int          # saved the wolves' target (legacy `healer_saved` meaning)
    healer_exit_method: str

    # Investigator — threat = wolf or SK. mean_chance is the random-hit baseline across
    # investigation nights (threats_alive / investigable_alive) for the lift de-luck.
    investigator_investigations_total: int
    investigator_wolf_finds: int
    investigator_threat_finds: int   # wolf + SK
    investigator_found_wolf_day: int | None
    investigator_mean_chance: float | None
    investigator_exit_method: str

    # Wolves
    wolf_killed_healer_day: int | None
    wolf_killed_investigator_day: int | None
    power_roles_killed_by_wolves: int
    wolf_power_target_nights: int    # wolves targeted a live power role (numerator)
    power_role_alive_nights: int     # nights >=1 power role was alive (opportunity denom)
    mislynch_days_total: int         # town-lynch days
    mislynch_days_steered: int
    wolf_elim_days_total: int
    wolf_elim_days_blended: int
    wolf_elim_days_dissented: int

    # Serial killer — survival is the core (dense) proxy; SK wins by outlasting.
    sk_nights_survived: int
    sk_kills_landed: int
    sk_exit_method: str

    # Vigilante — shooting a wolf/SK is good; shooting town is friendly fire; holding
    # fire is a legitimate choice (never penalized). Raw counts, not a forced rate.
    vigilante_shots_taken: int
    vigilante_evil_shots: int
    vigilante_friendly_fire_shots: int
    vigilante_bullets_unused: int
    vigilante_exit_method: str


class DerivedGameMetrics(BaseModel):
    # Town (faction-aware; "correct" credits the SK-lynch)
    correct_elimination_rate: float | None = None   # anti-town (wolf+SK) / total eliminations
    wolf_elimination_rate: float | None = None
    town_mislynch_rate: float | None = None
    town_vote_accuracy: float | None = None
    # Healer
    healer_save_rate: float | None = None
    healer_town_save_rate: float | None = None
    healer_friendly_fire_save_rate: float | None = None
    healer_wolf_block_rate: float | None = None
    # Investigator
    investigator_threat_find_rate: float | None = None
    investigator_threat_find_lift: float | None = None   # rate ÷ random baseline (de-lucked)
    investigator_wolf_find_rate: float | None = None
    # Wolves
    wolf_steering_rate: float | None = None
    wolf_blending_rate: float | None = None
    wolf_dissent_rate: float | None = None
    wolf_power_role_targeting_rate: float | None = None
    # Vigilante
    vigilante_correct_shot_rate: float | None = None


# ---------------------------------------------------------------------------
# Public output model — the self-contained analysis artifact
# ---------------------------------------------------------------------------


class ComputedGameMetrics(DerivedGameMetrics):
    winner: str
    game_length: int
    # Town
    mislynches: int                  # town-member lynches (count)
    serial_killer_lynched: int
    tie_count: int
    no_vote_count: int
    # Healer
    healer_save_count: int
    healer_exit_method: str
    # Investigator
    investigator_exit_method: str
    investigator_wolves_found: int
    investigator_found_wolf_day: int | None = None
    # Wolves
    power_roles_killed_by_wolves: int
    wolf_killed_healer_day: int | None = None
    wolf_killed_investigator_day: int | None = None
    # Serial killer
    sk_nights_survived: int
    sk_exit_method: str
    sk_kills_landed: int
    # Vigilante
    vigilante_shots_taken: int
    vigilante_evil_shots: int
    vigilante_friendly_fire_shots: int
    vigilante_bullets_unused: int
    vigilante_exit_method: str


@dataclass
class GameOutcome:
    result: dict
    game_metrics: ComputedGameMetrics
