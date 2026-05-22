import hashlib

from Agents.schemas.metrics import (
    BaseGameMetrics,
    ComputedGameMetrics,
    DerivedGameMetrics,
    Metrics,
)
from Agents.tracing import langfuse


def _score_id(*parts: str) -> str:
    return hashlib.sha256(":".join(parts).encode("utf-8")).hexdigest()[:16]


def _safe_div(numerator: int, denominator: int) -> float | None:
    return numerator / denominator if denominator > 0 else None


# ---------------------------------------------------------------------------
# Computation pipeline
# ---------------------------------------------------------------------------


def _compute_base_metrics(result: dict, metrics: Metrics) -> BaseGameMetrics:
    roles = result["roles"]
    survivors = result["surviving_wolves"] + result["surviving_villagers"]

    healer_id = next(p for p, r in roles.items() if r == "healer")
    investigator_id = next(p for p, r in roles.items() if r == "investigator")

    # --- Tier 1: straight from final state ---
    winner = result["winner"]
    game_length = result["current_day"]

    # --- Tier 2: single pass over day resolutions ---

    mislynches = 0
    total_eliminations = 0
    wolf_eliminations = 0

    for day in metrics.day_resolutions:
        if day.voted_player is not None:
            total_eliminations += 1
            if day.voted_player_role != "wolf":
                mislynches += 1
            else:
                wolf_eliminations += 1

    tie_count = sum(1 for d in metrics.day_resolutions if d.tied_players)
    no_vote_count = sum(1 for d in metrics.day_resolutions if d.no_vote)

    # --- Tier 3: single pass over night resolutions ---

    healer_save_count = sum(
        1 for n in metrics.night_resolutions if n.healer_saved
    )

    healer_nights_alive = sum(
        1 for n in metrics.night_resolutions if n.healer_target is not None
    )

    investigator_found_wolf_day = next(
        (n.day for n in metrics.night_resolutions
         if n.investigator_target_role == "wolf"),
        None,
    )

    investigator_wolves_found = sum(
        1 for n in metrics.night_resolutions
        if n.investigator_target_role == "wolf"
    )

    investigator_investigations_total = sum(
        1 for n in metrics.night_resolutions
        if n.investigator_target is not None
    )

    wolf_killed_healer_day = next(
        (n.day for n in metrics.night_resolutions
         if n.wolves_target == healer_id and n.kill_successful),
        None,
    )

    wolf_killed_investigator_day = next(
        (n.day for n in metrics.night_resolutions
         if n.wolves_target == investigator_id and n.kill_successful),
        None,
    )

    power_roles_killed_by_wolves = sum(
        1 for n in metrics.night_resolutions
        if n.kill_successful
        and n.wolf_target_role in ("healer", "investigator")
    )

    wolf_power_role_target_nights = sum(
        1 for n in metrics.night_resolutions
        if n.wolves_target in (healer_id, investigator_id)
    )

    wolf_kill_nights_total = len(metrics.night_resolutions)

    # --- Tier 4: wolf voting behavior ---

    mislynch_days_steered = 0
    mislynch_days_total = 0
    wolf_elim_days_blended = 0
    wolf_elim_days_dissented = 0
    wolf_elim_days_total = 0

    for day in metrics.day_resolutions:
        if day.voted_player is None:
            continue

        wolf_votes = [v for v in day.votes if roles.get(v["voter"]) == "wolf"]
        if not wolf_votes:
            continue

        wolves_voted_with_majority = sum(
            1 for v in wolf_votes if v["votee"] == day.voted_player
        )
        majority_of_wolves_aligned = wolves_voted_with_majority > len(wolf_votes) / 2

        if day.voted_player_role != "wolf":
            mislynch_days_total += 1
            if majority_of_wolves_aligned:
                mislynch_days_steered += 1
        else:
            surviving_wolf_votes = [
                v for v in day.votes
                if roles.get(v["voter"]) == "wolf"
                and v["voter"] != day.voted_player
            ]

            if not surviving_wolf_votes:
                continue

            surviving_wolves_voted_for_eliminated_wolf = sum(
                1 for v in surviving_wolf_votes
                if v["votee"] == day.voted_player
            )

            majority_of_surviving_wolves_aligned = (
                surviving_wolves_voted_for_eliminated_wolf
                > len(surviving_wolf_votes) / 2
            )

            wolf_elim_days_total += 1

            if majority_of_surviving_wolves_aligned:
                wolf_elim_days_blended += 1
            else:
                wolf_elim_days_dissented += 1

    # --- Tier 5: power role exit methods ---

    def _exit_method(player_id: str) -> str:
        if player_id in survivors:
            return "survived"
        for day in metrics.day_resolutions:
            if day.voted_player == player_id:
                return "voted_out"
        return "killed_by_wolves"

    return BaseGameMetrics(
        winner=winner,
        game_length=game_length,
        mislynches=mislynches,
        total_eliminations=total_eliminations,
        wolf_eliminations=wolf_eliminations,
        tie_count=tie_count,
        no_vote_count=no_vote_count,
        healer_save_count=healer_save_count,
        healer_nights_alive=healer_nights_alive,
        healer_exit_method=_exit_method(healer_id),
        investigator_found_wolf_day=investigator_found_wolf_day,
        investigator_wolves_found=investigator_wolves_found,
        investigator_investigations_total=investigator_investigations_total,
        investigator_exit_method=_exit_method(investigator_id),
        wolf_killed_healer_day=wolf_killed_healer_day,
        wolf_killed_investigator_day=wolf_killed_investigator_day,
        power_roles_killed_by_wolves=power_roles_killed_by_wolves,
        wolf_power_role_target_nights=wolf_power_role_target_nights,
        wolf_kill_nights_total=wolf_kill_nights_total,
        mislynch_days_total=mislynch_days_total,
        mislynch_days_steered=mislynch_days_steered,
        wolf_elim_days_total=wolf_elim_days_total,
        wolf_elim_days_blended=wolf_elim_days_blended,
        wolf_elim_days_dissented=wolf_elim_days_dissented,
    )


