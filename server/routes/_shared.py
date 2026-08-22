"""HTTP policies shared by the game-creation and room routers."""

from fastapi import HTTPException, Response

from server.config import server_settings
from server.dependencies import seat_cookie_name
from server.runtime import SUPPORTED_GAME_MODELS

_SEAT_COOKIE_MAX_AGE = 24 * 3600  # comfortably outlives any in-memory game


def set_seat_cookie(response: Response, game_id: str, token: str) -> None:
    """Attach the per-game seat credential using the server's cookie policy.

    EventSource cannot set headers, but browsers attach cookies to SSE requests.
    HttpOnly keeps the credential outside page JavaScript; the path scopes it to
    one game; SameSite=Lax requires the deployed UI and API to remain same-site.
    ``SEAT_COOKIE_SECURE`` stays off for plain-HTTP development and on behind TLS.
    """
    response.set_cookie(
        key=seat_cookie_name(game_id),
        value=token,
        max_age=_SEAT_COOKIE_MAX_AGE,
        path=f"/games/{game_id}",
        httponly=True,
        samesite="lax",
        secure=server_settings.SEAT_COOKIE_SECURE,
    )


def check_byok(api_key: str, model: str) -> None:
    """Apply the BYOK model-selection policy to either game-creation door."""
    if model and not api_key:
        raise HTTPException(status_code=422, detail="model selection requires api_key")
    if model and model not in SUPPORTED_GAME_MODELS:
        raise HTTPException(
            status_code=422,
            detail=(
                "unsupported model; pick from GET /models: "
                f"{sorted(SUPPORTED_GAME_MODELS)}"
            ),
        )
