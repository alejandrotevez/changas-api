from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities import Usuario
from app.framework.models import UserModel


class UserRepository:
    """SQLAlchemy implementation of the UserRepository protocol."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_email(self, email: str) -> Optional[Usuario]:
        stmt = select(UserModel).where(UserModel.email == email)
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        return self._to_domain(row) if row else None

    async def get_by_google_id(self, google_id: str) -> Optional[Usuario]:
        stmt = select(UserModel).where(UserModel.google_id == google_id)
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        return self._to_domain(row) if row else None

    async def get_by_id(self, user_id: str) -> Optional[Usuario]:
        row = await self._session.get(UserModel, user_id)
        return self._to_domain(row) if row else None

    async def create(self, user: Usuario) -> Usuario:
        user_id = user.id or uuid.uuid4().hex
        model = UserModel(
            id=user_id,
            nombre=user.nombre,
            email=user.email,
            password_hash=user.password_hash,
            google_id=user.google_id,
            rol_actual=user.rol_actual,
            tags=_to_json(user.tags),
            created_at=user.created_at or datetime.now(timezone.utc),
        )
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return self._to_domain(model)

    async def update(self, user: Usuario) -> Usuario:
        model = await self._session.get(UserModel, user.id)
        if model is None:
            raise ValueError(f"Usuario with id '{user.id}' not found")

        model.nombre = user.nombre
        model.email = user.email
        model.password_hash = user.password_hash
        model.google_id = user.google_id
        model.rol_actual = user.rol_actual
        model.tags = _to_json(user.tags)

        await self._session.flush()
        await self._session.refresh(model)
        return self._to_domain(model)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _to_domain(model: UserModel) -> Usuario:
        return Usuario(
            id=model.id,
            nombre=model.nombre,
            email=model.email,
            password_hash=model.password_hash,
            google_id=model.google_id,
            rol_actual=model.rol_actual,
            tags=_parse_json(model.tags),
            created_at=model.created_at,
        )


def _to_json(value: list[str]) -> str:
    return json.dumps(value, ensure_ascii=False)


def _parse_json(value: str) -> list[str]:
    try:
        parsed = json.loads(value)
        return parsed if isinstance(parsed, list) else []
    except (json.JSONDecodeError, TypeError):
        return []
