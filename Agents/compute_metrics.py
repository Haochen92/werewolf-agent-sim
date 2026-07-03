import hashlib

from Agents.game_config import GameConfig
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

# Vigilante starting loadout = the SUPPLY denominator for the wolf-kill rate (constant per game).
# vigilante_bullets is NOT persisted in run records (nor in the record's game_config), so the rate
# must denominate by this known constant — NOT shots_taken+bullets_unused, which collapses to
# shots_taken on recompute (bullets_unused unrecoverable → 0) and silently drops every held-bullet
# game, the exact games the supply denominator exists to keep. A non-default loadout would need
# persisting; sourced from GameConfig so it tracks the config default, not a magic number.
_VIGILANTE_LOADOUT = GameConfig.model_fields["vigilante_bullets"].default


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


# ---------------------------------------------------------------------------
# Diagnostic-tier per-game computations (metrics-audit survivors, 2026-07-02).
#
# The definitions mirror the audit runners that VALIDATED them
# (evaluation/src/audits/{accusation_metrics,claim_conversion}.py, per
# evidence/metrics/metrics_audit/proxy_discovery_log.md §3.B/§3.C). They are re-expressed here
# against the live object shapes (DayChannel / *ResolutionMetric) rather than imported, because
# Agents/ (production) must not depend on evaluation/ (the eval harness) — the runners already
# import FROM Agents, so the dependency only runs one way. Both sides compute the same quantity;
# the runners stay the validation source of record.
# ---------------------------------------------------------------------------


def _town_accusation_counts(result: dict) -> tuple[int, int]:
    """(town accusations on a true threat, all town accusations) from the discussion layer.

    Parse day_channel addressed_targets with stance=='accusation' (skip passes + self-accusations),
    keep those whose accuser is town-aligned; the numerator is the subset aimed at a wolf/SK. Mirrors
    accusation_metrics.accusations() exactly (denominator counts every town accusation, even one at an
    unknown target). Feeds the DIAGNOSTIC town_accusation_precision rate.
    """
    roles = result.get("roles") or {}
    total = on_threat = 0
    for m in result.get("day_channel", []) or []:
        if getattr(m, "passed", False):
            continue
        accuser = m.player
        if roles.get(accuser) not in TOWN_ROLES:
            continue
        for a in m.addressed_targets or []:
            if a.stance != "accusation":
                continue
            target = a.target
            if not target or target == accuser:
                continue
            total += 1
            if roles.get(target) in THREAT_ROLES:
                on_threat += 1
    return on_threat, total


