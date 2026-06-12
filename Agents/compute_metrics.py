import hashlib

from Agents.schemas.metrics import (
    BaseGameMetrics,
    ComputedGameMetrics,
    DerivedGameMetrics,
    Metrics,
)
from Agents.tracing import langfuse


# Town-aligned roles (win when both wolves and the SK are gone) and the roles that
# are ENEMIES of the town (the two kill-worthy factions: wolves + the night-immune SK).
TOWN_ROLES = {"villager", "healer", "investigator", "vigilante"}
THREAT_ROLES = {"wolf", "serial_killer"}
# Town power roles the wolves most want to remove (used for targeting/exposure metrics).
POWER_ROLES = ("healer", "investigator", "vigilante")


def _score_id(*parts: str) -> str:
    return hashlib.sha256(":".join(parts).encode("utf-8")).hexdigest()[:16]


def _safe_div(numerator: float, denominator: float) -> float | None:
    return numerator / denominator if denominator > 0 else None


def _mean(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None


# ---------------------------------------------------------------------------
# Computation pipeline
# ---------------------------------------------------------------------------


def _dead_before_each_night(metrics: Metrics) -> dict[int, set[str]]:
    """For each night, the set of players already dead ENTERING that night.

    Chronological: within a day the lynch happens first, then the night's kills. So
    entering night d = (lynches on days 1..d) + (night kills on nights 1..d-1).
    Lets downstream metrics ask "was this power role / the SK still alive that night?"
    """
    day_res_by_day = {d.day: d for d in metrics.day_resolutions}
    night_res_by_day = {n.day: n for n in metrics.night_resolutions}
    all_days = sorted(set(day_res_by_day) | set(night_res_by_day))

    dead: set[str] = set()
    entering: dict[int, set[str]] = {}
    for day in all_days:
        dr = day_res_by_day.get(day)
        if dr and dr.voted_player:
            dead.add(dr.voted_player)
        entering[day] = set(dead)
        nr = night_res_by_day.get(day)
        if nr:
            dead |= set(nr.deaths)
    return entering


def _compute_base_metrics(result: dict, metrics: Metrics) -> BaseGameMetrics:
    roles = result["roles"]
    # surviving_villagers is the non-wolf bucket (town + the solo SK + vigilante).
    survivors = result["surviving_wolves"] + result["surviving_villagers"]

    def _role_id(role: str) -> str | None:
        return next((p for p, r in roles.items() if r == role), None)

    healer_id = _role_id("healer")
    investigator_id = _role_id("investigator")
    sk_id = _role_id("serial_killer")
    vigilante_id = _role_id("vigilante")
    power_ids = {pid for pid in (healer_id, investigator_id, vigilante_id) if pid}

    entering = _dead_before_each_night(metrics)

    winner = result.get("winner") or "draw"
    game_length = result["current_day"]

    # --- Day eliminations (faction-aware: wolf+SK are both town enemies) ---
    total_eliminations = wolf_eliminations = sk_eliminations = town_mislynches = 0
    for day in metrics.day_resolutions:
        if day.voted_player is None:
            continue
        total_eliminations += 1
        role = day.voted_player_role
        if role == "wolf":
            wolf_eliminations += 1
        elif role == "serial_killer":
            sk_eliminations += 1
        elif role in TOWN_ROLES:
            town_mislynches += 1
    anti_town_eliminations = wolf_eliminations + sk_eliminations
    serial_killer_lynched = 1 if sk_eliminations > 0 else 0

    tie_count = sum(1 for d in metrics.day_resolutions if d.tied_players)
    no_vote_count = sum(1 for d in metrics.day_resolutions if d.no_vote)

    # --- Town voting, per individual vote ---
    town_votes_total = town_votes_on_threat = 0
    for day in metrics.day_resolutions:
        for v in day.votes:
            votee = v["votee"]
            if roles.get(v["voter"]) not in TOWN_ROLES:
                continue
            if votee == "abstain" or votee not in roles:
                continue
            town_votes_total += 1
            if roles[votee] in THREAT_ROLES:
                town_votes_on_threat += 1

    # --- Healer: intercepts of ANY attacker, classified by saved player's faction ---
    healer_action_nights = healer_saves_total = 0
    healer_town_saves = healer_ff_saves = healer_wolf_blocks = 0
    for n in metrics.night_resolutions:
        ht = n.healer_target
        if ht is None:
            continue
        healer_action_nights += 1
        attacked = ht in (n.wolves_target, n.serial_killer_target, n.vigilante_target)
        if not (attacked and ht not in n.deaths):
            continue
        healer_saves_total += 1
        saved_role = roles.get(ht)
        if saved_role in TOWN_ROLES:
            healer_town_saves += 1
        elif saved_role == "wolf":
            healer_ff_saves += 1
        if ht == n.wolves_target:
            healer_wolf_blocks += 1

    # --- Investigator: threat = wolf or SK; lift baseline = random-hit chance/night ---
    investigator_investigations_total = investigator_wolf_finds = investigator_threat_finds = 0
    chance_rates: list[float] = []
    for n in metrics.night_resolutions:
        if n.investigator_target is None:
            continue
        investigator_investigations_total += 1
        if n.investigator_target_role == "wolf":
            investigator_wolf_finds += 1
        if n.investigator_target_role in THREAT_ROLES:
            investigator_threat_finds += 1
        alive = n.wolves_before + n.town_before + n.sk_before
        investigable = max(1, alive - 1)  # the investigator cannot investigate itself
        chance_rates.append((n.wolves_before + n.sk_before) / investigable)
    investigator_found_wolf_day = next(
        (n.day for n in metrics.night_resolutions if n.investigator_target_role == "wolf"),
        None,
    )
    investigator_mean_chance = _mean(chance_rates)

    # --- Wolves: power-role targeting (opportunity = nights >=1 power role alive) ---
    wolf_power_target_nights = power_role_alive_nights = 0
    for n in metrics.night_resolutions:
        dead = entering.get(n.day, set())
        if any(pid not in dead for pid in power_ids):
            power_role_alive_nights += 1
        if n.wolves_target in power_ids:
            wolf_power_target_nights += 1

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
        if n.kill_successful and n.wolf_target_role in POWER_ROLES
    )

    # --- Wolf voting behavior (steering measured on TOWN mislynch days only) ---
    mislynch_days_total = mislynch_days_steered = 0
    wolf_elim_days_total = wolf_elim_days_blended = wolf_elim_days_dissented = 0
    wolf_blend_votes_aligned = wolf_blend_votes_total = 0
    for day in metrics.day_resolutions:
        if day.voted_player is None:
            continue
        wolf_votes = [v for v in day.votes if roles.get(v["voter"]) == "wolf"]
        if not wolf_votes:
            continue
        aligned = sum(1 for v in wolf_votes if v["votee"] == day.voted_player)
        majority_wolves_aligned = aligned > len(wolf_votes) / 2

        # Unconditioned blending (vote-level, ALL lynch days — not just wolf-elim days):
        # does each living wolf's vote align with the day's eventual lynch? Excludes the wolf
        # being lynched (he can't blend with his own removal). The conditioned wolf_blending_rate
        # below only samples wolf-elim days (disaster states) and is structurally blind to a wolf
        # who blends and is never caught; this is the validated day-camouflage proxy.
        for v in wolf_votes:
            if v["voter"] == day.voted_player:
                continue
            wolf_blend_votes_total += 1
            if v["votee"] == day.voted_player:
                wolf_blend_votes_aligned += 1

        if day.voted_player_role in TOWN_ROLES:
            mislynch_days_total += 1
            if majority_wolves_aligned:
                mislynch_days_steered += 1
        elif day.voted_player_role == "wolf":
            surviving_wolf_votes = [
                v for v in day.votes
                if roles.get(v["voter"]) == "wolf" and v["voter"] != day.voted_player
            ]
            if not surviving_wolf_votes:
                continue
            blended = sum(
                1 for v in surviving_wolf_votes if v["votee"] == day.voted_player
            )
            wolf_elim_days_total += 1
            if blended > len(surviving_wolf_votes) / 2:
                wolf_elim_days_blended += 1
            else:
                wolf_elim_days_dissented += 1
        # SK-lynch days are neither steering nor blending — excluded from both.

    # --- Serial killer: survival is the dense proxy (SK wins by outlasting) ---
    sk_nights_survived = (
        sum(1 for n in metrics.night_resolutions if sk_id not in entering.get(n.day, set()))
        if sk_id else 0
    )
    sk_kills_landed = sum(1 for n in metrics.night_resolutions if n.serial_killer_kill_landed)

    # --- Vigilante: shot quality (evil = good, town = friendly fire); holds not penalized ---
    vigilante_shots_taken = sum(
        1 for n in metrics.night_resolutions if n.vigilante_target is not None
    )
    vigilante_evil_shots = sum(
        1 for n in metrics.night_resolutions if n.vigilante_target_role in THREAT_ROLES
    )
    vigilante_friendly_fire_shots = sum(
        1 for n in metrics.night_resolutions if n.vigilante_target_role in TOWN_ROLES
    )
    vigilante_bullets_unused = int(result.get("vigilante_bullets") or 0)

    # --- Exit methods (generic: per-killer night attribution is a deferred downstream pass) ---
    def _exit_method(player_id: str | None) -> str:
        if player_id is None:
            return "absent"
        if player_id in survivors:
            return "survived"
        if any(d.voted_player == player_id for d in metrics.day_resolutions):
            return "voted_out"
        return "killed_at_night"

    def _sk_exit_method() -> str:
        if sk_id is None:
            return "absent"
        if sk_id in survivors:
            return "survived"
        if any(d.voted_player == sk_id for d in metrics.day_resolutions):
            return "lynched"  # the SK can only be removed by a day vote
        return "draw"

    return BaseGameMetrics(
        winner=winner,
        game_length=game_length,
        total_eliminations=total_eliminations,
        wolf_eliminations=wolf_eliminations,
        sk_eliminations=sk_eliminations,
        anti_town_eliminations=anti_town_eliminations,
        town_mislynches=town_mislynches,
        serial_killer_lynched=serial_killer_lynched,
        tie_count=tie_count,
        no_vote_count=no_vote_count,
        town_votes_total=town_votes_total,
        town_votes_on_threat=town_votes_on_threat,
        healer_action_nights=healer_action_nights,
        healer_saves_total=healer_saves_total,
        healer_town_saves=healer_town_saves,
        healer_ff_saves=healer_ff_saves,
        healer_wolf_blocks=healer_wolf_blocks,
        healer_exit_method=_exit_method(healer_id),
        investigator_investigations_total=investigator_investigations_total,
        investigator_wolf_finds=investigator_wolf_finds,
        investigator_threat_finds=investigator_threat_finds,
        investigator_found_wolf_day=investigator_found_wolf_day,
        investigator_mean_chance=investigator_mean_chance,
        investigator_exit_method=_exit_method(investigator_id),
        wolf_killed_healer_day=wolf_killed_healer_day,
        wolf_killed_investigator_day=wolf_killed_investigator_day,
        power_roles_killed_by_wolves=power_roles_killed_by_wolves,
        wolf_power_target_nights=wolf_power_target_nights,
        power_role_alive_nights=power_role_alive_nights,
        mislynch_days_total=mislynch_days_total,
        mislynch_days_steered=mislynch_days_steered,
        wolf_elim_days_total=wolf_elim_days_total,
        wolf_elim_days_blended=wolf_elim_days_blended,
        wolf_elim_days_dissented=wolf_elim_days_dissented,
        wolf_blend_votes_aligned=wolf_blend_votes_aligned,
        wolf_blend_votes_total=wolf_blend_votes_total,
        sk_nights_survived=sk_nights_survived,
        sk_kills_landed=sk_kills_landed,
        sk_exit_method=_sk_exit_method(),
        vigilante_shots_taken=vigilante_shots_taken,
        vigilante_evil_shots=vigilante_evil_shots,
        vigilante_friendly_fire_shots=vigilante_friendly_fire_shots,
        vigilante_bullets_unused=vigilante_bullets_unused,
        vigilante_exit_method=_exit_method(vigilante_id),
    )


