from __future__ import annotations

from math import ceil
from typing import Any

from pydantic import BaseModel, Field, model_validator


class GameConfig(BaseModel):
    initial_roles: list[str] = Field(
        default_factory=lambda: [
            # Lean-eval casting (Phase A #2): 9 players, 3 factions.
            "villager",
            "villager",
            "villager",
            "wolf",
            "wolf",
            "healer",
            "investigator",
            "vigilante",
            "serial_killer",
        ],
        min_length=1,
    )
    player_id_prefix: str = Field(default="player", min_length=1)
    starting_day: int = Field(default=1, ge=1)
    first_voting_day: int = Field(default=2, ge=1)

    # --- Role / faction rules (Phase A #2) ---------------------------------------
    vigilante_bullets: int = Field(default=2, ge=0)
    # Town-side night kills the vigilante may attempt over the whole game. A shot is
    # spent on the attempt (even if healed or whiffed on the night-immune SK).

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
    # All deterministic, pure-function knobs; tune later. See evidence/agent_speaking/.
    discussion_utterance_multiplier: float = Field(default=3.0, gt=0)
    # global hard cap on real utterances/day = ceil(multiplier * surviving players),
    # floored by min_discussion_utterances. Backstop only — pass_turn does the real
    # termination, so this is biased generous to avoid truncating an active day.
    min_discussion_utterances: int = Field(default=6, ge=1)
    per_pair_reengagement_cap: int = Field(default=2, ge=1)
    # K: a directed (speaker -> target, stance) edge can create an obligation at most
    # K times/day (escalation cap). Distinct from the open-edge freshness dedup.
    reengagement_cooldown_multiplier: float = Field(default=3, gt=0)
    # M = ceil(multiplier * surviving players). Once a directed pair has gone M
    # utterances untouched, its K cycle-count resets to 0 so a cooled feud can reopen
    # after the room has moved on. Throttles CONSECUTIVE ping-pong (K caps a burst)
    # without permanently killing a topic for the day; default ~one full table.
    proactive_budget: int = Field(default=3, ge=1)
    # terminate once this many DISTINCT proactive picks pass (decline the floor) in a
    # row on a quiet cycle; any real utterance resets the streak.
    opener_floor: int = Field(default=3, ge=0)
    # The day's first `opener_floor` real utterances bypass the proactive novelty gate, so
    # every day gets a substantive opening before echo-gating (and trailing-pass termination)
    # can kick in. Prevents the gate from collapsing a low-material day to ~1 utterance.

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

    def reengagement_cooldown(self, num_survivors: int) -> int:
        """M: utterances a directed pair must sit untouched before its K resets."""
        return ceil(self.reengagement_cooldown_multiplier * num_survivors)

    def discussion_recursion_limit(self, num_survivors: int) -> int:
        """LangGraph recursion_limit for the SCHEDULE self-loop.

        Each cycle = 2 super-steps (SCHEDULE node + role node). A cycle may be a real
        utterance OR a pass marker: passes consume super-steps but do NOT count toward
        the cap, and up to proactive_budget-1 passes can occur between real utterances
        before a trailing-pass run terminates the day. Worst case is therefore
        ~proactive_budget cycles per utterance slot, so size the limit at
        2 * proactive_budget * cap (+headroom) to guarantee the graceful cap /
        trailing-pass termination always fires before an ungraceful GraphRecursionError.
        """
        return 2 * self.proactive_budget * self.utterance_cap(num_survivors) + 10


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
