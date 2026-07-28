from __future__ import annotations

import uuid
from datetime import datetime, timezone
from app.domain.entities import Cotizacion
from app.domain.exceptions import Forbidden, InvalidTransition, NotFound
from app.domain.interfaces import (
    CotizacionRepository,
    MatchRepository,
    UserRepository,
)


class CotizacionUseCase:
    """Manage cotizaciones (budget quotes) within a match.

    Lifecycle: PENDIENTE → ACEPTADA | RECHAZADA
    - Changador creates (role: CHANGADOR)
    - Cliente accepts or rejects (role: CLIENTE)
    """

    def __init__(
        self,
        cotizacion_repo: CotizacionRepository,
        match_repo: MatchRepository,
        user_repo: UserRepository,
    ) -> None:
        self._cotizacion_repo = cotizacion_repo
        self._match_repo = match_repo
        self._user_repo = user_repo

    async def create(
        self,
        match_id: str,
        user_id: str,
        monto_estimado: float,
        detalle: str,
        fecha_disponible: str,
    ) -> Cotizacion:
        match = await self._match_repo.get_by_id(match_id)
        if match is None:
            raise NotFound(entity="Match", id=match_id)

        if not self._is_participant(match, user_id):
            raise NotFound(entity="Match", id=match_id)

        user = await self._user_repo.get_by_id(user_id)
        if user is None or user.rol_actual != "CHANGADOR":
            raise Forbidden("Only a changador can create a cotizacion")

        cotizacion = Cotizacion(
            id=uuid.uuid4().hex,
            match_id=match_id,
            monto_estimado=monto_estimado,
            detalle=detalle,
            fecha_disponible=fecha_disponible,
            estado="PENDIENTE",
            creado_por_id=user_id,
            created_at=datetime.now(timezone.utc),
        )
        return await self._cotizacion_repo.create(cotizacion)

    async def accept(
        self,
        match_id: str,
        cotizacion_id: str,
        user_id: str,
    ) -> Cotizacion:
        return await self._transition(
            match_id=match_id,
            cotizacion_id=cotizacion_id,
            user_id=user_id,
            target_state="ACEPTADA",
        )

    async def reject(
        self,
        match_id: str,
        cotizacion_id: str,
        user_id: str,
    ) -> Cotizacion:
        return await self._transition(
            match_id=match_id,
            cotizacion_id=cotizacion_id,
            user_id=user_id,
            target_state="RECHAZADA",
        )

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    async def _transition(
        self,
        match_id: str,
        cotizacion_id: str,
        user_id: str,
        target_state: str,
    ) -> Cotizacion:
        match = await self._match_repo.get_by_id(match_id)
        if match is None:
            raise NotFound(entity="Match", id=match_id)

        if not self._is_participant(match, user_id):
            raise NotFound(entity="Match", id=match_id)

        user = await self._user_repo.get_by_id(user_id)
        if user is None or user.rol_actual != "CLIENTE":
            raise Forbidden(
                "Only the client can accept or reject a cotizacion"
            )

        cotizacion = await self._cotizacion_repo.get_by_id(cotizacion_id)
        if cotizacion is None:
            raise NotFound(entity="Cotizacion", id=cotizacion_id)

        if cotizacion.match_id != match_id:
            raise NotFound(entity="Cotizacion", id=cotizacion_id)

        if cotizacion.estado != "PENDIENTE":
            raise InvalidTransition(
                entity="Cotizacion",
                from_state=cotizacion.estado,
                to_state=target_state,
            )

        updated = Cotizacion(
            id=cotizacion.id,
            match_id=cotizacion.match_id,
            monto_estimado=cotizacion.monto_estimado,
            detalle=cotizacion.detalle,
            fecha_disponible=cotizacion.fecha_disponible,
            estado=target_state,
            creado_por_id=cotizacion.creado_por_id,
            created_at=cotizacion.created_at,
        )
        return await self._cotizacion_repo.update(updated)

    @staticmethod
    def _is_participant(match, user_id: str) -> bool:
        return match.user_a_id == user_id or match.user_b_id == user_id
