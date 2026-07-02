"""v7 recall-arm — deterministic PIVOTAL-TURN flagger over finished-game records.

The recall arm tests whether feeding the extractor the do-or-die turns as a SUGGESTIVE anchor lifts a
cheap model's capture of pivotal lessons up to pro's. This module produces those flags from a game's
structured record alone (roles + day/night resolutions) — no eval cases, no LLM. A turn is pivotal if it
sits in the decisive window: near wolf-parity, the endgame, or the round a power role was removed.

Flags are an ANCHOR (attention), never a quota or whitelist (per plan §3 D-anchor). Faction model: 9p,
wolves win at parity (wolves >= non-wolves), SK is a third faction, town = villager/healer/investigator/
vigilante. Power roles = investigator/healer/vigilante.
"""

from __future__ import annotations

POWER = {"investigator", "healer", "vigilante"}
TOWN = {"villager", "investigator", "healer", "vigilante"}


def _faction(role: str) -> str:
    if role == "wolf":
        return "wolves"
    if role == "serial_killer":
        return "serial_killer"
    return "town"


def pivotal_turns(record: dict) -> list[dict]:
    """Return the pivotal (phase, day, reason) turns for one finished game.

    Walks the alive timeline (Day-D vote then Night-D deaths) and flags a turn when, at that decision
    point, the board is in the decisive window. Deterministic; reason strings are for the anchor text.
    """
    roles = record.get("roles") or {}
    alive = set(roles)
    lynch = {d.get("day"): d.get("voted_player") for d in record.get("day_resolutions", [])}
    deaths = {n.get("day"): list(n.get("deaths") or []) for n in record.get("night_resolutions", [])}
    max_day = max([0, *lynch, *deaths])

    def counts():
        f = {"wolves": 0, "serial_killer": 0, "town": 0}
        for p in alive:
            f[_faction(roles.get(p, "villager"))] += 1
        return f

    out: list[dict] = []

    def consider(phase: str, day: int):
        c = counts()
        total = sum(c.values())
        non_wolf = c["serial_killer"] + c["town"]
        reasons = []
        if c["wolves"] + 1 >= non_wolf and c["wolves"] > 0:
            reasons.append("wolves at/near parity")
        if total <= 4:
            reasons.append("endgame (<=4 alive)")
        if reasons:
            out.append({"phase": phase, "day": day, "alive": total,
                        "reason": "; ".join(reasons)})

    for day in range(1, max_day + 1):
        # Day-D vote happens against the post-Night-(D-1) board
        consider("day_vote", day)
        consider("day_discussion", day)
        votee = lynch.get(day)
        if votee in alive:
            alive.discard(votee)
        # Night-D: flag if a power role is alive to be taken, then apply deaths
        powers_alive = [p for p in alive if roles.get(p) in POWER]
        consider("night_action", day)
        died = deaths.get(day, [])
        if any(roles.get(p) in POWER for p in died):
            lost = [roles.get(p) for p in died if roles.get(p) in POWER]
            out.append({"phase": "night_action", "day": day, "alive": len(alive),
                        "reason": f"power role removed at night: {','.join(lost)}"})
        for p in died:
            alive.discard(p)

    # dedup (phase, day), merge reasons
    merged: dict[tuple, dict] = {}
    for t in out:
        k = (t["phase"], t["day"])
        if k in merged:
            merged[k]["reason"] = "; ".join(sorted(set(
                merged[k]["reason"].split("; ") + t["reason"].split("; "))))
        else:
            merged[k] = dict(t)
    return sorted(merged.values(), key=lambda t: (t["day"], t["phase"]))


# the action_phases a fan-out unit covers (the "day" unit emits both day phases)
UNIT_PHASES = {"day": ("day_vote", "day_discussion"), "night": ("night_action",)}


def anchor_text(turns: list[dict], phases) -> str:
    """Suggestive-anchor block for the action_phases a cell covers. Empty if no pivotal turn for them.

    `phases` = a phase string or a collection of them (use UNIT_PHASES[unit_key]). RECOMMENDATION, not a
    command: raise attention on these turns, still extract only what is genuinely there and surface
    anything else (plan §3 D-anchor: soft prior, not a whitelist, not a quota)."""
    if isinstance(phases, str):
        phases = (phases,)
    phases = set(phases)
    rel = [t for t in turns if t["phase"] in phases]
    if not rel:
        return ""
    bullets = "\n".join(
        f"  - Day {t['day']} {t['phase']} ({t['reason']})" for t in rel)
    return (
        "\n\nPIVOTAL-TURN ANCHOR (suggestive, NOT a quota): the game's math marks these turns as "
        f"do-or-die moments:\n{bullets}\n"
        "Give them particular attention and make sure any genuine lesson there is captured — but only "
        "if a real lesson exists; do NOT manufacture one to fill a turn, and still surface any other "
        "lessons you find, flagged or not."
    )
