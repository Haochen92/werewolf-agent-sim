from __future__ import annotations

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
