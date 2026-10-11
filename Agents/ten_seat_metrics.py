"""The per-game metrics of the ten-seat game, read from each night's full record.

The nine-seat metrics in ``compute_metrics`` read per-role night fields (``healer_target``,
``serial_killer_target``, ...) that a ten-seat game never fills, and count the literal ``wolf`` role.
This module computes the same metrics from what a ten-seat night records (every choice, what the
rules made of them, and every actor's result: ``NightResolutionMetric.choices/outcome/records``),
with sides taken from the role registry, plus the proxies for the new roles (plan 2026-10-11 §8.2,
§8.3). Every proxy here is unvalidated on the ten-seat game; none pushes as "validated".

Grading uses what the engine decided (the plan's rule: consequences are graded on engine truth),
except where a result has to reach its actor to count: a find the investigator never learned (it
died that night) cannot convert.
"""

from __future__ import annotations

from typing import Any

from Agents.schemas.metrics import Metrics
from Agents.schemas.roles import LONE_KILLER, ROLE_SPECS, TOWN, WOLVES

EVIL_SIDES = (WOLVES, LONE_KILLER)


def _side(role: str | None) -> str | None:
    spec = ROLE_SPECS.get(role or "")
    return spec.side if spec is not None else None


def has_night_records(metrics: Metrics) -> bool:
    """Whether every night carries its full record (games recorded from 2026-10-11 on)."""
    return bool(metrics.night_resolutions) and all(n.outcome for n in metrics.night_resolutions)


def _safe_div(numerator: float, denominator: float) -> float | None:
    return numerator / denominator if denominator > 0 else None