def _investigator_find_next_round_convergence(result: dict, metrics: Metrics) -> float | None:
    """Mean over wolf-finds of (town day-(d+1) votes on the found wolf / all town votes that day).

    A find lands on NIGHT d; day d+1 is the first round the town can act on it. Skips finds whose
    next round has no town votes. Mirrors claim_conversion.find_next_round_convergence. Feeds the
    DIAGNOSTIC investigator_find_next_round_convergence proxy (a timing-sensitive refinement of the
    validated investigator_find_to_lynch_rate). Deterministic, no LLM.
    """
    roles = result.get("roles") or {}
    votes_by_day = {d.day: d.votes for d in metrics.day_resolutions}
    convs: list[float] = []
    for n in metrics.night_resolutions:
        if n.investigator_target_role != "wolf" or not n.investigator_target:
            continue
        nxt = votes_by_day.get((n.day or 0) + 1)
        if not nxt:
            continue
        town_votes = [v for v in nxt if roles.get(v["voter"]) in TOWN_ROLES]
        if not town_votes:
            continue
        on_wolf = sum(1 for v in town_votes if v["votee"] == n.investigator_target)
        convs.append(on_wolf / len(town_votes))
    return (sum(convs) / len(convs)) if convs else None


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
    # Threat-generic version: the SK also kills power roles, so wolf-only undercounts the town's
    # night-protection failure (validated -0.40 vs wolf-only -0.21 against villager win). Deduped PER
    # NIGHT by victim — a power role co-targeted by BOTH the wolves and the SK (same victim, both
    # flags set) is one death, counted once, not twice.
    power_roles_killed_by_evil = 0
    for n in metrics.night_resolutions:
        evil_victims = set()
        if n.kill_successful and n.wolf_target_role in POWER_ROLES:
            evil_victims.add(n.wolves_target)
        if n.serial_killer_kill_landed and n.serial_killer_target_role in POWER_ROLES:
            evil_victims.add(n.serial_killer_target)
        power_roles_killed_by_evil += len(evil_victims)

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
    sk_power_roles_killed = sum(
        1 for n in metrics.night_resolutions
        if n.serial_killer_kill_landed and n.serial_killer_target_role in POWER_ROLES
    )
    # Cross-faction targeting: SK landings on WOLVES. The validated deceiver SKILL — survival-de-
    # confounded (partial r=+0.30 net of nights_survived; within long-survivors 85% vs 53% win):
    # the lone SK must address the pack or face a 2v1 at parity. (Timing slice — early vs late — is
    # the richer follow-up; early kills correlate with worse outcomes but that cut is survival-bounded.)
    sk_wolf_kills = sum(
        1 for n in metrics.night_resolutions
        if n.serial_killer_kill_landed and n.serial_killer_target_role == "wolf"
    )
    # SK day-vote camouflage (parallel to wolf unconditioned blending): SK votes aligned with the
    # day's lynch / SK votes on lynch days (excl. the day the SK itself is lynched). SUGGESTIVE only
    # (p=.019, fails a ~12-test Bonferroni; kept for parallel-construction prior plausibility).
    sk_blend_aligned = sk_blend_total = 0
    if sk_id:
        for day in metrics.day_resolutions:
            if day.voted_player is None or day.voted_player == sk_id:
                continue
            for v in day.votes:
                if v["voter"] == sk_id:
                    sk_blend_total += 1
                    if v["votee"] == day.voted_player:
                        sk_blend_aligned += 1

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
    # Wolf REMOVALS only: shooting the SK does NOT remove it (night-immune) — it merely confirms it, a
    # transmission-dependent signal, not a kill. So the de-lucked removal proxy counts landed wolf
    # kills over the bullet supply (validated +0.16 p=.035); the lumped evil_shots dilutes with the
    # dead SK component (sk_shots r=+0.04). The SK-confirm belongs with the reveal/transmission metrics.
    vigilante_wolf_kills = sum(
        1 for n in metrics.night_resolutions
        if n.vigilante_target_role == "wolf" and n.vigilante_kill_landed
    )
    # Loadout = supply (constant); bullets_unused = supply − shots fired (recompute-stable, unlike the
    # old result.get("vigilante_bullets") which isn't persisted). 0 loadout when there's no vigilante.
    vigilante_loadout = _VIGILANTE_LOADOUT if vigilante_id is not None else 0
    vigilante_bullets_unused = max(0, vigilante_loadout - vigilante_shots_taken)

    # --- Conversion: did a private night-confirmation reach a public LYNCH? Deterministic, no LLM,
    # no transcript reading — join the confirmed PLAYER ID (not role: crediting any-wolf-lynched would
    # over-count) to voted_player on a later day. Validated: investigator find->lynch +0.40 vs the
    # dead find-rate -0.03; the rate also gauges the transmission bottleneck (~0.60 baseline = 40% of
    # confirmed wolves never lynched). It does NOT isolate the agent's causal role (the day-summary
    # reveal/led metric does that); a coincidental lynch still counts. ---
    def _lynched_after(player_id: str | None, learn_day: int) -> bool:
        return any(
            d.voted_player == player_id and d.day >= learn_day for d in metrics.day_resolutions
        )

    inv_finds = [
        (n.day, n.investigator_target)
        for n in metrics.night_resolutions
        if n.investigator_target_role == "wolf"
    ]
    investigator_finds_total = len(inv_finds)
    investigator_finds_lynched = sum(1 for day, wolf in inv_finds if _lynched_after(wolf, day))

    vig_sk_confirms = [
        (n.day, n.vigilante_target)
        for n in metrics.night_resolutions
        if n.vigilante_target_role == "serial_killer"
    ]
    vigilante_skconfirms_total = len(vig_sk_confirms)
    vigilante_skconfirms_lynched = sum(1 for day, sk in vig_sk_confirms if _lynched_after(sk, day))

    # Suspicion drawn (concealment OUTCOME, not a clean skill proxy): per LIVING member, votes-at-member
    # / total-votes-on-days-the-member-was-alive, averaged over the faction's members — kills the
    # team-size (wolf is 2, SK is 1) and attrition confounds. CAVEATS (carried in the doc): it is
    # outcome-proximate (esp. the night-immune SK: votes-at-SK is the precursor to its ONLY removal) AND
    # opponent-coupled — it is town_vote_accuracy viewed from the other seat, so never count "town voted
    # well" and "deceiver concealed poorly" as two pieces of evidence; they are one event.
    def _member_suspicion(member: str) -> float | None:
        alive_days = {
            d.day for d in metrics.day_resolutions
            if member in {v["voter"] for v in d.votes} or d.voted_player == member
        }
        num = den = 0
        for d in metrics.day_resolutions:
            if d.day not in alive_days:
                continue
            for v in d.votes:
                den += 1
                num += v["votee"] == member
        return num / den if den else None

    def _faction_suspicion(role: str) -> float | None:
        rates = [_member_suspicion(p) for p, ro in roles.items() if ro == role]
        rates = [x for x in rates if x is not None]
        return sum(rates) / len(rates) if rates else None

    wolf_suspicion_drawn = _faction_suspicion("wolf")
    sk_suspicion_drawn = _faction_suspicion("serial_killer")

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

    # --- Diagnostic-tier survivors (metrics-audit 2026-07-02): discussion-layer + timing proxies ---
    town_accusations_on_threat, town_accusations_total = _town_accusation_counts(result)
    investigator_find_next_round_convergence = _investigator_find_next_round_convergence(
        result, metrics
    )

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
        investigator_finds_total=investigator_finds_total,
        investigator_finds_lynched=investigator_finds_lynched,
        investigator_exit_method=_exit_method(investigator_id),
        wolf_killed_healer_day=wolf_killed_healer_day,
        wolf_killed_investigator_day=wolf_killed_investigator_day,
        power_roles_killed_by_wolves=power_roles_killed_by_wolves,
        power_roles_killed_by_evil=power_roles_killed_by_evil,
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
        sk_power_roles_killed=sk_power_roles_killed,
        sk_wolf_kills=sk_wolf_kills,
        sk_blend_votes_aligned=sk_blend_aligned,
        sk_blend_votes_total=sk_blend_total,
        wolf_suspicion_drawn=wolf_suspicion_drawn,
        sk_suspicion_drawn=sk_suspicion_drawn,
        sk_exit_method=_sk_exit_method(),
        vigilante_shots_taken=vigilante_shots_taken,
        vigilante_evil_shots=vigilante_evil_shots,
        vigilante_wolf_kills=vigilante_wolf_kills,
        vigilante_loadout=vigilante_loadout,
        vigilante_friendly_fire_shots=vigilante_friendly_fire_shots,
        vigilante_bullets_unused=vigilante_bullets_unused,
        vigilante_skconfirms_total=vigilante_skconfirms_total,
        vigilante_skconfirms_lynched=vigilante_skconfirms_lynched,
        vigilante_exit_method=_exit_method(vigilante_id),
        town_accusations_total=town_accusations_total,
        town_accusations_on_threat=town_accusations_on_threat,
        investigator_find_next_round_convergence=investigator_find_next_round_convergence,
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
        sk_kill_rate=_safe_div(base.sk_kills_landed, base.sk_nights_survived),
        sk_unconditioned_blending_rate=_safe_div(base.sk_blend_votes_aligned, base.sk_blend_votes_total),
        wolf_suspicion_drawn=base.wolf_suspicion_drawn,
        sk_suspicion_drawn=base.sk_suspicion_drawn,
        vigilante_correct_shot_rate=_safe_div(base.vigilante_evil_shots, base.vigilante_shots_taken),
        vigilante_wolf_kills_rate=_safe_div(base.vigilante_wolf_kills, base.vigilante_loadout),
        investigator_find_to_lynch_rate=_safe_div(
            base.investigator_finds_lynched, base.investigator_finds_total
        ),
        vigilante_skconfirm_to_lynch_rate=_safe_div(
            base.vigilante_skconfirms_lynched, base.vigilante_skconfirms_total
        ),
        # --- Diagnostic tier (metrics-audit survivors, 2026-07-02) ---
        wolf_power_kill_rate=_safe_div(
            base.power_roles_killed_by_wolves, base.power_role_alive_nights
        ),
        town_accusation_precision=_safe_div(
            base.town_accusations_on_threat, base.town_accusations_total
        ),
        investigator_find_next_round_convergence=base.investigator_find_next_round_convergence,
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
        investigator_finds_total=base.investigator_finds_total,
        investigator_finds_lynched=base.investigator_finds_lynched,
        power_roles_killed_by_wolves=base.power_roles_killed_by_wolves,
        power_roles_killed_by_evil=base.power_roles_killed_by_evil,
        wolf_killed_healer_day=base.wolf_killed_healer_day,
        wolf_killed_investigator_day=base.wolf_killed_investigator_day,
        wolf_blend_votes_aligned=base.wolf_blend_votes_aligned,
        wolf_blend_votes_total=base.wolf_blend_votes_total,
        sk_nights_survived=base.sk_nights_survived,
        sk_exit_method=base.sk_exit_method,
        sk_kills_landed=base.sk_kills_landed,
        sk_power_roles_killed=base.sk_power_roles_killed,
        sk_wolf_kills=base.sk_wolf_kills,
        sk_blend_votes_total=base.sk_blend_votes_total,
        vigilante_shots_taken=base.vigilante_shots_taken,
        vigilante_evil_shots=base.vigilante_evil_shots,
        vigilante_wolf_kills=base.vigilante_wolf_kills,
        vigilante_skconfirms_total=base.vigilante_skconfirms_total,
        vigilante_skconfirms_lynched=base.vigilante_skconfirms_lynched,
        vigilante_friendly_fire_shots=base.vigilante_friendly_fire_shots,
        vigilante_bullets_unused=base.vigilante_bullets_unused,
        vigilante_exit_method=base.vigilante_exit_method,
        # Diagnostic-tier denominators (carried so low-sample games can be filtered).
        power_role_alive_nights=base.power_role_alive_nights,
        town_accusations_total=base.town_accusations_total,
        town_accusations_on_threat=base.town_accusations_on_threat,
    )


