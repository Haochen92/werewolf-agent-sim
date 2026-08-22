"""DTOs returned by the public replay API."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from server.schemas import events as ev


class ReplayBase(BaseModel):
    """One row returned by ``GET /replays``."""

    model_config = ConfigDict(from_attributes=True)

    game_id: str
    finished_at: datetime | None = None
    winner: str
    days: int
    n_events: int
    n_humans: int
    cast_role_counts: dict[str, int]


class ReplayGame(ReplayBase):
    """One complete replay with every stored event revalidated for the wire."""

    events: list[ev.DurableGameEvent]
