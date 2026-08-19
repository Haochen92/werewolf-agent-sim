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

from uuid import uuid4

from Agents.config import RunConfig
from Agents.config.game import GameConfig

# Human-seat capacity = the cast size (the engine deals RunConfig.human_player seats,
# capped at the cast; verified end-to-end by the 2-human real-graph smoke 2026-08-19).
# Derived, not hardcoded: when the cast becomes a room option, the cap follows it.
MAX_HUMAN_SEATS = len(GameConfig().initial_roles)


class GameLobby:
    """One waiting room: identity + host credential + the joined seats (names only).

    host_key is returned once, in the create response — the creator's proof for
    /start ("creator starts manually" ruling). Slice 3 replaces this and the seat
    identity story with real per-seat tokens.
    """

    def __init__(self, *, api_key: str = "", model: str = "") -> None:
        self.game_id = str(uuid4())
        self.host_key = str(uuid4())
        # BYOK travels creation -> start: the creator funds the game.
        self.api_key = api_key
        self.model = model
        self.players: list[str] = []

    def join(self, name: str) -> int:
        """Claim a human seat; returns the 1-based seat position."""
        if len(self.players) >= MAX_HUMAN_SEATS:
            raise LookupError(
                "all human seats are taken — spectate via GET /games/{id}/events "
                "(spectators need no seat)")
        self.players.append(name)
        return len(self.players)

    def run_config(self) -> RunConfig:
        """Assemble the started game's config. Passing our game_id through keeps the
        room URL valid across the registry swap (RunConfig only mints when blank).
        No human_role ever: rooms deal random seats (see the module docstring)."""
        return RunConfig(
            game_id=self.game_id,
            human_player=len(self.players),
            # A served game is never mined into the memory store (the CLI human-game rule).
            memory_persistence={"dump_enabled": False},
        )
