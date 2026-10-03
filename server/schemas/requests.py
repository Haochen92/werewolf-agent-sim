"""Request-body models (DTOs) for the HTTP surface.

Deliberately a separate module from ``events.py``: that file is the frozen wire
contract (the tiered event types the frontend builds against, changed only by
ruling), while these are casual per-endpoint request shapes, free to change with
the API. New request/response DTOs belong here, never in the contract module.
"""

from __future__ import annotations

from typing import Annotated, Literal

import unicodedata

from pydantic import BaseModel, ConfigDict, Field, field_validator

from server.schemas.events import Role, Winner


# --- the menu: what the page fetches before any game exists ------------------------


class ModelRow(BaseModel):
    """One entry of the GET /models served-game menu."""

    model: str
    label: str
    rescue_model: str | None
    """Same-credential rescue model; None = no rescue (the typed technical-pass
    path still keeps the game moving)."""
    house_funded: bool = False
    """The server can pay for this model. Whether it will right now is ``house`` on the
    menu; a player's own key runs any row regardless."""
    is_default: bool = False
    """The row a game runs on when the player picks none. A live setting, not a fixed
    position in the list."""
    needs_key: bool = True
    """Starting a game on this row right now requires the player's own key: the row is
    not house-funded, or the house is off, or today's house games are used up. The same
    rule the door applies, said in advance so the client can hold the submit."""



class HouseFunding(BaseModel):
    """The house's purse for today, as GET /models reports it to the client."""

    enabled: bool
    """False means every model needs the player's key, whatever the row says."""
    games_per_day: int
    remaining: int
    """House-funded games the server will still start today. 0 = bring a key."""
    reset_at: str
    """ISO-8601 UTC: when the daily count starts again."""



class ModelsMenu(BaseModel):
    """GET /models response: the menu, and what the house will pay for right now."""

    models: list[ModelRow]
    house: HouseFunding


# --- the puppets: the catalogue a player picks from -----------------------------------


class CharacterCard(BaseModel):
    """One row of GET /characters: a puppet a player may stand as. Costumes say nothing
    about roles; the cast is dealt independently of the deal."""

    id: str
    """The slug the sprites are filed under; stable, and what a pick names."""
    display_name: str
    """What people read; may change without touching any record."""
    retired: bool = False
    """No longer picked or drawn, but old games still name it."""


# --- the solo door: one person's table, started on the spot ------------------------


class NewSoloGame(BaseModel):
    """POST /games body: the solo door. One person's table, started on the spot, with
    them in a seat or only watching an all-AI game. Rooms, where several people share a
    table, are the other door (POST /rooms) and a deliberately separate contract."""

    human: bool = False
    human_role: Role | None = None
    """Role choice lives ONLY here: solo has no other players to leak it to.
    Rooms always deal random seats."""
    api_key: str = ""
    """BYOK (optional): the player's own key funds this game's model calls.
    Ephemeral pass-through — held in session memory for the run, never stored or
    recorded; empty = the server's configured backend pays."""
    model: str = ""
    """Game model, from SUPPORTED_GAME_MODELS only (the tested list; GET /models).
    House-funded rows may use the server backend; all other choices require api_key.
    Empty = the default model."""
    memory: bool = False
    """AI memory (experimental): every AI seat consults lessons from past games before
    each decision, and the replay shows which lessons it weighed. Off by default — a
    memory-on game makes an extra model call per AI decision from day 2."""
    character: str | None = None
    """The puppet the human stands as, by id from GET /characters; None lets the house
    draw one. Ignored for an all-AI game. A puppet says nothing about a role."""



class GameCreated(BaseModel):
    """POST /games and POST /games/{id}/start response."""

    game_id: str
    seat_token: str | None = None
    """Solo door only: the body copy of the seat cookie set on this response (stash
    it client-side; POST /rejoin restores a lost cookie from it). None for LLM-only
    games and for /start — room seats received their tokens at /join."""


# --- the room door: a shared table, seats claimed before the start -----------------


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
    """Game model from SUPPORTED_GAME_MODELS. House-funded rows need no api_key;
    all other choices require one. Empty = default."""
    memory: bool = False
    """AI memory (experimental), chosen by the host for the whole table. Same semantics
    as the solo door."""
    name: str = Field(default="", max_length=40)
    """Public room title shown in the GET /rooms browser; "" renders as unnamed
    client-side. Capped server-side — it is the one free-text field strangers see."""



