"""Metric models: raw per-decision accumulators, the derived per-game proxies, and the public
analysis artifact.

All internal — serialized to batch records / tracing, never sent to a model. The decision-quality
proxy design (de-lucked, opportunity-normalized rates; win rate stays headline) is documented in
evidence/metrics/. Field-level meaning is kept in inline comments next to each count.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, NotRequired, TypedDict

from pydantic import BaseModel, Field

from Agents.observability.case_sink import EvalCaseSink


# ---------------------------------------------------------------------------
# Raw metric accumulators — populated during the game
# ---------------------------------------------------------------------------


class DayResolutionMetric(BaseModel):
    """Raw record of one day's vote resolution: who was lynched, the counts, ties, no-vote."""

    day: int
    votes: list[dict[str, str]]
    voted_player: str | None
    voted_player_role: str | None
    vote_counts: dict[str, int]
    tied_players: list[str]
    no_vote: bool


class NightResolutionMetric(BaseModel):
    """Raw record of one night's resolution (targets, deaths, kill-landed flags). Built at the
    night-resolution node — the single source of truth for heal + SK night-immunity rules."""

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
    """Per-game accumulator of the day + night resolution records (lives on GraphContext)."""

    day_resolutions: list[DayResolutionMetric] = Field(default_factory=list)
    night_resolutions: list[NightResolutionMetric] = Field(default_factory=list)
    # Post-game memory-pipeline dedup outcomes, keyed by item type
    # ("observations" / "strategy_points") -> DedupStats dump. Populated only when
    # extraction persists (dump on); empty for extraction-off / no-dump games. Lets
    # a seeding batch track per-game absorption (store saturation) from the record.
    dedup_stats: dict[str, Any] = Field(default_factory=dict)


class GraphContext(TypedDict):
    """Runtime context threaded through the graph; carries the live Metrics accumulator."""

    metrics: Metrics
    eval_sink: NotRequired[EvalCaseSink]
    """Local eval-case accumulator (the tee beside the Langfuse span dump).
    NotRequired + ``.get()``-accessed everywhere so contexts built without it
    (tests, ad-hoc invokes) keep working; emission is then Langfuse-only."""


# ---------------------------------------------------------------------------
# Internal intermediate models — used by the computation pipeline
# ---------------------------------------------------------------------------


class BaseGameMetrics(BaseModel):
    """Raw per-game counts derived from the resolutions — numerators plus their opportunity
    denominators — before any rates are taken. Per-field meaning in the inline comments below."""

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
    investigator_finds_total: int      # nights a wolf was confirmed (conversion denominator)
    investigator_finds_lynched: int    # of those, the confirmed wolf was lynched on a later day
    investigator_exit_method: str

    # Wolves
    wolf_killed_healer_day: int | None
    wolf_killed_investigator_day: int | None
    power_roles_killed_by_wolves: int
    power_roles_killed_by_evil: int  # wolf + SK night-kills of power roles (threat-generic; the stronger town-protection proxy)
    wolf_power_target_nights: int    # wolves targeted a live power role (numerator)
    power_role_alive_nights: int     # nights >=1 power role was alive (opportunity denom)
    mislynch_days_total: int         # town-lynch days
    mislynch_days_steered: int
    wolf_elim_days_total: int
    wolf_elim_days_blended: int
    wolf_elim_days_dissented: int
    wolf_blend_votes_aligned: int   # living wolf votes aligned w/ the day's lynch, ALL lynch days
    wolf_blend_votes_total: int      # all living wolf votes on lynch days (excl. self being lynched)

    # Serial killer — survival is the core (dense) proxy; SK wins by outlasting.
    sk_nights_survived: int
    sk_kills_landed: int
    sk_power_roles_killed: int        # SK night-kills landing on a power role (offense)
    sk_wolf_kills: int                # SK night-kills landing on a WOLF — cross-faction targeting (the 2v1-avoidance skill)
    sk_blend_votes_aligned: int       # SK votes aligned w/ the day's lynch (numerator of sk blending)
    sk_blend_votes_total: int         # SK votes on lynch days (denominator; 0 -> rate None)
    wolf_suspicion_drawn: float | None  # per-member alive-window votes-at-wolf share (outcome-proximate + opponent-coupled)
    sk_suspicion_drawn: float | None    # per-member alive-window votes-at-SK share (outcome-proximate: precursor to its only removal)
    sk_exit_method: str

    # Vigilante — shooting a wolf/SK is good; shooting town is friendly fire; holding
    # fire is a legitimate choice (never penalized). Raw counts, not a forced rate.
    vigilante_shots_taken: int
    vigilante_evil_shots: int
    vigilante_wolf_kills: int         # landed kills on wolves only (the SK can't be removed at night)
    vigilante_loadout: int            # starting bullet supply = the wolf-kill-rate denominator (0 if no vigilante)
    vigilante_friendly_fire_shots: int
    vigilante_bullets_unused: int
    vigilante_skconfirms_total: int   # nights the vigilante shot the (immune) SK = confirmed it
    vigilante_skconfirms_lynched: int # of those, the confirmed SK was lynched on a later day
    vigilante_exit_method: str


