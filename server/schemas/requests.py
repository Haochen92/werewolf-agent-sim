"""Request-body models (DTOs) for the HTTP surface.

Deliberately a separate module from ``events.py``: that file is the frozen wire
contract (the tiered event types the frontend builds against, changed only by
ruling), while these are casual per-endpoint request shapes, free to change with
the API. New request/response DTOs belong here, never in the contract module.
"""

from __future__ import annotations

from pydantic import BaseModel


class NewGame(BaseModel):
    """POST /games body."""

    human: bool = False
    human_role: str | None = None
    api_key: str = ""
    """BYOK (optional): the player's own key funds this game's model calls.
    Ephemeral pass-through — held in session memory for the run, never stored or
    recorded; empty = the server's configured backend pays."""
    model: str = ""
    """Game model, from SUPPORTED_GAME_MODELS only (the tested list; GET /models).
    Requires api_key — the model choice decides which provider the key must belong
    to. Empty = the default model."""


class ModelRow(BaseModel):
    """One entry of the GET /models BYOK menu."""

    model: str
    label: str
    rescue_model: str | None
    """Same-credential rescue model; None = no rescue (the typed technical-pass
    path still keeps the game moving)."""


class ModelsMenu(BaseModel):
    """GET /models response. First entry = the default for a bare key."""

    models: list[ModelRow]


class GameCreated(BaseModel):
    """POST /games response."""

    game_id: str


class GameStatus(BaseModel):
    """GET /games/{id} response: the poll-side snapshot (the stream carries the rest)."""

    game_id: str
    human_player: str
    """The seat the engine assigned the human; "" until INITIALIZE_GAME lands
    (or for an LLM-only game)."""
    pending_input: bool
    game_over: bool
    last_seq: int
    """High-water mark of the durable log — a reconnect cursor for ?last_seq=."""
    alive_role_counts: dict[str, int]
    """Public census only: fixed cast minus announced deaths, never engine state."""
    error: str | None
    """The session's death report (key-redacted); None while healthy."""


class TurnAccepted(BaseModel):
    """POST /games/{id}/turns response."""

    status: str = "accepted"
