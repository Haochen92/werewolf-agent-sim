"""HTTP policies shared by the game-creation and room routers."""

from fastapi import HTTPException, Response

from server.config import server_settings
from server.dependencies import seat_cookie_name
from server.house import HouseClosed, HousePolicy, ModelNeedsKey

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
