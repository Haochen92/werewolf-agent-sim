"""Process health and public model-discovery endpoints."""

from fastapi import APIRouter

from server.model_catalog import SUPPORTED_GAME_MODELS
from server.schemas.requests import ModelRow, ModelsMenu

router = APIRouter(tags=["system"])


@router.get("/health", summary="Liveness probe")
async def health_check() -> dict:
    return {"status": "healthy"}


@router.get(
    "/models",
    response_model=ModelsMenu,
    summary="The served-game model menu (tested models only)",
)
async def supported_models() -> ModelsMenu:
    """Return tested game models and their compatible rescue models."""
    return ModelsMenu(
        models=[
            ModelRow(model=model, label=row.display_name, rescue_model=row.rescue_model)
            for model, row in SUPPORTED_GAME_MODELS.items()
        ]
    )
