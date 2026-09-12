"""The house's purse: whether the server pays for games, which model it pays for by
default, and how many games a day it will fund.

Three knobs, read live. An operator changes them through PUT /admin/house and the change
takes effect within a few seconds, without a restart or a rebuild. A knob that was never
set, or every knob when storage is off, falls back to the process settings (the HOUSE_*
fields in config.py). The count of house-funded games started today comes from the games
table itself: every started game has a row that says whether a player key paid for it, so
nothing extra is kept.

Costs are the reason. The credits behind house funding are finite, so the demo needs a
ceiling it cannot pass, and the ceiling must be movable on the day rather than on the
next deploy. A player who brings their own key is never counted against it.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

from server.config import ServerSettings, server_settings
from server.game.model_catalog import SUPPORTED_GAME_MODELS
from server.storage.game_repository import GameRepository
from server.storage.settings_repository import SettingsRepository

logger = logging.getLogger(__name__)

KEY_ENABLED = "house.enabled"
KEY_DEFAULT_MODEL = "house.default_model"
KEY_GAMES_PER_DAY = "house.games_per_day"

HOUSE_MODELS = [m for m, row in SUPPORTED_GAME_MODELS.items() if row.house_funded]


class ModelNeedsKey(Exception):
    """The chosen model is not house-funded, or the house will not fund it right now."""


class HouseClosed(ModelNeedsKey):
    """House funding is unavailable: switched off, or today's games are spent.
    ``reset_at`` says when the daily count starts again; None when it is switched off."""

    def __init__(self, message: str, *, reset_at: datetime | None) -> None:
        super().__init__(message)
        self.reset_at = reset_at


@dataclass(frozen=True)
class HouseStatus:
    """What the house will do for the next game, as of now."""

    enabled: bool
    default_model: str
    games_per_day: int
    used_today: int
    reset_at: datetime

    @property
    def remaining(self) -> int:
        return max(0, self.games_per_day - self.used_today) if self.enabled else 0


def _day_window(now: datetime) -> tuple[datetime, datetime]:
    """The UTC day the count lives in: its start and the moment it resets."""
    start = now.astimezone(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    return start, start + timedelta(days=1)


class HousePolicy:
    """Decides, for one new game, which model it runs on and who pays."""

    def __init__(self, settings: SettingsRepository, games: GameRepository,
                 defaults: ServerSettings = server_settings, *,
                 cache_seconds: float = 10.0) -> None:
        self._settings = settings
        self._games = games
        self._defaults = defaults
        self._cache_seconds = cache_seconds
        self._knobs: dict[str, Any] | None = None
        self._loaded_at = 0.0

    # -- the knobs --------------------------------------------------------------------------

    async def _load(self) -> dict[str, Any]:
        """The stored knobs, re-read at most every few seconds so an admin change lands
        without a restart and a busy server does not query them per request."""
        if self._knobs is None or time.monotonic() - self._loaded_at > self._cache_seconds:
            self._knobs = await self._settings.load()
            self._loaded_at = time.monotonic()
        return self._knobs

    def _default_model(self, knobs: dict[str, Any]) -> str:
        """The stored default if it is still a house-funded row, else the process default,
        else the first house-funded row in the catalogue."""
        for candidate in (knobs.get(KEY_DEFAULT_MODEL), self._defaults.HOUSE_DEFAULT_MODEL):
            if candidate in HOUSE_MODELS:
                return candidate
        return HOUSE_MODELS[0]

    async def status(self, now: datetime | None = None) -> HouseStatus:
        knobs = await self._load()
        now = now or datetime.now(timezone.utc)
        start, reset_at = _day_window(now)
        enabled = bool(knobs.get(KEY_ENABLED, self._defaults.HOUSE_FUNDED_ENABLED))
        per_day = int(knobs.get(KEY_GAMES_PER_DAY, self._defaults.HOUSE_GAMES_PER_DAY))
        used = await self._games.count_house_games_since(start) if enabled else 0
        return HouseStatus(enabled=enabled, default_model=self._default_model(knobs),
                           games_per_day=per_day, used_today=used, reset_at=reset_at)

    async def update(self, *, enabled: bool | None = None, default_model: str | None = None,
                     games_per_day: int | None = None) -> HouseStatus:
        """Change the knobs an operator may change. Takes effect at once in this process
        and is persisted when storage is on. ValueError on a bad value."""
        if default_model is not None and default_model not in HOUSE_MODELS:
            raise ValueError(f"default_model must be a house-funded row: {HOUSE_MODELS}")
        if games_per_day is not None and games_per_day < 0:
            raise ValueError("games_per_day must be 0 or more")
        changes = {KEY_ENABLED: enabled, KEY_DEFAULT_MODEL: default_model,
                   KEY_GAMES_PER_DAY: games_per_day}
        knobs = dict(await self._load())
        for key, value in changes.items():
            if value is not None:
                knobs[key] = value
                await self._settings.save(key, value)
                logger.info("house: %s set to %r", key, value)
        self._knobs, self._loaded_at = knobs, time.monotonic()
        return await self.status()

    # -- the decision -----------------------------------------------------------------------

    async def authorize(self, api_key: str, model: str) -> str:
        """Settle which model a new game runs on and who pays for it. Returns the model,
        resolved from "" to the house default. Raises LookupError for a model not on the
        menu, ModelNeedsKey when the row is player-funded and no key came, and HouseClosed
        when the row is house-funded but the house is off or has spent today's games. A
        player who brings a key may run any row, and is never counted."""
        status = await self.status()
        model = model or status.default_model
        row = SUPPORTED_GAME_MODELS.get(model)
        if row is None:
            raise LookupError(
                f"unsupported model; pick from GET /models: {sorted(SUPPORTED_GAME_MODELS)}")
        if api_key:
            return model
        if not row.house_funded:
            raise ModelNeedsKey(f"{model} requires api_key")
        if not status.enabled:
            raise HouseClosed("house funding is switched off; supply your own api_key",
                              reset_at=None)
        if status.remaining <= 0:
            raise HouseClosed(
                f"the house has funded its {status.games_per_day} games for today; supply "
                f"your own api_key or come back after {status.reset_at.isoformat()}",
                reset_at=status.reset_at)
        return model
