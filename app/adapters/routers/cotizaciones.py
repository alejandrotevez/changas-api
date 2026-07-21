from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.middleware.auth import get_current_user
from app.adapters.repositories.cotizacion_repo import CotizacionRepository
from app.adapters.repositories.match_repo import MatchRepository
from app.adapters.repositories.user_repo import UserRepository
from app.adapters.schemas.cotizaciones import (
    CotizacionRequest,
    CotizacionResponse,
)
from app.domain.entities import Usuario
from app.domain.exceptions import Forbidden, InvalidTransition, NotFound
from app.framework.database import get_db
from app.usecases.cotizaciones import CotizacionUseCase

router = APIRouter(prefix="/matches", tags=["cotizaciones"])

# ---------------------------------------------------------------------------
# Dependencies
# ---------------------------------------------------------------------------


def _get_cotizacion_use_case(
    db: AsyncSession = Depends(get_db),
) -> CotizacionUseCase:
    cotizacion_repo = CotizacionRepository(db)
    match_repo = MatchRepository(db)
    user_repo = UserRepository(db)
    return CotizacionUseCase(
        cotizacion_repo=cotizacion_repo,
        match_repo=match_repo,
        user_repo=user_repo,
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post(
    "/{match_id}/cotizaciones",
    response_model=CotizacionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_cotizacion(
    match_id: str,
    body: CotizacionRequest,
    current_user: Usuario = Depends(get_current_user),
    use_case: CotizacionUseCase = Depends(_get_cotizacion_use_case),
) -> CotizacionResponse:
    try:
        cotizacion = await use_case.create(
            match_id=match_id,
            user_id=current_user.id,
            monto_estimado=body.monto_estimado,
            detalle=body.detalle,
            fecha_disponible=body.fecha_disponible,
        )
    except NotFound as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except Forbidden as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc

    return _to_cotizacion_response(cotizacion)


@router.patch(
    "/{match_id}/cotizaciones/{cotizacion_id}/accept",
    response_model=CotizacionResponse,
)
async def accept_cotizacion(
    match_id: str,
    cotizacion_id: str,
    current_user: Usuario = Depends(get_current_user),
    use_case: CotizacionUseCase = Depends(_get_cotizacion_use_case),
) -> CotizacionResponse:
    try:
        cotizacion = await use_case.accept(
            match_id=match_id,
            cotizacion_id=cotizacion_id,
            user_id=current_user.id,
        )
    except NotFound as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except Forbidden as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc
    except InvalidTransition as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    return _to_cotizacion_response(cotizacion)


@router.patch(
    "/{match_id}/cotizaciones/{cotizacion_id}/reject",
    response_model=CotizacionResponse,
)
async def reject_cotizacion(
    match_id: str,
    cotizacion_id: str,
    current_user: Usuario = Depends(get_current_user),
    use_case: CotizacionUseCase = Depends(_get_cotizacion_use_case),
) -> CotizacionResponse:
    try:
        cotizacion = await use_case.reject(
            match_id=match_id,
            cotizacion_id=cotizacion_id,
            user_id=current_user.id,
        )
    except NotFound as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except Forbidden as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc
    except InvalidTransition as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    return _to_cotizacion_response(cotizacion)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _to_cotizacion_response(cotizacion) -> CotizacionResponse:
    return CotizacionResponse(
        id=cotizacion.id,
        match_id=cotizacion.match_id,
        monto_estimado=cotizacion.monto_estimado,
        detalle=cotizacion.detalle,
        fecha_disponible=cotizacion.fecha_disponible,
        estado=cotizacion.estado,
        creado_en=cotizacion.created_at,
    )
