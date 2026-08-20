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

    WW_POSTGRES_DSN: str = ""
    """Postgres for server-owned tables (the replay archive; live-session durability
    later) — the SAME var/database the memory tick uses (ruled 2026-08-20: one knob,
    one container; split into a dedicated var only the day the deploy splits DBs).
    Empty = archiving disabled (games still run; /replays answers 503)."""

    @property
    def cors_allowed_origins(self) -> list[str]:
        return [o.strip() for o in self.CORS_ALLOWED_ORIGINS.split(",") if o.strip()]

    @property
    def replay_database_url(self) -> str:
        """The DSN with SQLAlchemy's async psycopg3 driver marker spliced in — the env
        var stays a plain libpq DSN so the memory tick (raw psycopg) can share it."""
        for prefix in ("postgresql://", "postgres://"):
            if self.WW_POSTGRES_DSN.startswith(prefix):
                return self.WW_POSTGRES_DSN.replace(prefix, "postgresql+psycopg://", 1)
        return self.WW_POSTGRES_DSN


server_settings = ServerSettings()
