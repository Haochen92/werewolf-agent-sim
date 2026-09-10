"""HTTP policies shared by the game-creation and room routers."""

from fastapi import HTTPException, Response

from server.config import server_settings
from server.dependencies import seat_cookie_name
from server.model_catalog import SUPPORTED_GAME_MODELS

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


def check_model_access(api_key: str, model: str) -> None:
    """Validate a model selection against house-funded and BYOK-only policy."""
    if not model:
        return
    row = SUPPORTED_GAME_MODELS.get(model)
    if row is None:
        raise HTTPException(
            status_code=422,
            detail=(
                "unsupported model; pick from GET /models: "
                f"{sorted(SUPPORTED_GAME_MODELS)}"
            ),
        )
    if not api_key and not row.house_funded:
        raise HTTPException(status_code=422, detail="model selection requires api_key")
