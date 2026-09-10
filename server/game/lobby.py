"""The waiting room: a lobby game starts as a GameLobby and becomes a GameSession.

POST /games (lobby=true) puts a GameLobby in the registry; /join claims human seats;
the host's /start builds the real GameSession under the SAME game_id and swaps it
into the registry — the room URL is the game URL, before and after.

Rooms are multiplayer-only and deal every human a random seat (owner ruling: role
choice inside a shared room can't be clean — honored picks make join order a race,
denied picks leak that a human holds the role. Solo role choice lives on the
instant-start path, POST /games {human, human_role}, where there is no one to leak
to). A room therefore carries no per-joiner secrets at all — the roster is public.

Deliberately NOT a state inside GameSession: session construction fires engine side
effects (memory seeding, runnable-config minting) that a waiting room must not, and
a lobby has none of a session's machinery (no stream, no log, no translator).
Registry values are the union GameLobby | GameSession; server.dependencies sorts
callers to the right door (status serves both; turns/events demand a session).

Error contract (mapped to HTTP by the routes): LookupError = state conflict (409);
the host_key check lives in the route (403).
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import NamedTuple
from uuid import uuid4

from Agents.config import RunConfig
from Agents.config.game import GameConfig

# Human-seat capacity = the cast size (the engine deals RunConfig.human_player seats,
# capped at the cast; verified end-to-end by the 2-human real-graph smoke 2026-08-19).
# Derived, not hardcoded: when the cast becomes a room option, the cap follows it.
MAX_HUMAN_SEATS = len(GameConfig().initial_roles)


class HumanSeat(NamedTuple):
    """One claimed seat: the public roster name + the private proof of ownership."""

    name: str
    token: str


class GameLobby:
    """One waiting room: identity + host credential + the joined seats.

    Two credentials, both uuid4, both delivered exactly once in a response body:
    host_key (create response) proves "may start the game"; each seat's token
    (join response + HttpOnly cookie) proves "owns this seat" for turns, private
    events, and rejoin — there are no accounts, so holding the token IS the identity.
    """

    def __init__(self, *, api_key: str = "", model: str = "", name: str = "") -> None:
        self.game_id = str(uuid4())
        self.host_key = str(uuid4())
        # BYOK travels creation -> start: the creator funds the game.
        self.api_key = api_key
        self.model = model
        self.name = name
        """Public room title for the GET /rooms browser; "" = unnamed."""
        self.locked = False
        """Host-set (POST /lock): a locked room bounces joins but keeps its seats —
        the invite-link era's implicit lock ("don't share the link"), made explicit
        now that rooms are publicly listed."""
        self.created_at = datetime.now(timezone.utc)
        """Listing TTL anchor: old rooms drop out of GET /rooms (browse filter only
        — the direct room URL keeps working)."""
        self.seats: list[HumanSeat] = []

    @property
    def players(self) -> list[str]:
        """The public roster: display names only, never the tokens."""
        return [s.name for s in self.seats]

    @property
    def tokens(self) -> list[str]:
        """Seat tokens in join order. Join order IS deal order (the orchestrator
        builds human_players deterministically), so at start the GameSession maps
        token i -> human_players[i]."""
        return [s.token for s in self.seats]

    def join(self, name: str) -> tuple[int, str]:
        """Claim a human seat; returns (1-based position, the seat's secret token)."""
        if self.locked:
            raise LookupError("room is locked — ask the host to unlock it")
        if len(self.seats) >= MAX_HUMAN_SEATS:
            raise LookupError(
                "all human seats are taken — spectate via GET /games/{id}/events "
                "(spectators need no seat)")
        seat = HumanSeat(name=name, token=str(uuid4()))
        self.seats.append(seat)
        return len(self.seats), seat.token

    def position_of(self, token: str) -> int | None:
        """1-based join position owning this token; None = unknown (403 material)."""
        for i, seat in enumerate(self.seats, start=1):
            if seat.token == token:
                return i
        return None

    def run_config(self) -> RunConfig:
        """Assemble the started game's config. Passing our game_id through keeps the
        room URL valid across the registry swap (RunConfig only mints when blank).
        No human_role ever: rooms deal random seats (see the module docstring)."""
        return RunConfig(
            game_id=self.game_id,
            human_player=len(self.seats),
            # A served game is never mined into the memory store (the CLI human-game rule).
            memory_persistence={"dump_enabled": False},
        )