def _compute_derived_metrics(base: BaseGameMetrics) -> DerivedGameMetrics:
    return DerivedGameMetrics(
        correct_elimination_rate=_safe_div(base.wolf_eliminations, base.total_eliminations),
        healer_save_rate=_safe_div(base.healer_save_count, base.healer_nights_alive),
        investigator_accuracy=_safe_div(base.investigator_wolves_found, base.investigator_investigations_total),
        wolf_steering_rate=_safe_div(base.mislynch_days_steered, base.mislynch_days_total),
        wolf_blending_rate=_safe_div(base.wolf_elim_days_blended, base.wolf_elim_days_total),
        wolf_dissent_rate=_safe_div(base.wolf_elim_days_dissented, base.wolf_elim_days_total),
        wolf_power_role_targeting_rate=_safe_div(base.wolf_power_role_target_nights, base.wolf_kill_nights_total),
    )


def compute_game_metrics(result: dict, metrics: Metrics) -> ComputedGameMetrics:
    base = _compute_base_metrics(result, metrics)
    derived = _compute_derived_metrics(base)

    return ComputedGameMetrics(
        **derived.model_dump(),
        winner=base.winner,
        game_length=base.game_length,
        mislynches=base.mislynches,
        healer_save_count=base.healer_save_count,
        healer_exit_method=base.healer_exit_method,
        investigator_exit_method=base.investigator_exit_method,
        investigator_wolves_found=base.investigator_wolves_found,
        power_roles_killed_by_wolves=base.power_roles_killed_by_wolves,
        tie_count=base.tie_count,
        no_vote_count=base.no_vote_count,
        investigator_found_wolf_day=base.investigator_found_wolf_day,
        wolf_killed_healer_day=base.wolf_killed_healer_day,
        wolf_killed_investigator_day=base.wolf_killed_investigator_day,
    )


# ---------------------------------------------------------------------------
# Langfuse push
# ---------------------------------------------------------------------------


def push_scores_to_langfuse(
    game_metrics: ComputedGameMetrics,
    trace_id: str,
    session_id: str | None = None,
):
    for field_name, value in game_metrics.model_dump().items():
        if value is None:
            continue

        data_type = "CATEGORICAL" if isinstance(value, str) else "NUMERIC"
        langfuse.create_score(
            score_id=_score_id("game_metric", "trace", trace_id, field_name),
            trace_id=trace_id,
            name=field_name,
            value=value,
            data_type=data_type,
        )
        if session_id:
            langfuse.create_score(
                score_id=_score_id(
                    "game_metric",
                    "session",
                    session_id,
                    trace_id,
                    field_name,
                ),
                session_id=session_id,
                name=field_name,
                value=value,
                data_type=data_type,
                metadata={"trace_id": trace_id},
            )
