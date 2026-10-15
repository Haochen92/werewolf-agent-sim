"""The v6 cell fan-out plan: which (role, phase-group) cells each role contributes, and the
phase wording / representative action_phase each cell extracts under.

One LLM call per (game, role, phase): the discussion, the vote and the night each get their own call.
The day was one call that tagged each observation by phase until 2026-10-11, when the ten-seat pilot
filed nearly every day observation under the vote (a day moment ends in a vote, so the vote became
its outcome), leaving the discussion namespace, which an evil player's discussion turns retrieve
from, almost empty. Villager has no night cell. Shared by the LIVE post-game extractor (extract_postgame_per_cell) and the offline re-miner
(reextract_cells.py) so the two stay in lockstep.
"""

from __future__ import annotations

# (group label, prompt phase wording, the action_phase the call extracts and its schema lookup)
DISCUSSION_GROUP = ("day_discussion", "day discussion (what is said, claimed and argued, before the vote)",
                    "day_discussion")
VOTE_GROUP = ("day_vote", "day vote (whom to vote for, and when)", "day_vote")
NIGHT_GROUP = ("night", "night (the secret night action)", "night_action")
DAY_GROUPS = [DISCUSSION_GROUP, VOTE_GROUP]

ROLE_UNITS: dict[str, list[tuple[str, str, str]]] = {
    "villager": DAY_GROUPS,
    "healer": [*DAY_GROUPS, NIGHT_GROUP],
    "investigator": [*DAY_GROUPS, NIGHT_GROUP],
    "vigilante": [*DAY_GROUPS, NIGHT_GROUP],
    "wolf": [*DAY_GROUPS, NIGHT_GROUP],
    "serial_killer": [*DAY_GROUPS, NIGHT_GROUP],
    # The ten-seat roles (plan 2026-10-11 §9). Town day is extracted for the owner's review but
    # never retrieved in play (plan_gating).
    "sentinel": [*DAY_GROUPS, NIGHT_GROUP],
    "trailseer": [*DAY_GROUPS, NIGHT_GROUP],
    "sigilist": [*DAY_GROUPS, NIGHT_GROUP],
    "chanteuse": [*DAY_GROUPS, NIGHT_GROUP],
    "illusionist": [*DAY_GROUPS, NIGHT_GROUP],
    "necromancer": [*DAY_GROUPS, NIGHT_GROUP],
    "speculator": [*DAY_GROUPS, NIGHT_GROUP],
    "fortune_teller": [*DAY_GROUPS, NIGHT_GROUP],
}
