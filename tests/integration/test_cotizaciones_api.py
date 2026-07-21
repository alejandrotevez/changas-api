"""Integration tests for cotizaciones endpoints."""

from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.framework.models import CotizacionModel, MatchModel
from tests.conftest import _uuid


@pytest.mark.asyncio
async def test_changador_creates_cotizacion(
    async_client: AsyncClient,
    auth_header_changador: dict[str, str],
    db_session: AsyncSession,
) -> None:
    """Changador can create a cotizacion (201)."""
    match = MatchModel(
        id="match-cot-001",
        user_a_id="cliente-001",
        user_b_id="changador-001",
        created_at=None,
    )
    db_session.add(match)
    await db_session.commit()

    resp = await async_client.post(
        "/v1/matches/match-cot-001/cotizaciones",
        json={
            "montoEstimado": 45000,
            "detalle": "Incluye materiales y mano de obra",
            "fechaDisponible": "2026-07-25",
        },
        headers=auth_header_changador,
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["estado"] == "PENDIENTE"
    assert "matchId" in body
    assert "creadoEn" in body


@pytest.mark.asyncio
async def test_cliente_can_accept_cotizacion(
    async_client: AsyncClient,
    auth_header_cliente: dict[str, str],
    db_session: AsyncSession,
) -> None:
    """Cliente can accept PENDIENTE → ACEPTADA."""
    match = MatchModel(
        id="match-cot-002",
        user_a_id="cliente-001",
        user_b_id="changador-001",
        created_at=None,
    )
    db_session.add(match)
    cot = CotizacionModel(
        id=_uuid(),
        match_id="match-cot-002",
        monto_estimado=45000,
        detalle="Arreglo cocina",
        fecha_disponible="2026-07-25",
        estado="PENDIENTE",
        creado_por_id="changador-001",
        created_at=None,
    )
    db_session.add(cot)
    await db_session.commit()

    resp = await async_client.patch(
        f"/v1/matches/match-cot-002/cotizaciones/{cot.id}/accept",
        headers=auth_header_cliente,
    )
    assert resp.status_code == 200
    assert resp.json()["estado"] == "ACEPTADA"


@pytest.mark.asyncio
async def test_cliente_can_reject_cotizacion(
    async_client: AsyncClient,
    auth_header_cliente: dict[str, str],
    db_session: AsyncSession,
) -> None:
    """Cliente can reject PENDIENTE → RECHAZADA."""
    match = MatchModel(
        id="match-cot-003",
        user_a_id="cliente-001",
        user_b_id="changador-001",
        created_at=None,
    )
    db_session.add(match)
    cot = CotizacionModel(
        id=_uuid(),
        match_id="match-cot-003",
        monto_estimado=30000,
        detalle="Pintura living",
        fecha_disponible="2026-08-01",
        estado="PENDIENTE",
        creado_por_id="changador-001",
        created_at=None,
    )
    db_session.add(cot)
    await db_session.commit()

    resp = await async_client.patch(
        f"/v1/matches/match-cot-003/cotizaciones/{cot.id}/reject",
        headers=auth_header_cliente,
    )
    assert resp.status_code == 200
    assert resp.json()["estado"] == "RECHAZADA"


@pytest.mark.asyncio
async def test_cliente_cannot_create_cotizacion(
    async_client: AsyncClient,
    auth_header_cliente: dict[str, str],
    db_session: AsyncSession,
) -> None:
    """Cliente creating cotizacion returns 403."""
    match = MatchModel(
        id="match-cot-004",
        user_a_id="cliente-001",
        user_b_id="changador-001",
        created_at=None,
    )
    db_session.add(match)
    await db_session.commit()

    resp = await async_client.post(
        "/v1/matches/match-cot-004/cotizaciones",
        json={
            "montoEstimado": 10000,
            "detalle": "Test",
            "fechaDisponible": "2026-07-30",
        },
        headers=auth_header_cliente,
    )
    assert resp.status_code == 403