# ---------------------------------------------------------------------------
# Langfuse push
# ---------------------------------------------------------------------------

# Minimal trust tiering for the ~50-field push (a full GameScore class is NOT built here).
# The push otherwise treats every field co-equal, so a *validated wrong-sign* proxy sits
# next to the point-biserial-checked basket and gets read as if trustworthy.
#
# DO_NOT_USE = proxies that are wrong-sign or uninterpretable against faction-won (the
# investigator find-rate cluster + wolf_steering_rate). Pushed with a `dnu_` name prefix +
# a `tier="do_not_use"` metadata tag so they can never be silently averaged into a verdict.
DO_NOT_USE_METRICS = frozenset({
    "investigator_found_wolf_day",
    "investigator_threat_find_rate",
    "investigator_wolf_find_rate",
    "investigator_threat_find_lift",
    "wolf_steering_rate",
})

# VALIDATED_BASKET = the proxies checked (point-biserial vs win) and trusted; tagged
# tier="validated" so a downstream reader can filter to just these.
VALIDATED_BASKET_METRICS = frozenset({
    "town_vote_accuracy",
    "correct_elimination_rate",
    "town_mislynch_rate",
    "mislynches",
    "serial_killer_lynched",
    "healer_town_save_rate",
    "investigator_find_to_lynch_rate",
    "wolf_unconditioned_blending_rate",
    "sk_kill_rate",
    "sk_power_roles_killed",
    "power_roles_killed_by_evil",
})

