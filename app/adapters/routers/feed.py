from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.middleware.auth import get_current_user
from app.adapters.repositories.feed_repo import FeedRepository
from app.adapters.repositories.swipe_repo import SwipeRepository
from app.adapters.schemas.feed import (
    ChangadorPerfilResponse,
    ChangaPostResponse,
    FeedItemResponse,
)
from app.adapters.schemas.swipe import SwipeRequest, SwipeResponse
from app.domain.entities import ChangadorPerfil, ChangaPost, Usuario
from app.domain.exceptions import DuplicateSwipe, Forbidden, NotFound
from app.framework.database import get_db
from app.usecases.feed import FeedUseCase
from app.usecases.swipe import SwipeResult, SwipeUseCase

router = APIRouter(prefix="/feed", tags=["feed"])

# ---------------------------------------------------------------------------
# Dependencies
# ---------------------------------------------------------------------------


def _get_feed_use_case(db: AsyncSession = Depends(get_db)) -> FeedUseCase:
    feed_repo = FeedRepository(db)
    swipe_repo = SwipeRepository(db)
    return FeedUseCase(feed_repo=feed_repo, swipe_repo=swipe_repo)


def _get_swipe_use_case(db: AsyncSession = Depends(get_db)) -> SwipeUseCase:
    from app.adapters.repositories.match_repo import MatchRepository

    swipe_repo = SwipeRepository(db)
    feed_repo = FeedRepository(db)
    match_repo = MatchRepository(db)
    return SwipeUseCase(
        swipe_repo=swipe_repo,
        match_repo=match_repo,
        feed_repo=feed_repo,
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("", response_model=list[FeedItemResponse])
async def get_feed(
    rol: Optional[str] = Query(default=None),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    current_user: Usuario = Depends(get_current_user),
    use_case: FeedUseCase = Depends(_get_feed_use_case),
) -> list[FeedItemResponse]:
    resolved_rol = rol or current_user.rol_actual
    items = await use_case.execute(
        user_id=current_user.id,
        rol=resolved_rol,
        page=page,
        limit=limit,
    )
    return [_to_feed_response(item) for item in items]


@router.post(
    "/swipe",
    response_model=SwipeResponse,
    status_code=status.HTTP_200_OK,
)
async def swipe_item(
    body: SwipeRequest,
    current_user: Usuario = Depends(get_current_user),
    use_case: SwipeUseCase = Depends(_get_swipe_use_case),
) -> SwipeResponse:
    try:
        result: SwipeResult = await use_case.execute(
            user_id=current_user.id,
            item_id=body.item_id,
            liked=body.liked,
        )
    except NotFound as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except DuplicateSwipe as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    except Forbidden as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    return SwipeResponse(
        es_match=result.es_match,
        match_id=result.match_id,
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _to_feed_response(
    item: ChangaPost | ChangadorPerfil,
) -> ChangaPostResponse | ChangadorPerfilResponse:
    if isinstance(item, ChangaPost):
        return ChangaPostResponse.model_validate(item)
    return ChangadorPerfilResponse.model_validate(item)