def ten_seat_metrics(result: dict, metrics: Metrics) -> dict[str, Any]:
    """The ten-seat values of the nine-seat-only metrics, and the new roles' proxies, as field updates
    for ``ComputedGameMetrics``. A role the game did not deal reads None."""
    roles: dict[str, str] = result["roles"]
    holder = {role: player for player, role in roles.items()}
    side = {player: _side(role) for player, role in roles.items()}
    nights = metrics.night_resolutions
    days = metrics.day_resolutions

    died_on = {}  # player -> night it died
    for n in nights:
        for p in n.deaths:
            died_on.setdefault(p, n.day)
    lynched_on = {d.voted_player: d.day for d in days if d.voted_player}

    def records(role: str, action: str | None = None) -> list[tuple[int, dict]]:
        """(night, record) for the role's own records (not a necromancer's borrowed ones)."""
        player = holder.get(role)
        return [(n.day, r) for n in nights for r in n.records
                if r["actor"] == player and (action is None or r["action"] == action)]

    def went_ahead(r: dict) -> bool:
        return r["result"] != "roleblocked"

    def lynched_after(player: str | None, night: int) -> bool:
        """Voted out on a day after the night (a night belongs to the day before it)."""
        return player is not None and lynched_on.get(player, 0) > night

    def nights_alive(player: str | None) -> int | None:
        if player is None:
            return None
        return sum(1 for n in nights if player not in _dead_entering(n.day))

    def _dead_entering(night: int) -> set[str]:
        return ({p for p, d in lynched_on.items() if d <= night}
                | {p for p, d in died_on.items() if d < night})

    out: dict[str, Any] = {}

    # --- Day eliminations, by side ---
    lynched_sides = [_side(d.voted_player_role) for d in days if d.voted_player]
    out["correct_elimination_rate"] = _safe_div(sum(s in EVIL_SIDES for s in lynched_sides), len(lynched_sides))
    out["wolf_elimination_rate"] = _safe_div(sum(s == WOLVES for s in lynched_sides), len(lynched_sides))
    out["lone_killer_lynched"] = int(LONE_KILLER in lynched_sides)

    # --- Healer: saves of any attacker, by the saved player's side ---
    protects = [(d, r) for d, r in records("healer", "protect") if went_ahead(r)]
    pack_victim = {n.day: next((c["target"] for c in n.choices
                                if c["kind"] == "kill" and _side(c["role"]) == WOLVES), None) for n in nights}
    saves = [(d, r) for d, r in protects if r["result"] == "saved"]
    out["healer_save_count"] = len(saves) if "healer" in holder else None
    out["healer_save_rate"] = _safe_div(len(saves), len(protects))
    out["healer_town_save_rate"] = _safe_div(sum(side.get(r["target"]) == TOWN for _, r in saves), len(protects))
    out["healer_friendly_fire_save_rate"] = _safe_div(
        sum(side.get(r["target"]) in EVIL_SIDES for _, r in saves), len(protects))
    out["healer_wolf_block_rate"] = _safe_div(sum(r["target"] == pack_victim.get(d) for d, r in saves), len(protects))

    # --- Investigator: a find is a delivered Suspicious ---
    finds = [(d, r["target"]) for d, r in records("investigator", "investigate")
             if r["result"] == "suspicious" and died_on.get(holder.get("investigator")) != d]
    if "investigator" in holder:
        out["investigator_finds_total"] = len(finds)
        out["investigator_wolves_found"] = sum(side.get(t) == WOLVES for _, t in finds)
        out["investigator_finds_lynched"] = sum(lynched_after(t, d) for d, t in finds)
        out["investigator_find_to_lynch_rate"] = _safe_div(out["investigator_finds_lynched"], len(finds))

    # --- Vigilante: shots that went ahead (a blocked shot keeps its bullet) ---
    if "vigilante" in holder:
        shots = [(d, r) for d, r in records("vigilante", "shoot") if went_ahead(r)]
        loadout = ROLE_SPECS["vigilante"].uses or 0
        out["vigilante_shots_taken"] = len(shots)
        out["vigilante_evil_shots"] = sum(side.get(r["target"]) in EVIL_SIDES for _, r in shots)
        out["vigilante_friendly_fire_shots"] = sum(side.get(r["target"]) == TOWN for _, r in shots)
        out["vigilante_wolf_kills"] = sum(side.get(r["target"]) == WOLVES and r["result"] == "killed"
                                          for _, r in shots)
        immune_hits = [(d, r["target"]) for d, r in shots if r["result"] == "immune"]
        out["vigilante_skconfirms_total"] = len(immune_hits)
        out["vigilante_skconfirms_lynched"] = sum(lynched_after(t, d) for d, t in immune_hits)
        out["vigilante_bullets_unused"] = max(0, loadout - len(shots))
        out["vigilante_correct_shot_rate"] = _safe_div(out["vigilante_evil_shots"], len(shots))
        out["vigilante_wolf_kills_rate"] = _safe_div(out["vigilante_wolf_kills"], loadout)

    # --- Serial killer ---
    if "serial_killer" in holder:
        kills = [r for _, r in records("serial_killer", "kill") if r["result"] == "killed"]
        survived = nights_alive(holder["serial_killer"]) or 0
        out["sk_kills_landed"] = len(kills)
        out["sk_power_roles_killed"] = sum(side.get(r["target"]) == TOWN for r in kills)
        out["sk_wolf_kills"] = sum(side.get(r["target"]) == WOLVES for r in kills)
        out["sk_kill_rate"] = _safe_div(len(kills), survived)

    # --- Town roles killed at night by an evil attacker (pack, lone killer, a borrowed body) ---
    killed_by_evil = 0
    for n in nights:
        for victim in n.deaths:
            attackers = [a["attacker"] for a in n.outcome.get("attacks_on", {}).get(victim, [])]
            if side.get(victim) == TOWN and any(side.get(a) in EVIL_SIDES for a in attackers):
                killed_by_evil += 1
    out["power_roles_killed_by_evil"] = killed_by_evil

    # --- The pack's votes: blending with the day's elimination ---
    aligned = total = 0
    for d in days:
        if d.voted_player is None:
            continue
        for v in d.votes:
            if side.get(v["voter"]) == WOLVES and v["voter"] != d.voted_player:
                total += 1
                aligned += v["votee"] == d.voted_player
    out["wolf_blend_votes_aligned"], out["wolf_blend_votes_total"] = aligned, total
    out["wolf_unconditioned_blending_rate"] = _safe_div(aligned, total)

    # --- Chanteuse: what each block cancelled ---
    if "chanteuse" in holder:
        real = critical = wasted = 0
        blocks = records("chanteuse", "block")
        for night, r in blocks:
            n = next(x for x in nights if x.day == night)
            blocked = next((c for c in n.choices if c["actor"] == r["target"]), None)
            if r["result"] != "blocked" or blocked is None or side.get(r["target"]) != TOWN:
                wasted += 1  # an immune target, nothing to cancel, or a teammate
                continue
            real += 1
            critical += _would_have_hurt_the_pack(blocked, n, side, pack_victim.get(night))
        out["chanteuse_blocks"] = len(blocks)
        out["chanteuse_blocks_real"] = real
        out["chanteuse_blocks_critical"] = critical
        out["chanteuse_blocks_wasted"] = wasted

    # --- Illusionist: conceals that landed, and those that hid a town role's record ---
    if "illusionist" in holder:
        landed = [(d, r) for d, r in records("illusionist", "conceal") if r["result"] == "concealed"]
        hid_record = 0
        for night, _ in landed:
            n = next(x for x in nights if x.day == night)
            for victim in n.outcome.get("concealed", []):
                earlier = any(rec["actor"] == victim for m in nights if m.day < night for rec in m.records)
                hid_record += side.get(victim) == TOWN and earlier
        out["illusionist_conceals"] = len(landed)
        out["illusionist_conceals_hid_record"] = hid_record

    # --- Necromancer: nights survived (its win is last one standing) ---
    if "necromancer" in holder:
        out["necromancer_nights_survived"] = nights_alive(holder["necromancer"])

    # --- Neutrals ---
    if "speculator" in holder:
        pick = next(((d, r) for d, r in records("speculator", "pick")), None)
        out["speculator_pick_night"] = pick[0] if pick else None
        out["speculator_pick_side"] = pick[1]["target"] if pick else "none"
        out["speculator_won"] = int(str(result.get("neutral_result", "")).startswith("won"))
    if "fortune_teller" in holder:
        ft = holder["fortune_teller"]
        out["fortune_teller_points"] = sum(b["points"] for n in nights for b in n.outcome.get("bets", [])
                                           if b["actor"] == ft)

    # --- Information roles and the sigilist ---
    if "sentinel" in holder:
        watches = [r for _, r in records("sentinel", "watch") if went_ahead(r)]
        out["sentinel_watches"] = len(watches)
        out["sentinel_watches_naming_evil"] = sum(any(side.get(p) in EVIL_SIDES for p in r["seen"]) for r in watches)
    if "trailseer" in holder:
        follows = [r for _, r in records("trailseer", "follow") if went_ahead(r)]
        out["trailseer_follows"] = len(follows)
        out["trailseer_follows_naming_evil"] = sum(side.get(r["target"]) in EVIL_SIDES and bool(r["seen"])
                                                   for r in follows)
    if "sigilist" in holder:
        sigils = [r for _, r in records("sigilist", "sigil") if went_ahead(r)]
        out["sigilist_sigils"] = len(sigils)
        out["sigilist_hits"] = sum(r["result"] == "hit" for r in sigils)

    return out


def _would_have_hurt_the_pack(blocked: dict, night, side: dict[str, str | None], victim: str | None) -> bool:
    """Whether a blocked town action would have hurt the pack (fellow wolves only, not the lone
    killer, the wolves' rival): saved its victim, struck its carrier, shot or found a wolf, or shown
    a wolf's visit. Plan 2026-10-11 §8.3; "fellow wolves only" is proposed, not yet ruled."""
    kind, target = blocked["kind"], blocked["target"]
    carrier = next((c["actor"] for c in night.choices if c["kind"] == "kill" and side.get(c["actor"]) == WOLVES), None)
    visits = night.outcome.get("visits", [])
    if kind == "protect":
        return target == victim
    if kind == "sigil":
        return target == carrier
    if kind in ("kill", "investigate"):
        return side.get(target) == WOLVES
    if kind == "watch":
        return any(visited == target and side.get(visitor) == WOLVES for visitor, visited in visits)
    if kind == "follow":
        return side.get(target) == WOLVES and any(visitor == target for visitor, _ in visits)
    return False