class DerivedGameMetrics(BaseModel):
    """Rate/ratio proxies computed from BaseGameMetrics (de-lucked where noted). Each is None when
    its denominator is zero (the role never had the opportunity), so absence != zero performance."""

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
    investigator_find_to_lynch_rate: float | None = None  # CONVERSION: confirmed wolf -> lynched (validated +0.40; gauges the bottleneck)
    # Wolves
    wolf_steering_rate: float | None = None
    wolf_blending_rate: float | None = None              # conditioned on wolf-elim days (disaster-state only)
    wolf_unconditioned_blending_rate: float | None = None  # all lynch days — the validated camouflage proxy
    wolf_dissent_rate: float | None = None
    wolf_power_role_targeting_rate: float | None = None
    # Serial killer (offense; survival is the core but outcome-proximate — see ComputedGameMetrics)
    sk_kill_rate: float | None = None                        # kills / nights survived (de-lucked offense)
    sk_unconditioned_blending_rate: float | None = None      # SK day-vote camouflage (SUGGESTIVE: p=.019, fails Bonferroni)
    wolf_suspicion_drawn: float | None = None                # concealment OUTCOME (per-member alive-window) — outcome-proximate + opponent-coupled
    sk_suspicion_drawn: float | None = None                  # concealment OUTCOME — most outcome-proximate (≈ "got lynched"); not a clean skill proxy
    # Vigilante
    vigilante_correct_shot_rate: float | None = None         # conditional precision (evil hits / shots); underpowered descriptor
    vigilante_wolf_kills_rate: float | None = None           # landed wolf-kills / bullet supply — the de-lucked removal proxy (validated)
    vigilante_skconfirm_to_lynch_rate: float | None = None   # CONVERSION: confirmed SK -> lynched (promising, underpowered n~9)


# ---------------------------------------------------------------------------
# Public output model — the self-contained analysis artifact
# ---------------------------------------------------------------------------


class ComputedGameMetrics(DerivedGameMetrics):
    """The self-contained per-game analysis artifact: the derived rates plus the raw counts they
    were computed from, so a record is interpretable without re-deriving."""

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
    investigator_finds_total: int = 0      # conversion denominator (filter low-sample games)
    investigator_finds_lynched: int = 0
    # Wolves
    power_roles_killed_by_wolves: int
    power_roles_killed_by_evil: int
    wolf_killed_healer_day: int | None = None
    wolf_killed_investigator_day: int | None = None
    wolf_blend_votes_aligned: int = 0   # numerator of wolf_unconditioned_blending_rate
    wolf_blend_votes_total: int = 0      # denominator (0 -> rate is None); carry it to filter low-sample games
    # Serial killer
    sk_nights_survived: int
    sk_exit_method: str
    sk_kills_landed: int
    sk_power_roles_killed: int = 0
    sk_wolf_kills: int = 0
    sk_blend_votes_total: int = 0     # denominator for sk blending (filter low-sample games)
    # Vigilante
    vigilante_shots_taken: int
    vigilante_evil_shots: int
    vigilante_wolf_kills: int
    vigilante_skconfirms_total: int = 0    # conversion denominator (filter low-sample games)
    vigilante_skconfirms_lynched: int = 0
    vigilante_friendly_fire_shots: int
    vigilante_bullets_unused: int
    vigilante_exit_method: str


@dataclass
class GameOutcome:
    """A finished game's bundle: the raw result dict, the computed metrics, and (optionally) the
    raw per-decision accumulators for re-derivation downstream."""

    result: dict
    game_metrics: ComputedGameMetrics
    # Raw per-decision accumulators (day_resolutions + night_resolutions) as a
    # json-safe dict, so a batch record can dump the per-night decisions (targets,
    # deaths, kill-landed) — not just the derived proxies in game_metrics.
    raw_metrics: dict | None = None
    game_id: str = ""
    """The game's pinned id (scheduler seed source; also keys the eval-case sidecar)."""
    trace_id: str = ""
    """Langfuse trace id of the game's root span — links the batch record to the trace."""
    eval_records: list[dict] | None = None
    """Locally-emitted eval cases as normalized span dicts (see
    Agents.observability.case_sink); run_batch persists them as a per-game sidecar."""
