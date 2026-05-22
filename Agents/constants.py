from typing import Literal

roles = ["villager", "wolf", "investigator", "healer"]

ActionPhase = Literal["day_discussion", "day_vote", "night_action"]
ACTION_PHASES: list[str] = ["day_discussion", "day_vote", "night_action"]

VALID_ACTION_PHASES_BY_ROLE: dict[str, list[str]] = {
    "villager": ["day_discussion", "day_vote"],
    "wolf": ["day_discussion", "day_vote", "night_action"],
    "healer": ["day_discussion", "day_vote", "night_action"],
    "investigator": ["day_discussion", "day_vote", "night_action"],
}