def _compute_derived_metrics(base: BaseGameMetrics) -> DerivedGameMetrics:
    threat_find_rate = _safe_div(base.investigator_threat_finds, base.investigator_investigations_total)
    lift = (
        threat_find_rate / base.investigator_mean_chance
        if threat_find_rate is not None and base.investigator_mean_chance
        else None
    )
    return DerivedGameMetrics(
        correct_elimination_rate=_safe_div(base.anti_town_eliminations, base.total_eliminations),
        wolf_elimination_rate=_safe_div(base.wolf_eliminations, base.total_eliminations),
        town_mislynch_rate=_safe_div(base.town_mislynches, base.total_eliminations),
        town_vote_accuracy=_safe_div(base.town_votes_on_threat, base.town_votes_total),
        healer_save_rate=_safe_div(base.healer_saves_total, base.healer_action_nights),
        healer_town_save_rate=_safe_div(base.healer_town_saves, base.healer_action_nights),
        healer_friendly_fire_save_rate=_safe_div(base.healer_ff_saves, base.healer_action_nights),
        healer_wolf_block_rate=_safe_div(base.healer_wolf_blocks, base.healer_action_nights),
        investigator_threat_find_rate=threat_find_rate,
        investigator_threat_find_lift=lift,
        investigator_wolf_find_rate=_safe_div(base.investigator_wolf_finds, base.investigator_investigations_total),
        wolf_steering_rate=_safe_div(base.mislynch_days_steered, base.mislynch_days_total),
        wolf_blending_rate=_safe_div(base.wolf_elim_days_blended, base.wolf_elim_days_total),
        wolf_unconditioned_blending_rate=_safe_div(base.wolf_blend_votes_aligned, base.wolf_blend_votes_total),
        wolf_dissent_rate=_safe_div(base.wolf_elim_days_dissented, base.wolf_elim_days_total),
        wolf_power_role_targeting_rate=_safe_div(base.wolf_power_target_nights, base.power_role_alive_nights),
        vigilante_correct_shot_rate=_safe_div(base.vigilante_evil_shots, base.vigilante_shots_taken),
    )


