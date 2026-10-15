"""Read and write the settings table: the knobs an operator changes while the server runs."""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert

from server.database_models.settings import SettingRow
from server.db import Database

logger = logging.getLogger(__name__)


class SettingsRepository:
    def __init__(self, database: Database) -> None:
        self._database = database

    @property
    def configured(self) -> bool:
        return self._database.configured

    async def load(self) -> dict[str, Any]:
        """Every stored setting, keyed by name. Empty when storage is off."""
        if not self._database.configured:
            return {}
        async with self._database.session() as session:
            rows = (await session.execute(select(SettingRow))).scalars().all()
        return {row.key: row.value for row in rows}

    async def save(self, key: str, value: Any) -> None:
        """Insert or replace one setting. A no-op with a warning when storage is off, so
        a knob still takes effect in memory until the next restart."""
        if not self._database.configured:
            logger.warning("setting %s=%r not persisted: WW_POSTGRES_DSN is not set", key, value)
            return
        stmt = insert(SettingRow).values(key=key, value=value)
        stmt = stmt.on_conflict_do_update(
            index_elements=["key"], set_={"value": value, "updated_at": func.now()})
        async with self._database.session() as session:
            await session.execute(stmt)
            await session.commit()
