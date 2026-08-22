"""Process health and public model-discovery endpoints."""

from fastapi import APIRouter

from server.runtime import SUPPORTED_GAME_MODELS
from server.schemas.requests import ModelRow, ModelsMenu

router = APIRouter(tags=["system"])


@router.get("/health", summary="Liveness probe")
async def health_check() -> dict:
    return {"status": "healthy"}


@router.get(
    "/models",
    response_model=ModelsMenu,
    summary="The BYOK selection menu (tested game models only)",
)
async def supported_models() -> ModelsMenu:
    """Return tested game models and their same-credential rescue models."""
    return ModelsMenu(
        models=[
            ModelRow(model=model, label=row.label, rescue_model=row.rescue)
            for model, row in SUPPORTED_GAME_MODELS.items()
        ]
    )
