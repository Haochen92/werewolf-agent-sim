"""The waiting room a multiplayer game starts in: one GameLobby per room.

POST /rooms creates one, players claim seats with POST /games/{id}/join, and the host
starts play with POST /games/{id}/start. The game keeps the room's id: the registry in
game/live_game_registry.py builds the running GameSession and puts it where the lobby was, so the
room link still works once the game has begun.

Everyone in a room is dealt a random seat. Picking a role in a shared room cannot be
fair: if picks are honoured, joining first wins the role, and if one is refused, the
refusal tells the asker that a human already holds it. Solo players do pick their role,
on the instant-start door POST /games, where there is nobody to leak to. A room therefore
keeps no per-player secrets, and its roster is public.

A lobby is its own object rather than an early state of GameSession because building a
session starts real engine work (seeding memory, minting a run config) that a room of
people who have not started yet must not trigger, and because a room has none of a
session's machinery: no event stream, no log, no translator.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import NamedTuple
from uuid import uuid4

from Agents.config import RunConfig
from Agents.config.game import GameConfig

# Maximum number of human seats is equal to
# the maximum number of characters in a game, defined in configuration.
MAX_HUMAN_SEATS = len(GameConfig().initial_roles)


class HumanSeat(NamedTuple):
    """One claimed seat: the name everyone sees, and the secret token that proves the
    seat belongs to this player."""

    name: str
    token: str


class GameLobby:
    """A waiting room for multiplayer games.

    Key attributes:
        game_id: The game's id, minted here. The running game keeps it, so the room link
            still works after the game starts.
        host_key: A secret handed back once at creation. Presenting it is what allows
            starting or locking the room.
        seats: The human players who joined, in join order. Each seat holds the chosen
            name and a token that uniquely identifies that player. There are no accounts,
            so holding the token is the only proof that a seat is yours.
    """

    def __init__(self, *, api_key: str = "", model: str = "", name: str = "") -> None:
        self.game_id = str(uuid4())
        self.host_key = str(uuid4())
        # The creator's own API key, held until the game starts: whoever creates the room
        # pays for the models it runs on.
        self.api_key = api_key
        self.model = model
        """The model the game will run on, chosen when the room is created."""
        self.name = name
        """Public room title for the GET /rooms browser; "" = unnamed."""
        self.locked = False
        """Set by the host through POST /games/{id}/lock. A locked room turns new joins
        away but keeps the players who are already in it."""
        self.created_at = datetime.now(timezone.utc)
        """When the room was opened. GET /rooms stops listing rooms older than the
        browsing window (two hours by default, see ROOM_LIST_TTL_SECONDS);
        the room's own URL keeps working."""
        self.seats: list[HumanSeat] = []

    @property
    def players(self) -> list[str]:
        """The public roster: display names only, never the tokens."""
        return [s.name for s in self.seats]

    @property
    def tokens(self) -> list[str]:
        """Seat tokens in the order people joined. The engine deals its human seats in
        that same order, so the first token belongs to the first human player."""
        return [s.token for s in self.seats]

    def join(self, name: str) -> str:
        """Claim a human seat and return its freshly minted secret token. The token is
        the only proof that a browser owns this seat; nothing else identifies a player.
        Raises LookupError when the room is locked or full; the route turns that into a 409."""
        if self.locked:
            raise LookupError("room is locked — ask the host to unlock it")
        if len(self.seats) >= MAX_HUMAN_SEATS:
            raise LookupError(
                "all human seats are taken — spectate via GET /games/{id}/events "
                "(spectators need no seat)")
        seat = HumanSeat(name=name, token=str(uuid4()))
        self.seats.append(seat)
        return seat.token

    def owns(self, token: str) -> bool:
        """Whether this token belongs to one of the room's seats."""
        return any(seat.token == token for seat in self.seats)

    def run_config(self) -> RunConfig:
        """Build the config the started game runs on. The room's own game_id is passed
        through so the room link still works after the swap (RunConfig only invents an id
        when it is given none). A role is never requested: rooms deal random seats."""
        return RunConfig(
            game_id=self.game_id,
            human_player=len(self.seats),
            # A game played over the server is never mined into the memory store.
            memory_persistence={"dump_enabled": False},
        )
