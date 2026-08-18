"""Server deployment settings — the knobs of the HTTP surface, not the game.

Game configuration stays on ``RunConfig`` (per game, minted per POST /games); this
module holds only process-level deployment concerns, read once at import from the
environment / ``.env``.
"""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class ServerSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    CORS_ALLOWED_ORIGINS: str = "http://localhost:3000"
    """Comma-separated explicit origins for the browser frontend. Explicit because
    ``allow_origins=["*"]`` combined with credentials is rejected by browsers; stored
    as a plain string so a comma-separated env value parses (pydantic-settings
    JSON-decodes list-typed fields)."""

    @property
    def cors_allowed_origins(self) -> list[str]:
        return [o.strip() for o in self.CORS_ALLOWED_ORIGINS.split(",") if o.strip()]


server_settings = ServerSettings()
