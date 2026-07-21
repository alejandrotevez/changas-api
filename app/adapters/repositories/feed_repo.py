from __future__ import annotations

import json
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities import ChangadorPerfil, ChangaPost
from app.framework.models import ChangadorPerfilModel, ChangaPostModel


class FeedRepository:
    """SQLAlchemy implementation of the FeedRepository protocol."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_changa_posts(
        self,
        exclude_swiped_ids: list[str],
        limit: int = 20,
        offset: int = 0,
    ) -> list[ChangaPost]:
        stmt = select(ChangaPostModel).order_by(ChangaPostModel.created_at.desc())

        if exclude_swiped_ids:
            stmt = stmt.where(ChangaPostModel.id.notin_(exclude_swiped_ids))

        stmt = stmt.offset(offset).limit(limit)
        result = await self._session.execute(stmt)
        rows = result.scalars().all()
        return [self._changa_to_domain(r) for r in rows]

    async def get_changador_perfiles(
        self,
        exclude_swiped_ids: list[str],
        limit: int = 20,
        offset: int = 0,
    ) -> list[ChangadorPerfil]:
        stmt = select(ChangadorPerfilModel).order_by(
            ChangadorPerfilModel.created_at.desc()
        )

        if exclude_swiped_ids:
            stmt = stmt.where(ChangadorPerfilModel.id.notin_(exclude_swiped_ids))

        stmt = stmt.offset(offset).limit(limit)
        result = await self._session.execute(stmt)
        rows = result.scalars().all()
        return [self._perfil_to_domain(r) for r in rows]

    async def get_item_owner_id(self, item_id: str) -> Optional[str]:
        # Check ChangaPost first
        post = await self._session.get(ChangaPostModel, item_id)
        if post is not None:
            return post.user_id

        # Then check ChangadorPerfil
        perfil = await self._session.get(ChangadorPerfilModel, item_id)
        if perfil is not None:
            return perfil.user_id

        return None

    async def get_changa_post_by_user_id(
        self, user_id: str
    ) -> Optional[ChangaPost]:
        stmt = select(ChangaPostModel).where(ChangaPostModel.user_id == user_id)
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        return self._changa_to_domain(row) if row else None

    async def get_changador_perfil_by_user_id(
        self, user_id: str
    ) -> Optional[ChangadorPerfil]:
        stmt = select(ChangadorPerfilModel).where(
            ChangadorPerfilModel.user_id == user_id
        )
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        return self._perfil_to_domain(row) if row else None

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _changa_to_domain(model: ChangaPostModel) -> ChangaPost:
        return ChangaPost(
            id=model.id,
            titulo=model.titulo,
            descripcion_corta=model.descripcion_corta,
            fotos=_parse_json_list(model.fotos),
            tags=_parse_json_list(model.tags),
            barrio=model.barrio,
            user_id=model.user_id,
            created_at=model.created_at,
        )

    @staticmethod
    def _perfil_to_domain(model: ChangadorPerfilModel) -> ChangadorPerfil:
        return ChangadorPerfil(
            id=model.id,
            nombre=model.nombre,
            fotos_trabajos=_parse_json_list(model.fotos_trabajos),
            especialidades=_parse_json_list(model.especialidades),
            user_id=model.user_id,
            created_at=model.created_at,
        )


def _parse_json_list(value: str) -> list[str]:
    try:
        parsed = json.loads(value)
        return parsed if isinstance(parsed, list) else []
    except (json.JSONDecodeError, TypeError):
        return []
