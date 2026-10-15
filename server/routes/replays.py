"""Public read-only endpoints for completed-game replays."""

from fastapi import APIRouter, HTTPException, Response

from server.dependencies import ReplayServiceDep
from server.storage.replay_service import (
    IncompleteReplay,
    ReplayArchiveNotConfigured,
    ReplayNotFound,
)
from server.schemas.replays import ReplayBase, ReplayGame

router = APIRouter(tags=["replays"])

TOTAL_COUNT_HEADER = "X-Total-Count"
"""The response header that carries the replay list's total. The browser may only read it
from another origin because the app's CORS setup names it as exposed."""


@router.get(
    "/replays",
    response_model=list[ReplayBase],
    summary="Browse finished games (newest first)",
    responses={200: {"headers": {TOTAL_COUNT_HEADER: {
        "description": "How many finished games there are in all, across every page.",
        "schema": {"type": "integer"},
    }}}},
)
async def list_replays(
    service: ReplayServiceDep,
    response: Response,
    limit: int = 50,
    offset: int = 0,
) -> list[ReplayBase]:
    """One page of finished games. The body stays a plain list; the total number of
    finished games, for a footer like "212 games", rides in the X-Total-Count header."""
    try:
        page = await service.list_replays(limit=limit, offset=offset)
        response.headers[TOTAL_COUNT_HEADER] = str(await service.count_replays())
        return page
    except ReplayArchiveNotConfigured as exc:
        raise HTTPException(
            status_code=503, detail="replay archive not configured"
        ) from exc


@router.get(
    "/replays/{game_id}",
    response_model=ReplayGame,
    summary="One finished game's full event log",
)
async def get_replay(game_id: str, service: ReplayServiceDep) -> ReplayGame:
    try:
        return await service.get_replay(game_id)
    except ReplayArchiveNotConfigured as exc:
        raise HTTPException(
            status_code=503, detail="replay archive not configured"
        ) from exc
    except ReplayNotFound as exc:
        raise HTTPException(status_code=404, detail="unknown replay") from exc
    except IncompleteReplay as exc:
        raise HTTPException(
            status_code=500, detail="incomplete replay event log"
        ) from exc