class RoomCreated(BaseModel):
    """POST /rooms response."""

    game_id: str
    """Also the room id: the registry swap at /start keeps it, so the room URL is
    the game URL before and after."""
    host_key: str
    """The creator's credential for POST /start — returned exactly once, here
    (never in status)."""



class RoomSummary(BaseModel):
    """One row of GET /rooms: the public face of a waiting room. Also the POST /lock
    response (the host's fresh view after flipping the flag). Never any secret —
    no host_key, no tokens."""

    game_id: str
    name: str
    players: list[str]
    """Display names in join order (the roster is public — see server/lobby.py)."""
    host: str | None = None
    """The name shown as the room's host: whoever took the first seat (normally the
    person who created the room). None while nobody has joined."""
    max_seats: int
    locked: bool
    """Locked rooms still list (the client renders them unjoinable) — vanishing
    mid-browse reads as a bug; a visible lock reads as a full table."""
    created_at: str
    """ISO-8601 UTC creation time — the client's 'created N min ago' source."""



class JoinGame(BaseModel):
    """POST /games/{id}/join body. No role field on purpose: rooms deal random
    seats (role choice is solo-only, on the instant-start path)."""

    name: str = "human"
    """Display name for the room roster (public to the room). Spaces are trimmed and
    collapsed; at most ``MAX_PLAYER_NAME`` characters, of letters in any script, digits,
    spaces, hyphens, apostrophes and dots, so it fits a name tag and prints in any font."""

    @field_validator("name")
    @classmethod
    def _a_printable_name(cls, value: str) -> str:
        name = " ".join(value.split())
        if not name:
            raise ValueError("a name is needed")
        if len(name) > MAX_PLAYER_NAME:
            raise ValueError(f"a name has at most {MAX_PLAYER_NAME} characters")
        bad = sorted({ch for ch in name if not _name_char(ch)})
        if bad:
            raise ValueError("a name uses letters, digits, spaces and - ' . only "
                             f"(not {' '.join(bad)})")
        return name


MAX_PLAYER_NAME = 12
"""The longest name a player boards with: what a platform name tag holds at full size."""

_NAME_MARKS = set(" -'.’")


def _name_char(ch: str) -> bool:
    """Letters (any script, with their accents), digits, and a few name marks."""
    return ch in _NAME_MARKS or unicodedata.category(ch)[0] in "LMN"



class ChooseCharacter(BaseModel):
    """POST /games/{id}/character body: the puppet this seat stands as, picked in the
    waiting room. The seat cookie says whose seat."""

    character: str | None = None
    """An id from GET /characters, or None to give the pick up and let the house draw."""


class SeatJoined(BaseModel):
    """POST /games/{id}/join and POST /games/{id}/rejoin response."""

    token: str
    """The seat's secret — proof of ownership (no accounts: holding it IS the
    identity). Also set as an HttpOnly cookie on this response; this body copy is
    the client's backup (localStorage) for POST /rejoin after cookie loss."""



class RejoinGame(BaseModel):
    """POST /games/{id}/rejoin body: re-prove seat ownership after cookie loss
    (new device, cleared browsing data) with the stashed body-copy token."""

    token: str


# --- a running game: the poll-side snapshot, a turn, a key after a restart ---------


