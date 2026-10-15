"""Operator endpoints: read and change the live knobs without a restart.

Guarded by one shared secret, ADMIN_TOKEN, sent as the X-Admin-Token header. With no
token configured the endpoints answer 404, so an unconfigured deploy exposes nothing.
"""

from typing import Annotated

from fastapi import APIRouter, Header, HTTPException

from server.config import server_settings
from server.dependencies import House
from server.schemas.requests import HouseUpdate, HouseView

router = APIRouter(prefix="/admin", tags=["admin"])


def _require_admin(x_admin_token: Annotated[str, Header()] = "") -> None:
    if not server_settings.ADMIN_TOKEN:
        raise HTTPException(status_code=404, detail="admin endpoints are disabled")
    if x_admin_token != server_settings.ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="bad admin token")


@router.get("/house", response_model=HouseView, summary="The house's purse as of now")
async def read_house(house: House,
                     x_admin_token: Annotated[str, Header()] = "") -> HouseView:
    _require_admin(x_admin_token)
    return _view(await house.status())


@router.put("/house", response_model=HouseView, summary="Change the house's knobs, live")
async def update_house(body: HouseUpdate, house: House,
                       x_admin_token: Annotated[str, Header()] = "") -> HouseView:
    _require_admin(x_admin_token)
    try:
        status = await house.update(enabled=body.enabled, default_model=body.default_model,
                                    games_per_day=body.games_per_day)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return _view(status)


def _view(status) -> HouseView:
    return HouseView(enabled=status.enabled, default_model=status.default_model,
                     games_per_day=status.games_per_day, used_today=status.used_today,
                     remaining=status.remaining, reset_at=status.reset_at.isoformat())
