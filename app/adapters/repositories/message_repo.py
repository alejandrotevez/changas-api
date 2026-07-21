from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities import Mensaje
from app.framework.models import MessageModel


class MessageRepository:
    """SQLAlchemy implementation of the MessageRepository protocol."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_match(self, match_id: str) -> list[Mensaje]:
        stmt = (
            select(MessageModel)
            .where(MessageModel.match_id == match_id)
            .order_by(MessageModel.created_at.asc())
        )
        result = await self._session.execute(stmt)
        rows = result.scalars().all()
        return [self._to_domain(r) for r in rows]

    async def create(self, mensaje: Mensaje) -> Mensaje:
        model = MessageModel(
            id=mensaje.id,
            match_id=mensaje.match_id,
            autor_id=mensaje.autor_id,
            texto=mensaje.texto,
            created_at=mensaje.created_at,
        )
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return self._to_domain(model)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _to_domain(model: MessageModel) -> Mensaje:
        return Mensaje(
            id=model.id,
            match_id=model.match_id,
            autor_id=model.autor_id,
            texto=model.texto,
            created_at=model.created_at,
        )
