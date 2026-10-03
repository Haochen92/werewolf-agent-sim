"""The puppet catalogue: what a player may pick to stand as."""

from fastapi import APIRouter

from server.game.cast import CATALOGUE
from server.schemas.requests import CharacterCard

router = APIRouter(tags=["characters"])


@router.get(
    "/characters",
    response_model=list[CharacterCard],
    summary="The puppets a player may stand as (public)",
)
async def list_characters() -> list[CharacterCard]:
    """Every character the catalogue has issued, retired ones last. The ids are what a
    pick names and what a game's cast is recorded in."""
    cards = [CharacterCard(id=c.id, display_name=c.display_name, retired=c.retired)
             for c in CATALOGUE]
    return sorted(cards, key=lambda c: c.retired)
