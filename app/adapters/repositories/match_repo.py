from __future__ import annotations

from typing import Optional

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities import Match
from app.framework.models import MatchModel


class MatchRepository:
    """SQLAlchemy implementation of the MatchRepository protocol."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_user(self, user_id: str) -> list[Match]:
        stmt = select(MatchModel).where(
            (MatchModel.user_a_id == user_id) | (MatchModel.user_b_id == user_id)
        )
        result = await self._session.execute(stmt)
        rows = result.scalars().all()
        return [self._to_domain(r) for r in rows]

    async def get_by_id(self, match_id: str) -> Optional[Match]:
        row = await self._session.get(MatchModel, match_id)
        return self._to_domain(row) if row else None

    async def exists(self, user_a_id: str, user_b_id: str) -> bool:
        stmt = select(MatchModel).where(
            and_(
                (
                    (MatchModel.user_a_id == user_a_id)
                    & (MatchModel.user_b_id == user_b_id)
                )
                | (
                    (MatchModel.user_a_id == user_b_id)
                    & (MatchModel.user_b_id == user_a_id)
                )
            )
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def create(self, match: Match) -> Match:
        model = MatchModel(
            id=match.id,
            user_a_id=match.user_a_id,
            user_b_id=match.user_b_id,
            created_at=match.created_at,
        )
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return self._to_domain(model)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _to_domain(model: MatchModel) -> Match:
        return Match(
            id=model.id,
            user_a_id=model.user_a_id,
            user_b_id=model.user_b_id,
            created_at=model.created_at,
        )
