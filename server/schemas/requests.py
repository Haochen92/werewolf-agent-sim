"""Request-body models (DTOs) for the HTTP surface.

Deliberately a separate module from ``events.py``: that file is the frozen wire
contract (the tiered event types the frontend builds against, changed only by
ruling), while these are casual per-endpoint request shapes, free to change with
the API. New request/response DTOs belong here, never in the contract module.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class NewGame(BaseModel):
    """POST /games body: the instant-start (solo / LLM-only) door. Multiplayer
    rooms are created at POST /rooms — a deliberately separate contract."""

    human: bool = False
    human_role: str | None = None
    """Role choice lives ONLY here: solo has no other players to leak it to.
    Rooms always deal random seats."""
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
    """POST /games and POST /games/{id}/start response."""

    game_id: str
    seat_token: str | None = None
    """Solo door only: the body copy of the seat cookie set on this response (stash
    it client-side; POST /rejoin restores a lost cookie from it). None for LLM-only
    games and for /start — room seats received their tokens at /join."""


class NewRoom(BaseModel):
    """POST /rooms body: the multiplayer door. No human/role fields ON PURPOSE —
    a room seats humans only via POST /join and always deals random roles, so the
    concept is unrepresentable here instead of guarded; extra="forbid" turns a
    client sending instant-start fields into a clean 422."""

    model_config = ConfigDict(extra="forbid")

    api_key: str = ""
    """BYOK (optional): the creator's key funds the whole game. Same semantics as
    the instant-start door."""
    model: str = ""
    """Game model from SUPPORTED_GAME_MODELS; requires api_key; empty = default."""
    name: str = Field(default="", max_length=40)
    """Public room title shown in the GET /rooms browser; "" renders as unnamed
    client-side. Capped server-side — it is the one free-text field strangers see."""


class RoomSummary(BaseModel):
    """One row of GET /rooms: the public face of a waiting room. Also the POST /lock
    response (the host's fresh view after flipping the flag). Never any secret —
    no host_key, no tokens."""

    game_id: str
    name: str
    players: list[str]
    """Display names in join order (the roster is public — see server/lobby.py)."""
    max_seats: int
    locked: bool
    """Locked rooms still list (the client renders them unjoinable) — vanishing
    mid-browse reads as a bug; a visible lock reads as a full table."""
    created_at: str
    """ISO-8601 UTC creation time — the client's 'created N min ago' source."""


class RoomCreated(BaseModel):
    """POST /rooms response."""

    game_id: str
    """Also the room id: the registry swap at /start keeps it, so the room URL is
    the game URL before and after."""
    host_key: str
    """The creator's credential for POST /start — returned exactly once, here
    (never in status)."""


class JoinGame(BaseModel):
    """POST /games/{id}/join body. No role field on purpose: rooms deal random
    seats (role choice is solo-only, on the instant-start path)."""

    name: str = "human"
    """Display name for the room roster (public to the room)."""


class SeatJoined(BaseModel):
    """POST /games/{id}/join and POST /games/{id}/rejoin response."""

    position: int
    """1-based join order — the roster index, not an engine seat (the engine
    assigns player ids only at game start)."""
    token: str
    """The seat's secret — proof of ownership (no accounts: holding it IS the
    identity). Also set as an HttpOnly cookie on this response; this body copy is
    the client's backup (localStorage) for POST /rejoin after cookie loss."""


class RejoinGame(BaseModel):
    """POST /games/{id}/rejoin body: re-prove seat ownership after cookie loss
    (new device, cleared browsing data) with the stashed body-copy token."""

    token: str


class GameStatus(BaseModel):
    """GET /games/{id} response: the poll-side snapshot (the stream carries the rest).

    One shape for both registry phases — a lobby fills only the header trio
    (game_id, state, players) and leaves the game fields at their defaults."""

    game_id: str
    state: str
    """Lifecycle: "waiting" (lobby) | "running" | "finished" (game_over). A dead
    task stays "running" with the error field set — error is orthogonal."""
    players: list[str] = Field(default_factory=list)
    """The lobby roster (display names). Empty once running: engine seats
    replace the roster at start."""
    max_seats: int = 0
    """Human-seat capacity of a waiting room — the client's "room full" signal
    (len(players) == max_seats). 0 once running; the server 409 stays the
    authority either way."""
    name: str = ""
    """The room title (waiting rooms only; "" once running)."""
    locked: bool = False
    """Waiting rooms only: joins currently bounce (the host may unlock)."""
    human_players: list[str] = Field(default_factory=list)
    """The seats the engine dealt to humans; empty until INITIALIZE_GAME lands
    (or for an LLM-only game)."""
    you: str | None = None
    """The requester's OWN engine seat, resolved from their seat cookie — how the
    client learns which player it is. None for spectators, waiting rooms, and the
    moment before seats are dealt."""
    pending_input: bool = False
    pending_seats: list[str] = Field(default_factory=list)
    """Which seats owe input right now — several at once when a parallel superstep
    (night fan-out, votes) interrupts for more than one human."""
    deadlines: dict[str, str] = Field(default_factory=dict)
    """Per-seat AFK deadlines (ISO-8601 UTC): when each pending seat's turn will be
    delegated to its agent — the client's countdown source. Empty in solo games
    (no timer) and whenever nobody owes input."""
    game_over: bool = False
    last_seq: int = 0
    """High-water mark of the durable log — a reconnect cursor for ?last_seq=."""
    alive_role_counts: dict[str, int] = Field(default_factory=dict)
    """Public census only: fixed cast minus announced deaths, never engine state."""
    error: str | None = None
    """The session's death report (key-redacted); None while healthy."""


class TurnAccepted(BaseModel):
    """POST /games/{id}/turns response."""

    status: str = "accepted"
