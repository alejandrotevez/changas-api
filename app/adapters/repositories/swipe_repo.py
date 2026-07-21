from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities import Swipe
from app.framework.models import (
    ChangadorPerfilModel,
    ChangaPostModel,
    SwipeModel,
)


class SwipeRepository:
    """SQLAlchemy implementation of the SwipeRepository protocol."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, swipe: Swipe) -> Swipe:
        model = SwipeModel(
            id=swipe.id,
            user_id=swipe.user_id,
            item_id=swipe.item_id,
            liked=swipe.liked,
            created_at=swipe.created_at,
        )
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return self._to_domain(model)

    async def exists(self, user_id: str, item_id: str) -> bool:
        stmt = select(SwipeModel).where(
            SwipeModel.user_id == user_id,
            SwipeModel.item_id == item_id,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def get_by_user_and_item(
        self, user_id: str, item_id: str
    ) -> Optional[Swipe]:
        stmt = select(SwipeModel).where(
            SwipeModel.user_id == user_id,
            SwipeModel.item_id == item_id,
        )
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        return self._to_domain(row) if row else None

    async def get_mutual_like(
        self, user_id: str, item_owner_id: str
    ) -> Optional[Swipe]:
        """Check if item_owner_id has liked any item owned by user_id."""
        # Collect item IDs owned by user_id
        changa_stmt = select(ChangaPostModel.id).where(
            ChangaPostModel.user_id == user_id
        )
        changa_result = await self._session.execute(changa_stmt)
        changa_ids = [row[0] for row in changa_result.all()]

        perfil_stmt = select(ChangadorPerfilModel.id).where(
            ChangadorPerfilModel.user_id == user_id
        )
        perfil_result = await self._session.execute(perfil_stmt)
        perfil_ids = [row[0] for row in perfil_result.all()]

        all_item_ids = changa_ids + perfil_ids
        if not all_item_ids:
            return None

        swipe_stmt = (
            select(SwipeModel)
            .where(
                SwipeModel.user_id == item_owner_id,
                SwipeModel.liked == True,  # noqa: E712
                SwipeModel.item_id.in_(all_item_ids),
            )
            .limit(1)
        )
        result = await self._session.execute(swipe_stmt)
        row = result.scalar_one_or_none()
        return self._to_domain(row) if row else None

    async def get_swiped_item_ids(self, user_id: str) -> list[str]:
        stmt = select(SwipeModel.item_id).where(SwipeModel.user_id == user_id)
        result = await self._session.execute(stmt)
        return [row[0] for row in result.all()]

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _to_domain(model: SwipeModel) -> Swipe:
        return Swipe(
            id=model.id,
            user_id=model.user_id,
            item_id=model.item_id,
            liked=model.liked,
            created_at=model.created_at,
        )
