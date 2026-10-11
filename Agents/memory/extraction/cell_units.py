"""The v6 cell fan-out plan: which (role, phase-group) cells each role contributes, and the
phase wording / representative action_phase each cell extracts under.

One LLM call per (game, role, phase-group): the day call covers day_discussion+day_vote (the merged
day cell tags each observation by phase), the night call covers night_action. Villager has no night
cell. Shared by the LIVE post-game extractor (extract_postgame_per_cell) and the offline re-miner
(reextract_cells.py) so the two stay in lockstep.
"""

from __future__ import annotations

# (group label, prompt phase wording, representative action_phase for the schema lookup)
DAY_GROUP = ("day", "day (public discussion and the elimination vote)", "day_vote")
NIGHT_GROUP = ("night", "night (the secret night action)", "night_action")

ROLE_UNITS: dict[str, list[tuple[str, str, str]]] = {
    "villager": [DAY_GROUP],
    "healer": [DAY_GROUP, NIGHT_GROUP],
    "investigator": [DAY_GROUP, NIGHT_GROUP],
    "vigilante": [DAY_GROUP, NIGHT_GROUP],
    "wolf": [DAY_GROUP, NIGHT_GROUP],
    "serial_killer": [DAY_GROUP, NIGHT_GROUP],
    # The ten-seat roles: every one has a day and a night cell (plan 2026-10-11 §9). Town day is
    # extracted for the owner's review but never retrieved in play (plan_gating).
    "sentinel": [DAY_GROUP, NIGHT_GROUP],
    "trailseer": [DAY_GROUP, NIGHT_GROUP],
    "sigilist": [DAY_GROUP, NIGHT_GROUP],
    "chanteuse": [DAY_GROUP, NIGHT_GROUP],
    "illusionist": [DAY_GROUP, NIGHT_GROUP],
    "necromancer": [DAY_GROUP, NIGHT_GROUP],
    "speculator": [DAY_GROUP, NIGHT_GROUP],
    "fortune_teller": [DAY_GROUP, NIGHT_GROUP],
}
