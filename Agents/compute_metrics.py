import hashlib

from Agents.tracing import Metrics
from Agents.tracing import langfuse
from pydantic import BaseModel


def _score_id(*parts: str) -> str:
    return hashlib.sha256(":".join(parts).encode("utf-8")).hexdigest()[:16]


class ComputedGameMetrics(BaseModel):
    # Always present
    winner: str
    game_length: int
    mislynches: int
    healer_save_count: int
    healer_exit_method: str
    investigator_exit_method: str

    # Nullable
    correct_elimination_rate: float | None = None
    investigator_found_wolf_day: int | None = None
    wolf_killed_healer_day: int | None = None
    wolf_killed_investigator_day: int | None = None
    wolf_steering_rate: float | None = None
    wolf_blending_rate: float | None = None
    wolf_dissent_rate: float | None = None


def compute_game_metrics(result: dict, metrics: Metrics) -> ComputedGameMetrics:
    roles = result["roles"]
    survivors = result["surviving_wolves"] + result["surviving_villagers"]

    healer_id = next(p for p, r in roles.items() if r == "healer")
    investigator_id = next(p for p, r in roles.items() if r == "investigator")

    # --- Tier 1: straight from final state ---
    winner = result["winner"]
    game_length = result["current_day"]

    # --- Tier 2: single pass over accumulators ---

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

    correct_elimination_rate = (
        wolf_eliminations / total_eliminations
        if total_eliminations > 0
        else None
    )

    healer_save_count = sum(
        1 for n in metrics.night_resolutions if n.healer_saved
    )

    investigator_found_wolf_day = next(
        (n.day for n in metrics.night_resolutions
         if n.investigator_target_role == "wolf"),
        None,
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

    # --- Tier 3: wolf voting behavior ---

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
            # Mislynch day — did wolves steer?
            mislynch_days_total += 1
            if majority_of_wolves_aligned:
                mislynch_days_steered += 1
        else:
            # Wolf eliminated — did surviving wolves blend or dissent?
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

    wolf_steering_rate = (
        mislynch_days_steered / mislynch_days_total
        if mislynch_days_total > 0
        else None
    )

    wolf_blending_rate = (
        wolf_elim_days_blended / wolf_elim_days_total
        if wolf_elim_days_total > 0
        else None
    )

    wolf_dissent_rate = (
        wolf_elim_days_dissented / wolf_elim_days_total
        if wolf_elim_days_total > 0
        else None
    )

    # --- Power role exit methods ---

    def _exit_method(player_id: str) -> str:
        if player_id in survivors:
            return "survived"
        for day in metrics.day_resolutions:
            if day.voted_player == player_id:
                return "voted_out"
        return "killed_by_wolves"

    return ComputedGameMetrics(
        winner=winner,
        game_length=game_length,
        mislynches=mislynches,
        correct_elimination_rate=correct_elimination_rate,
        healer_save_count=healer_save_count,
        investigator_found_wolf_day=investigator_found_wolf_day,
        wolf_killed_healer_day=wolf_killed_healer_day,
        wolf_killed_investigator_day=wolf_killed_investigator_day,
        wolf_steering_rate=wolf_steering_rate,
        wolf_blending_rate=wolf_blending_rate,
        wolf_dissent_rate=wolf_dissent_rate,
        healer_exit_method=_exit_method(healer_id),
        investigator_exit_method=_exit_method(investigator_id),
    )


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
