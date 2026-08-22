"""Public read-only endpoints for completed-game replays."""

from fastapi import APIRouter, HTTPException

from server.dependencies import ReplayServiceDep
from server.replay_service import (
    IncompleteReplay,
    ReplayArchiveNotConfigured,
    ReplayNotFound,
)
from server.schemas.replays import ReplayBase, ReplayGame

router = APIRouter(tags=["replays"])


@router.get(
    "/replays",
    response_model=list[ReplayBase],
    summary="Browse finished games (newest first)",
)
async def list_replays(
    service: ReplayServiceDep,
    limit: int = 50,
    offset: int = 0,
) -> list[ReplayBase]:
    try:
        return await service.list_replays(limit=limit, offset=offset)
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
