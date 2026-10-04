"""Process health and public model-discovery endpoints."""

from fastapi import APIRouter

from server.dependencies import House, ReplayServiceDep
from server.game.model_catalog import SUPPORTED_GAME_MODELS
from server.schemas.requests import HouseFunding, ModelRow, ModelsMenu

router = APIRouter(tags=["system"])


@router.get("/health", summary="Liveness probe")
async def health_check() -> dict:
    return {"status": "healthy"}


@router.get(
    "/models",
    response_model=ModelsMenu,
    summary="The served-game model menu (tested models only), and what the house will pay for",
)
async def supported_models(house: House, replays: ReplayServiceDep) -> ModelsMenu:
    """Every tested model with its rescue, whether the house pays for it, which one is the
    default right now, and what a finished game on it has cost on average; plus the house's
    purse for today, so the client can say "house pays, 3 left" or "your key needed" before
    the player submits."""
    status = await house.status()
    costs = await replays.average_costs()
    return ModelsMenu(
        models=[
            ModelRow(model=model, label=row.display_name, rescue_model=row.rescue_model,
                     house_funded=row.house_funded, is_default=(model == status.default_model),
                     needs_key=(not row.house_funded or not status.enabled
                                or status.remaining <= 0),
                     avg_cost_usd=costs.get(model, (None, 0))[0],
                     priced_games=costs.get(model, (None, 0))[1])
            for model, row in SUPPORTED_GAME_MODELS.items()
        ],
        house=HouseFunding(enabled=status.enabled, games_per_day=status.games_per_day,
                           remaining=status.remaining, reset_at=status.reset_at.isoformat()),
    )
