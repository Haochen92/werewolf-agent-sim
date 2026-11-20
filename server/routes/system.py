"""Process health and public model-discovery endpoints."""

import asyncio
import logging

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from sqlalchemy import text

from server.dependencies import GraphRuntimeDep, House, ReplayServiceDep
from server.game.model_catalog import backup_models, menu_models
from server.schemas.requests import HouseFunding, ModelRow, ModelsMenu

from ._shared import memory_unavailable

router = APIRouter(tags=["system"])
logger = logging.getLogger(__name__)

_DATABASE_CHECK_TIMEOUT_S = 2.0


# 200 when the server can do its work, 503 when its database does not answer within two seconds.
# A game cannot be saved, recovered or replayed without the database, so a server that cannot
# reach it is reported unhealthy. The trace store is left out on purpose: games play without it,
# and its outage must not mark the game server down. "database" is "off" when the server runs
# with no database configured (local development). These notes are comments, not a docstring,
# and the summary is unchanged, so the saved API description and the browser's types stay as
# they are.
@router.get("/health", summary="Liveness probe")
async def health_check(request: Request) -> dict:
    database = request.app.state.resources.database
    if not database.configured:
        return {"status": "healthy", "database": "off"}
    try:
        async with asyncio.timeout(_DATABASE_CHECK_TIMEOUT_S):
            async with database.session() as session:
                await session.execute(text("SELECT 1"))
    except Exception as exc:
        logger.error("health: the database did not answer: %r", exc)
        return JSONResponse(status_code=503,
                            content={"status": "unhealthy", "database": "unreachable"})
    return {"status": "healthy", "database": "ok"}


@router.get(
    "/models",
    response_model=ModelsMenu,
    summary="The served-game model menu (tested models only), and what the house will pay for",
)
async def supported_models(house: House, replays: ReplayServiceDep,
                           runtime: GraphRuntimeDep) -> ModelsMenu:
    """Every tested model with its rescue, whether the house pays for it, which one is the
    default right now, and what a finished game on it has cost on average (memory off and
    memory on apart); plus the house's
    purse for today, so the client can say "house pays, 3 left" or "your key needed" before
    the player submits; and whether a new game may switch memory on."""
    status = await house.status()
    costs = await replays.average_costs()
    return ModelsMenu(
        models=[
            ModelRow(model=row.model, label=row.display_name, rescue_model=row.rescue_model,
                     house_funded=row.house_funded, is_default=(row.model == status.default_model),
                     needs_key=(not row.house_funded or not status.enabled
                                or status.remaining <= 0),
                     avg_cost_usd=costs.get((row.model, False), (None, 0))[0],
                     priced_games=costs.get((row.model, False), (None, 0))[1],
                     avg_cost_memory_usd=costs.get((row.model, True), (None, 0))[0],
                     priced_memory_games=costs.get((row.model, True), (None, 0))[1])
            for row in menu_models()
        ],
        house=HouseFunding(enabled=status.enabled, games_per_day=status.games_per_day,
                           remaining=status.remaining, reset_at=status.reset_at.isoformat()),
        backups=backup_models(),
        memory_available=(await memory_unavailable(runtime)) is None,
    )
