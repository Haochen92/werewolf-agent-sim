"""HTTP policies shared by the game-creation and room routers."""

from datetime import datetime, timezone

from fastapi import HTTPException, Response

from server.config import server_settings
from server.dependencies import seat_cookie_name
from server.game.game_session import GameSession
from server.game.lobby import MAX_HUMAN_SEATS, GameLobby
from server.house import HouseClosed, HousePolicy, ModelNeedsKey
from server.schemas.requests import GameStatus

_SEAT_COOKIE_MAX_AGE = 24 * 3600  # comfortably outlives any in-memory game


def set_seat_cookie(response: Response, game_id: str, token: str) -> None:
    """Attach the per-game seat credential using the server's cookie policy.

    EventSource cannot set headers, but browsers attach cookies to SSE requests.
    HttpOnly keeps the credential outside page JavaScript; the path scopes it to
    one game; SameSite=Lax requires the deployed UI and API to remain same-site.
    The optional path prefix is the browser-visible mount point (``/api`` in
    production), not the prefix-stripped path FastAPI receives from Caddy.
    ``SEAT_COOKIE_SECURE`` stays off for plain-HTTP development and on behind TLS.
    """
    response.set_cookie(
        key=seat_cookie_name(game_id),
        value=token,
        max_age=_SEAT_COOKIE_MAX_AGE,
        path=f"{server_settings.seat_cookie_path_prefix}/games/{game_id}",
        httponly=True,
        samesite="lax",
        secure=server_settings.SEAT_COOKIE_SECURE,
    )


def clear_seat_cookie(response: Response, game_id: str) -> None:
    """Remove the seat credential set by ``set_seat_cookie`` (same name and path)."""
    response.delete_cookie(
        key=seat_cookie_name(game_id),
        path=f"{server_settings.seat_cookie_path_prefix}/games/{game_id}",
        httponly=True,
        samesite="lax",
        secure=server_settings.SEAT_COOKIE_SECURE,
    )


async def authorize_model(house: HousePolicy, api_key: str, model: str) -> str:
    """Resolve the model a new game runs on and settle who pays, or answer why not: 422
    for a model not on the menu or a player-funded row without a key, 402 when the house
    would have paid but is switched off or has spent today's games (Retry-After says when
    the count resets)."""
    try:
        return await house.authorize(api_key, model)
    except HouseClosed as exc:
        headers = {}
        if exc.reset_at is not None:
            headers["Retry-After"] = exc.reset_at.strftime("%a, %d %b %Y %H:%M:%S GMT")
        raise HTTPException(status_code=402, detail=str(exc), headers=headers) from exc
    except (LookupError, ModelNeedsKey) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


def live_status(session: GameLobby | GameSession, token: str) -> GameStatus:
    """The snapshot of a waiting room or a running game, from the live registry: what
    GET /games/{id} answers, and what the actions that change a room hand back."""
    if token and not session.owns(token):
        raise HTTPException(status_code=403, detail="unknown seat token")
    if isinstance(session, GameLobby):
        return GameStatus(
            game_id=session.game_id,
            state="waiting",
            server_time=datetime.now(timezone.utc).isoformat(),
            players=list(session.players),
            characters=session.picks,
            host=session.host,
            max_seats=MAX_HUMAN_SEATS,
            name=session.name,
            locked=session.locked,
            you_aboard=session.place_of(token) if token else None,
        )
    you = (session.seat_for_token(token) or None) if token else None
    # A pending night turn identifies a private actor just as surely as its prompt.
    # Match the input_request audience: one's own seat until game over, then everyone.
    pending = sorted(seat for seat in session.pending_requests
                     if session.game_over or seat == you)
    return GameStatus(
        game_id=session.game_id,
        state="finished" if session.game_over else "running",
        server_time=datetime.now(timezone.utc).isoformat(),
        human_players=session.human_players,
        you=you,
        awaiting_key=session.awaiting_key,
        pending_input=bool(pending),
        pending_seats=pending,
        deadlines={seat: session.turn_deadlines[seat] for seat in pending
                   if seat in session.turn_deadlines},
        game_over=session.game_over,
        last_seq=session.log[-1].seq if session.log else 0,
        alive_role_counts=session.public_alive_counts,
        cast=[c.character for c in session.cast],
        error=session.error,
    )