class GameStatus(BaseModel):
    """GET /games/{id} response: the poll-side snapshot (the stream carries the rest).

    One shape for both registry phases — a lobby fills only the header trio
    (game_id, state, players) and leaves the game fields at their defaults."""

    game_id: str
    state: Literal["waiting", "running", "finished", "dropped"]
    """Lifecycle: "waiting" (lobby), "running", "finished" (game over), "dropped" (ended
    without finishing; ``error`` says why). A task that died while the game was still
    live also reports "running" with ``error`` set until it leaves the registry."""
    server_time: str
    """ISO-8601 UTC wall clock sampled with this snapshot. The browser subtracts its
    own receipt-time clock so AFK deadlines remain honest on devices with clock skew."""
    players: list[str] = Field(default_factory=list)
    """The lobby roster (display names). Empty once running: engine seats
    replace the roster at start."""
    host: str | None = None
    """Waiting rooms only: the name shown as the room's host, whoever took the first
    seat (normally the room's creator). None while nobody has joined, and once running."""
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
    characters: list[str | None] = Field(default_factory=list)
    """Waiting rooms only: each seat's chosen puppet, aligned with ``players`` (None
    where nobody chose yet). Once running, ``cast`` says who stands where."""
    you_aboard: int | None = None
    """Waiting rooms only: where the requester's own seat stands in ``players`` (0 = the
    first to join), from their seat cookie. None for someone without a seat, and once
    running (``you`` takes over then). Names can repeat, so this, not the name, is how a
    browser finds itself on the roster."""
    pending_input: bool = False
    """A seat this viewer may see owes input: exactly ``pending_seats`` being non-empty.
    False for live spectators; it must not reveal that a private night turn exists."""
    pending_seats: list[str] = Field(default_factory=list)
    """Pending seats visible to this viewer: only their own seat during play, empty
    for spectators. At game over all seats become visible, as with the event stream."""
    deadlines: dict[str, str] = Field(default_factory=dict)
    """AFK deadlines (ISO-8601 UTC) for visible pending seats only: when each turn is
    delegated to its agent. Empty for live spectators, solo games (no timer), and
    whenever the viewer has no pending seat."""
    game_over: bool = False
    """The engine has declared a winner; the observer backlog is being or has been streamed."""
    last_seq: int = 0
    """High-water mark of the durable log — a reconnect cursor for ?last_seq=."""
    awaiting_key: bool = False
    """The game ran on a player's key and was rebuilt after a restart without it. It is
    live but idle until a seat holder supplies the key again (POST /games/{id}/key)."""
    winner: Winner | None = None
    """The winning faction, once the game is over and served from its archived row."""
    archived: bool = False
    """True when this snapshot came from the database row rather than a live game: the
    game has ended and left the live registry. There is no stream to open; a finished
    game has a replay under the same id."""
    alive_role_counts: dict[str, int] = Field(default_factory=dict)
    """Public census only: fixed cast minus announced deaths, never engine state."""
    cast: list[str] = Field(default_factory=list)
    """Which puppet stands at each engine seat, in seat order (index 0 is player_1),
    by character id. Empty until the seats are dealt, and for games recorded before
    casts were stored: the client then shows the cast it always derived."""
    error: str | None = None
    """The session's death report (key-redacted); None while healthy."""



class TurnAccepted(BaseModel):
    """POST /games/{id}/turns response."""

    status: str = "accepted"



class DraftRequest(BaseModel):
    """POST /games/{id}/draft body: what the player wants from their agent's line, if
    anything. All of it is optional; with none of it the agent writes its own line."""

    notes: str = Field(default="", max_length=500)
    """What the line should do, in the player's own words: "push on player_5", "softer,
    ask player_4 instead". Empty (or left out) asks the agent for its own line."""
    current: str = Field(default="", max_length=1000)
    """The line now in the player's reply box. Read only with notes: it is the draft the
    notes revise."""
    seat_notes: dict[str, Annotated[str, Field(max_length=300)]] = Field(
        default_factory=dict, max_length=16)
    """The player's notebook: a note per seat, by player id ("player_5"). Sent only when
    the player chose to share it with their agent; never stored."""
    suspect: str = Field(default="", max_length=32)
    """The seat the player marked as their suspect, by player id; empty for none."""



class DraftResponse(BaseModel):
    """POST /games/{id}/draft response: a line the player may send as-is, edit, or drop.
    Nothing has entered the game; POST /turns still says it."""

    draft: str
    """The line. Empty when the agent, left to itself, would pass this turn."""
    drafts_left: int
    """How many more drafts this turn allows. The wait for each is credited back to the
    seat's clock, so the cap is what keeps a turn from stretching."""
    deadline: str | None = None
    """The seat's countdown after the wait was credited back (ISO-8601 UTC); None when
    no clock runs (solo games)."""



class FundGame(BaseModel):
    """POST /games/{id}/key body: a seat holder's key to resume a game that lost its
    funding in a restart. Tried on the provider before the game moves; never stored."""

    api_key: str = Field(min_length=1)


# --- admin: the house's knobs -------------------------------------------------------


class HouseView(HouseFunding):
    """GET/PUT /admin/house response: the purse plus the knobs behind it."""

    default_model: str
    used_today: int



class HouseUpdate(BaseModel):
    """PUT /admin/house body: any subset of the knobs."""

    model_config = ConfigDict(extra="forbid")

    enabled: bool | None = None
    default_model: str | None = None
    """Must be a house-funded row of the catalogue."""
    games_per_day: int | None = None
