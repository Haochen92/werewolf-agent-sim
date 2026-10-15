"""Process health and public model-discovery endpoints."""

from fastapi import APIRouter

from server.dependencies import GraphRuntimeDep, House, ReplayServiceDep
from server.game.model_catalog import menu_models
from server.schemas.requests import HouseFunding, ModelRow, ModelsMenu

from ._shared import memory_unavailable

router = APIRouter(tags=["system"])


@router.get("/health", summary="Liveness probe")
async def health_check() -> dict:
    return {"status": "healthy"}


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
        memory_available=(await memory_unavailable(runtime)) is None,
    )
