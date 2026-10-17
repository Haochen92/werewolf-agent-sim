"""Crash reports to Sentry (owner, 2026-10-17). A game that dies, or a request that fails, is
sent with its stack trace and the game it belongs to, so a crash in a live game is found
without reading the container's log. Off unless SENTRY_DSN is set (tests, local runs).

Nothing private leaves the server: no request bodies, headers, cookies or query strings (a
POST /games body holds the player's API key), no local variables (a frame's locals can hold it
too), no model inputs or outputs, and the game's own key is scrubbed from what is sent. Ordinary log lines stay breadcrumbs: only real exceptions
become reports, so the routine ERROR lines (a technical pass, a random fallback) do not use up
the plan's monthly quota."""

from __future__ import annotations

import logging

import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.integrations.starlette import StarletteIntegration

from server.config import server_settings

logger = logging.getLogger(__name__)

# Field names whose values never leave, wherever they appear in a report (the SDK's own
# scrubber is off once data_collection is given, so before_send does it).
_PRIVATE = {"api_key", "seat_token", "host_key", "x_admin_token", "x-admin-token"}


def init_error_reporting() -> bool:
    """Start reporting if a DSN is configured; whether it started."""
    if not server_settings.SENTRY_DSN:
        return False
    off = {"mode": "off"}
    sentry_sdk.init(
        dsn=server_settings.SENTRY_DSN,
        environment=server_settings.SENTRY_ENVIRONMENT,
        # every category of collected data named and off: the SDK's own default collects
        data_collection={
            "user_info": False, "cookies": off, "http_headers": {"request": off},
            "http_bodies": [], "url_query_params": off, "stack_frame_variables": False,
            "gen_ai": {"inputs": False, "outputs": False},
        },
        max_request_body_size="never",
        traces_sample_rate=0,
        before_send=lambda event, _hint: _drop_private(event),
        # Only the web framework's: the auto-enabled model-provider integrations (Anthropic,
        # OpenAI, LangChain are installed) report every failed call, and a game's 401s and 429s
        # are handled by the turn itself.
        auto_enabling_integrations=False,
        integrations=[StarletteIntegration(), FastApiIntegration(),
                      LoggingIntegration(event_level=None)],
    )
    logger.info("error reporting on (environment=%s)", server_settings.SENTRY_ENVIRONMENT)
    return True


def report_game_failure(exc: BaseException, *, game_id: str, model: str, byok: bool,
                        secret: str = "", after_game_over: bool = False) -> None:
    """Send one game's failure, tagged with the game, with ``secret`` (its key) scrubbed."""
    if not sentry_sdk.get_client().is_active():
        return
    with sentry_sdk.new_scope() as scope:
        scope.set_tag("game_id", game_id)
        scope.set_tag("model", model or "server-default")
        scope.set_tag("byok", "yes" if byok else "no")
        scope.set_tag("stage", "post_game" if after_game_over else "in_game")
        if secret:
            scope.add_event_processor(lambda event, _hint: _scrub(event, secret))
        sentry_sdk.capture_exception(exc)


def _drop_private(value):
    """``value`` with the value of every private field replaced, at any depth."""
    if isinstance(value, dict):
        return {k: "[Filtered]" if str(k).lower() in _PRIVATE else _drop_private(v)
                for k, v in value.items()}
    if isinstance(value, list):
        return [_drop_private(v) for v in value]
    return value


def _scrub(value, secret: str):
    """``value`` with every occurrence of ``secret`` in its strings replaced."""
    if isinstance(value, str):
        return value.replace(secret, "***")
    if isinstance(value, dict):
        return {k: _scrub(v, secret) for k, v in value.items()}
    if isinstance(value, list):
        return [_scrub(v, secret) for v in value]
    return value