def compute_game_metrics(result: dict, metrics: Metrics) -> ComputedGameMetrics:
    base = _compute_base_metrics(result, metrics)
    derived = _compute_derived_metrics(base)

    return ComputedGameMetrics(
        **derived.model_dump(),
        winner=base.winner,
        game_length=base.game_length,
        mislynches=base.town_mislynches,
        serial_killer_lynched=base.serial_killer_lynched,
        tie_count=base.tie_count,
        no_vote_count=base.no_vote_count,
        healer_save_count=base.healer_saves_total,
        healer_exit_method=base.healer_exit_method,
        investigator_exit_method=base.investigator_exit_method,
        investigator_wolves_found=base.investigator_wolf_finds,
        investigator_found_wolf_day=base.investigator_found_wolf_day,
        power_roles_killed_by_wolves=base.power_roles_killed_by_wolves,
        wolf_killed_healer_day=base.wolf_killed_healer_day,
        wolf_killed_investigator_day=base.wolf_killed_investigator_day,
        wolf_blend_votes_aligned=base.wolf_blend_votes_aligned,
        wolf_blend_votes_total=base.wolf_blend_votes_total,
        sk_nights_survived=base.sk_nights_survived,
        sk_exit_method=base.sk_exit_method,
        sk_kills_landed=base.sk_kills_landed,
        vigilante_shots_taken=base.vigilante_shots_taken,
        vigilante_evil_shots=base.vigilante_evil_shots,
        vigilante_friendly_fire_shots=base.vigilante_friendly_fire_shots,
        vigilante_bullets_unused=base.vigilante_bullets_unused,
        vigilante_exit_method=base.vigilante_exit_method,
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
