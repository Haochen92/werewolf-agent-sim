"""Keeps the model catalogue the engine reads in step with the database.

The catalogue (which models are on the menu, who pays for them, their settings and prices) is
rows in the database so that ``scripts/model_catalog.py`` can change it without a deploy. The
engine reads it from memory (``Agents/llm_factory/catalog.py``); this job reads the tables at
startup, before any game is recovered, and again every few seconds, so a change reaches the
menu and new turns within about ten seconds. If the database cannot be read, the catalogue
already in memory stays (at startup, the seed in code), and the next pass tries again.
"""

from __future__ import annotations

import asyncio
import logging
import os

from Agents.llm_factory import catalog
from Agents.schemas.model_catalog import Catalog

logger = logging.getLogger(__name__)

REFRESH_SECONDS = 10.0


def catalog_dsn(dsn: str) -> str:
    """The database to read the catalogue from: "" when there is none, or when the process is
    pinned to the seed (WW_MODEL_CATALOG=seed, as the test suite is)."""
    return "" if os.getenv("WW_MODEL_CATALOG", "").lower() == "seed" else dsn


def _changes(old: Catalog | None, new: Catalog) -> str:
    """The models whose rows or prices differ, for the log."""
    if old is None or old.source != new.source:
        return f"loaded from the {new.source}"
    rows = {m.model: m for m in old.models}
    changed = sorted({m.model for m in new.models if rows.get(m.model) != m}
                     | (rows.keys() - {m.model for m in new.models})
                     | {k for k in old.prices.keys() | new.prices.keys()
                        if old.prices.get(k) != new.prices.get(k)})
    return "changed: " + ", ".join(changed)


async def refresh_catalog(dsn: str) -> bool:
    """Read the catalogue and install it if it differs from the one in memory. False when the
    database could not be read (the installed catalogue stays)."""
    try:
        fresh = await asyncio.to_thread(catalog.load_from_database, dsn)
    except Exception as e:  # noqa: BLE001 - keep serving on the catalogue already in memory
        logger.warning("model catalogue: database unreadable (%s); keeping the %s", e,
                       "installed one" if catalog.installed() else "seed")
        if catalog.installed() is None:
            catalog.install(catalog.seed())
        return False
    old = catalog.installed()
    if fresh != old:
        catalog.install(fresh)
        logger.info("model catalogue: %d models (%d on the menu), %d priced; %s",
                    len(fresh.models), len(fresh.menu()), len(fresh.prices), _changes(old, fresh))
    return True


async def run_catalog_refresh(dsn: str, every: float = REFRESH_SECONDS) -> None:
    """Re-read the catalogue every ``every`` seconds until cancelled."""
    while True:
        await asyncio.sleep(every)
        await refresh_catalog(dsn)