# DIAGNOSTIC = win-validated on the audit set (proxy_discovery_log §3) but adopted as CONTEXT, not
# as basket evidence — each is either environment-conditioned, coupled to a basket metric, or a
# refinement of one. Named explicitly (default-diagnostic already tags everything un-tiered, but
# these are deliberate adoptions the metrics audit graduated, so they get a roster of their own).
# NOT basket promotion: proxy_discovery_log records that as pending a larger wolf-win N. Caveats
# live as attribute docstrings on the DerivedGameMetrics fields (docstrings for humans).
DIAGNOSTIC_METRICS = frozenset({
    "wolf_power_kill_rate",
    "town_accusation_precision",
    "investigator_find_next_round_convergence",
})


def _metric_tier(field_name: str) -> str:
    if field_name in DO_NOT_USE_METRICS:
        return "do_not_use"
    if field_name in VALIDATED_BASKET_METRICS:
        return "validated"
    # DIAGNOSTIC_METRICS members and everything un-tiered both push as "diagnostic"; the named
    # set documents the audit-graduated adoptions (proxy_discovery_log §3).
    return "diagnostic"


def push_scores_to_langfuse(
    game_metrics: ComputedGameMetrics,
    trace_id: str,
    session_id: str | None = None,
):
    for field_name, value in game_metrics.model_dump().items():
        if value is None:
            continue

        data_type = "CATEGORICAL" if isinstance(value, str) else "NUMERIC"
        tier = _metric_tier(field_name)
        # DO_NOT_USE fields are renamed with a `dnu_` prefix so they stand out and can't be
        # confused with a trusted proxy; the tier is also carried in metadata for filtering.
        score_name = f"dnu_{field_name}" if tier == "do_not_use" else field_name
        langfuse.create_score(
            score_id=_score_id("game_metric", "trace", trace_id, field_name),
            trace_id=trace_id,
            name=score_name,
            value=value,
            data_type=data_type,
            metadata={"tier": tier},
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
                name=score_name,
                value=value,
                data_type=data_type,
                metadata={"trace_id": trace_id, "tier": tier},
            )
