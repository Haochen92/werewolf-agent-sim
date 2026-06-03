from __future__ import annotations

from math import ceil
from typing import Any

from pydantic import BaseModel, Field, model_validator


class GameConfig(BaseModel):
    initial_roles: list[str] = Field(
        default_factory=lambda: [
            "villager",
            "villager",
            "villager",
            "villager",
            "wolf",
            "wolf",
            "healer",
            "investigator",
        ],
        min_length=1,
    )
    player_id_prefix: str = Field(default="player", min_length=1)
    starting_day: int = Field(default=1, ge=1)
    first_voting_day: int = Field(default=2, ge=1)
    max_discussion_rounds_per_day: int = Field(default=4, ge=1)
    # ^ legacy (concurrent round model); still read by the interim check_round + prompt_inputs
    #   until the SCHEDULE-node rewrite (Stage 4) removes round-based control.

    # --- Sequential discussion scheduler (Phase 0) -------------------------------
    # All deterministic, pure-function knobs; tune later. See evidence/agent_speaking/.
    discussion_utterance_multiplier: float = Field(default=3.0, gt=0)
    # global hard cap on real utterances/day = ceil(multiplier * surviving players),
    # floored by min_discussion_utterances. Backstop only — pass_turn does the real
    # termination, so this is biased generous to avoid truncating an active day.
    min_discussion_utterances: int = Field(default=6, ge=1)
    per_pair_reengagement_cap: int = Field(default=2, ge=1)
    # K: a directed (speaker -> target, stance) edge can create an obligation at most
    # K times/day (escalation cap). Distinct from the open-edge freshness dedup.
    proactive_budget: int = Field(default=3, ge=1)
    # terminate once this many DISTINCT proactive picks pass (decline the floor) in a
    # row on a quiet cycle; any real utterance resets the streak.
    opener_floor: int = Field(default=1, ge=0)

    @model_validator(mode="after")
    def validate_day_order(self) -> "GameConfig":
        if self.first_voting_day < self.starting_day:
            raise ValueError("first_voting_day cannot be before starting_day")
        if "wolf" not in self.initial_roles:
            raise ValueError("initial_roles must include at least one wolf")
        if all(role == "wolf" for role in self.initial_roles):
            raise ValueError("initial_roles must include at least one non-wolf player")
        if "healer" not in self.initial_roles:
            raise ValueError("initial_roles must include a healer")
        if "investigator" not in self.initial_roles:
            raise ValueError("initial_roles must include an investigator")
        return self

    def utterance_cap(self, num_survivors: int) -> int:
        """Hard backstop on real utterances in a day's discussion."""
        return max(
            self.min_discussion_utterances,
            ceil(self.discussion_utterance_multiplier * num_survivors),
        )

    def discussion_recursion_limit(self, num_survivors: int) -> int:
        """LangGraph recursion_limit for the SCHEDULE self-loop.

        ~2 super-steps per utterance (SCHEDULE node + role node) plus headroom for
        the opener, day-summary, and voting tail. Derived from the cap so the graceful
        cap-termination always fires before an ungraceful GraphRecursionError.
        """
        return 2 * self.utterance_cap(num_survivors) + 10


DEFAULT_GAME_CONFIG = GameConfig()


def normalize_game_config(config: GameConfig | dict[str, Any] | None) -> GameConfig:
    if config is None:
        return DEFAULT_GAME_CONFIG
    if isinstance(config, GameConfig):
        return config
    return GameConfig.model_validate(config)


def game_config_dict(config: GameConfig | dict[str, Any] | None) -> dict[str, Any]:
    return normalize_game_config(config).model_dump()


def game_config_from_runnable(config: dict[str, Any] | None) -> GameConfig:
    configurable = config.get("configurable", {}) if config else {}
    return normalize_game_config(configurable.get("game_config"))
