"""DTOs returned by the public replay API."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

from server.schemas import events as ev
from server.schemas.events import Winner


class ReplayBase(BaseModel):
    """One row returned by ``GET /replays``."""

    model_config = ConfigDict(from_attributes=True)

    game_id: str
    finished_at: datetime | None = None
    winner: Winner
    days: int
    ended_phase: Literal["day", "voting", "night"] | None = None
    """The part of the day the game ended in: read with ``days``, "night" means the game
    ended on night ``days``. None for a game with no phase change on record."""
    n_events: int
    n_humans: int
    cast_role_counts: dict[str, int]
    model: str = ""
    """The model id the game was played on, as the catalogue names it. Empty for games
    recorded before the column existed."""
    memory: bool = False
    """Whether the AI seats consulted past-game lessons. False for games recorded
    before the column existed (they all ran memory-off)."""


class ReplayGame(ReplayBase):
    """One complete replay with every stored event revalidated for the wire."""

    events: list[ev.DurableGameEvent]
