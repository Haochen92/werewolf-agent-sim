"""Domain layer: the werewolf game rules + scheduler knobs, as a validated settings model.

`GameConfig` describes GAME BEHAVIOR only — casting, voting rules, and the deterministic
sequential-discussion scheduler parameters. It carries no LangGraph/runtime concepts: the one
knob that translated these rules into a LangGraph super-step budget (`discussion_recursion_limit`)
lives in `Agents.config.langgraph`, since that is framework adaptation, not a game rule.
"""
from __future__ import annotations

from math import ceil
from typing import Any

from pydantic import BaseModel, Field, model_validator

from Agents.schemas.roles import LONE_KILLER_ROLES, NEUTRAL_ROLES, SEATS


class GameConfig(BaseModel):
    # --- The deal (Phase 3) -------------------------------------------------------
    # Ten seats from a pool of twelve (Agents/schemas/roles.py): eight fixed, and the lone killer's
    # and the neutral seat each drawn at random per game unless chosen here.
    lone_killer: str | None = Field(default=None)
    # "serial_killer" | "necromancer"; None = drawn by the game's seed.
    neutral: str | None = Field(default=None)
    # "speculator" | "fortune_teller"; None = drawn by the game's seed.
    player_id_prefix: str = Field(default="player", min_length=1)
    starting_day: int = Field(default=1, ge=1)
    first_voting_day: int = Field(default=2, ge=1)

    # --- Role rules with a number in them ------------------------------------------
    vigilante_bullets: int = Field(default=2, ge=0)
    # Shots the vigilante may take over the whole game; a shot is spent on the attempt.
    sigils: int = Field(default=2, ge=0)
    # The sigilist's sigils; one is spent when placed, hit or miss.
    conceals: int = Field(default=2, ge=0)
    # The illusionist's conceals; one is spent only when a body is concealed.
    self_bets: int = Field(default=2, ge=0)
    # The fortune teller's self-bets, each a night it cannot be killed.
    fortune_points_to_win: int = Field(default=2, ge=1)
    # The score the fortune teller wins at.

    # --- Relaxed / optional voting (Phase A #2) ----------------------------------
    abstain_enabled: bool = Field(default=True)
    # When true, "abstain" is a valid day-vote target; an abstain plurality (or a tie)
    # yields no lynch instead of forcing one.
    no_lynch_force_after: int = Field(default=2, ge=1)
    # K: after this many consecutive no-lynch days, the next day drops "abstain" from
    # valid targets (a forced day) so the daytime cannot go permanently toothless.
    max_days: int = Field(default=12, ge=1)
    # Pure cost backstop — night kills end games far sooner. At the cap the winner is
    # decided by surviving-faction size (tie -> draw).

    # --- Sequential discussion scheduler (Phase 0) -------------------------------
    # All deterministic, pure-function knobs; tune later. See evidence/sequential_discussion/.
    discussion_utterance_multiplier: float = Field(default=3.0, gt=0)
    # global hard cap on real utterances/day = ceil(multiplier * surviving players),
    # floored by min_discussion_utterances. Backstop only — pass_turn does the real
    # termination, so this is biased generous to avoid truncating an active day.
    min_discussion_utterances: int = Field(default=6, ge=1)
    per_pair_reengagement_cap: int = Field(default=2, ge=1)
    # K: a directed (speaker -> target, stance) edge can create an obligation at most
    # K times/day (escalation cap). Distinct from the open-edge freshness dedup.
    reengagement_cooldown_multiplier: float = Field(default=1.0, gt=0)
    # M = ceil(multiplier * surviving players). Once a directed pair has gone M
    # utterances untouched, its K cycle-count resets to 0 so a cooled feud can reopen
    # after the room has moved on. Throttles CONSECUTIVE ping-pong (K caps a burst)
    # without permanently killing a topic for the day; default ~one full table.
    max_proactive_sweeps: int = Field(default=2, ge=0)
    # Phase 2 (2026-10-07): when nobody owes an answer, the scheduler sweeps the floor round the
    # survivors who have not spoken since the day began, one at a time in seat order, each line
    # answered before the next player is asked. A second sweep goes round those silent since the
    # first began, only if the first produced a new line; up to this many sweeps a day. 0 = the
    # opening and its chains only.

    @model_validator(mode="after")
    def validate_day_order(self) -> "GameConfig":
        if self.first_voting_day < self.starting_day:
            raise ValueError("first_voting_day cannot be before starting_day")
        if self.lone_killer is not None and self.lone_killer not in LONE_KILLER_ROLES:
            raise ValueError(f"lone_killer must be one of {LONE_KILLER_ROLES}")
        if self.neutral is not None and self.neutral not in NEUTRAL_ROLES:
            raise ValueError(f"neutral must be one of {NEUTRAL_ROLES}")
        return self

    @property
    def seats(self) -> int:
        """How many players a game seats."""
        return SEATS

    def starting_uses(self) -> dict[str, int]:
        """What each limited ability starts the game with, by role."""
        return {
            "vigilante": self.vigilante_bullets,
            "sigilist": self.sigils,
            "illusionist": self.conceals,
            "fortune_teller": self.self_bets,
            "speculator": 1,
        }

    def utterance_cap(self, num_survivors: int) -> int:
        """Hard backstop on real utterances in a day's discussion."""
        return max(
            self.min_discussion_utterances,
            ceil(self.discussion_utterance_multiplier * num_survivors),
        )

    def reengagement_cooldown(self, num_survivors: int) -> int:
        """M: utterances a directed pair must sit untouched before its K resets."""
        return ceil(self.reengagement_cooldown_multiplier * num_survivors)


DEFAULT_GAME_CONFIG = GameConfig()


def normalize_game_config(config: GameConfig | dict[str, Any] | None) -> GameConfig:
    if config is None:
        return DEFAULT_GAME_CONFIG
    if isinstance(config, GameConfig):
        return config
    return GameConfig.model_validate(config)


def game_config_dict(config: GameConfig | dict[str, Any] | None) -> dict[str, Any]:
    return normalize_game_config(config).model_dump()
