from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities import Cotizacion
from app.framework.models import CotizacionModel


class CotizacionRepository:
    """SQLAlchemy implementation of the CotizacionRepository protocol."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_match(self, match_id: str) -> list[Cotizacion]:
        stmt = (
            select(CotizacionModel)
            .where(CotizacionModel.match_id == match_id)
            .order_by(CotizacionModel.created_at.desc())
        )
        result = await self._session.execute(stmt)
        rows = result.scalars().all()
        return [self._to_domain(r) for r in rows]

    async def get_by_id(self, cotizacion_id: str) -> Optional[Cotizacion]:
        row = await self._session.get(CotizacionModel, cotizacion_id)
        return self._to_domain(row) if row else None

    async def create(self, cotizacion: Cotizacion) -> Cotizacion:
        model = CotizacionModel(
            id=cotizacion.id,
            match_id=cotizacion.match_id,
            monto_estimado=cotizacion.monto_estimado,
            detalle=cotizacion.detalle,
            fecha_disponible=cotizacion.fecha_disponible,
            estado=cotizacion.estado,
            creado_por_id=cotizacion.creado_por_id,
            created_at=cotizacion.created_at,
        )
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return self._to_domain(model)

    async def update(self, cotizacion: Cotizacion) -> Cotizacion:
        model = await self._session.get(CotizacionModel, cotizacion.id)
        if model is None:
            raise ValueError(f"Cotizacion with id '{cotizacion.id}' not found")

        model.monto_estimado = cotizacion.monto_estimado
        model.detalle = cotizacion.detalle
        model.fecha_disponible = cotizacion.fecha_disponible
        model.estado = cotizacion.estado
        model.creado_por_id = cotizacion.creado_por_id

        await self._session.flush()
        await self._session.refresh(model)
        return self._to_domain(model)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _to_domain(model: CotizacionModel) -> Cotizacion:
        return Cotizacion(
            id=model.id,
            match_id=model.match_id,
            monto_estimado=model.monto_estimado,
            detalle=model.detalle,
            fecha_disponible=model.fecha_disponible,
            estado=model.estado,
            creado_por_id=model.creado_por_id,
            created_at=model.created_at,
        )
