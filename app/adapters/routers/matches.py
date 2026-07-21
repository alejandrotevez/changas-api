from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.middleware.auth import get_current_user
from app.adapters.repositories.feed_repo import FeedRepository
from app.adapters.repositories.match_repo import MatchRepository
from app.adapters.repositories.message_repo import MessageRepository
from app.adapters.schemas.feed import (
    ChangadorPerfilResponse,
    ChangaPostResponse,
)
from app.adapters.schemas.matches import MatchResponse
from app.domain.entities import ChangadorPerfil, ChangaPost, Usuario
from app.framework.database import get_db
from app.usecases.matches import MatchUseCase

router = APIRouter(prefix="/matches", tags=["matches"])

# ---------------------------------------------------------------------------
# Dependencies
# ---------------------------------------------------------------------------


def _get_match_use_case(
    db: AsyncSession = Depends(get_db),
) -> MatchUseCase:
    match_repo = MatchRepository(db)
    feed_repo = FeedRepository(db)
    message_repo = MessageRepository(db)
    return MatchUseCase(
        match_repo=match_repo,
        feed_repo=feed_repo,
        message_repo=message_repo,
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("", response_model=list[MatchResponse])
async def list_matches(
    current_user: Usuario = Depends(get_current_user),
    use_case: MatchUseCase = Depends(_get_match_use_case),
) -> list[MatchResponse]:
    items = await use_case.list_user_matches(current_user.id)
    return [
        MatchResponse(
            id=mi.id,
            item=_to_feed_response(mi.item),
            creado_en=mi.creado_en,
            ultimo_mensaje=mi.ultimo_mensaje,
        )
        for mi in items
    ]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _to_feed_response(
    item: ChangaPost | ChangadorPerfil,
) -> ChangaPostResponse | ChangadorPerfilResponse:
    if isinstance(item, ChangaPost):
        return ChangaPostResponse.model_validate(item)
    return ChangadorPerfilResponse.model_validate(item)
