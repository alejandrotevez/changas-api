from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.middleware.auth import get_current_user
from app.adapters.repositories.match_repo import MatchRepository
from app.adapters.repositories.message_repo import MessageRepository
from app.adapters.schemas.chat import MessageResponse, SendMessageRequest
from app.domain.entities import Usuario
from app.domain.exceptions import NotFound
from app.framework.database import get_db
from app.usecases.chat import ChatUseCase

router = APIRouter(prefix="/matches", tags=["chat"])

# ---------------------------------------------------------------------------
# Dependencies
# ---------------------------------------------------------------------------


def _get_chat_use_case(
    db: AsyncSession = Depends(get_db),
) -> ChatUseCase:
    match_repo = MatchRepository(db)
    message_repo = MessageRepository(db)
    return ChatUseCase(
        match_repo=match_repo,
        message_repo=message_repo,
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get(
    "/{match_id}/messages",
    response_model=list[MessageResponse],
)
async def get_messages(
    match_id: str,
    current_user: Usuario = Depends(get_current_user),
    use_case: ChatUseCase = Depends(_get_chat_use_case),
) -> list[MessageResponse]:
    try:
        messages = await use_case.get_messages(
            match_id=match_id,
            user_id=current_user.id,
        )
    except NotFound as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    return [
        MessageResponse(
            id=m.id,
            autor_id=m.autor_id,
            texto=m.texto,
            enviado_en=m.created_at,
        )
        for m in messages
    ]


@router.post(
    "/{match_id}/messages",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
)
async def send_message(
    match_id: str,
    body: SendMessageRequest,
    current_user: Usuario = Depends(get_current_user),
    use_case: ChatUseCase = Depends(_get_chat_use_case),
) -> MessageResponse:
    try:
        mensaje = await use_case.send_message(
            match_id=match_id,
            user_id=current_user.id,
            texto=body.texto,
        )
    except NotFound as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    return MessageResponse(
        id=mensaje.id,
        autor_id=mensaje.autor_id,
        texto=mensaje.texto,
        enviado_en=mensaje.created_at,
    )
