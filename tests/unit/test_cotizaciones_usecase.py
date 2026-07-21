"""Unit tests for cotizaciones use case."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest

from app.domain.entities import Cotizacion, Match, Usuario
from app.domain.exceptions import Forbidden, InvalidTransition, NotFound
from app.usecases.cotizaciones import CotizacionUseCase


def _match(**overrides: object) -> Match:
    return Match(
        id="match-1",
        user_a_id="changador-1",
        user_b_id="cliente-1",
        created_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
        **overrides,  # type: ignore[arg-type]
    )


def _usuario(
    id: str = "changador-1",
    rol: str = "CHANGADOR",
    **overrides: object,
) -> Usuario:
    return Usuario(
        id=id,
        nombre="Test User",
        email=f"{id}@test.com",
        password_hash="hash",
        rol_actual=rol,
        created_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
        **overrides,  # type: ignore[arg-type]
    )


def _cotizacion(
    match_id: str = "match-1",
    estado: str = "PENDIENTE",
    creado_por_id: str = "changador-1",
    **overrides: object,
) -> Cotizacion:
    return Cotizacion(
        id="cotizacion-1",
        match_id=match_id,
        monto_estimado=15000.0,
        detalle="Arreglo de caño",
        fecha_disponible="2025-02-01",
        estado=estado,
        creado_por_id=creado_por_id,
        created_at=datetime(2025, 1, 5, tzinfo=timezone.utc),
        **overrides,  # type: ignore[arg-type]
    )


class TestCotizacionUseCase:
    @pytest.mark.asyncio
    async def test_create_cotizacion_happy_path(self) -> None:
        match_repo = AsyncMock()
        match_repo.get_by_id = AsyncMock(return_value=_match())
        user_repo = AsyncMock()
        user_repo.get_by_id = AsyncMock(
            return_value=_usuario(id="changador-1", rol="CHANGADOR")
        )
        cotizacion_repo = AsyncMock()
        expected = _cotizacion()
        cotizacion_repo.create = AsyncMock(return_value=expected)

        uc = CotizacionUseCase(
            cotizacion_repo=cotizacion_repo,
            match_repo=match_repo,
            user_repo=user_repo,
        )

        result = await uc.create(
                match_id="match-1",
                user_id="changador-1",
                monto_estimado=15000.0,
                detalle="Arreglo de caño",
                fecha_disponible="2025-02-01",
            )

        assert result.estado == "PENDIENTE"
        assert result.monto_estimado == 15000.0
        assert result.creado_por_id == "changador-1"

    @pytest.mark.asyncio
    async def test_create_cotizacion_by_cliente(self) -> None:
        match_repo = AsyncMock()
        match_repo.get_by_id = AsyncMock(return_value=_match())
        user_repo = AsyncMock()
        user_repo.get_by_id = AsyncMock(
            return_value=_usuario(id="cliente-1", rol="CLIENTE")
        )

        uc = CotizacionUseCase(
            cotizacion_repo=AsyncMock(),
            match_repo=match_repo,
            user_repo=user_repo,
        )
        with pytest.raises(
            Forbidden, match="Only a changador can create a cotizacion"
        ):
            await uc.create(
                match_id="match-1",
                user_id="cliente-1",
                monto_estimado=5000.0,
                detalle="Limpieza",
                fecha_disponible="2025-02-10",
            )

    @pytest.mark.asyncio
    async def test_create_cotizacion_nonexistent_match(self) -> None:
        match_repo = AsyncMock()
        match_repo.get_by_id = AsyncMock(return_value=None)

        uc = CotizacionUseCase(
            cotizacion_repo=AsyncMock(),
            match_repo=match_repo,
            user_repo=AsyncMock(),
        )
        with pytest.raises(NotFound, match="Match with id 'bad-id' not found"):
            await uc.create(
                match_id="bad-id",
                user_id="changador-1",
                monto_estimado=10000.0,
                detalle="Test",
                fecha_disponible="2025-03-01",
            )

    @pytest.mark.asyncio
    async def test_accept_cotizacion_happy_path(self) -> None:
        match_repo = AsyncMock()
        match_repo.get_by_id = AsyncMock(return_value=_match())
        user_repo = AsyncMock()
        user_repo.get_by_id = AsyncMock(
            return_value=_usuario(id="cliente-1", rol="CLIENTE")
        )
        cotizacion_repo = AsyncMock()
        cotizacion_repo.get_by_id = AsyncMock(return_value=_cotizacion())
        accepted = _cotizacion(estado="ACEPTADA")
        cotizacion_repo.update = AsyncMock(return_value=accepted)

        uc = CotizacionUseCase(
            cotizacion_repo=cotizacion_repo,
            match_repo=match_repo,
            user_repo=user_repo,
        )
        result = await uc.accept(
            match_id="match-1",
            cotizacion_id="cotizacion-1",
            user_id="cliente-1",
        )

        assert result.estado == "ACEPTADA"
        cotizacion_repo.update.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_accept_cotizacion_by_non_participant(self) -> None:
        match_repo = AsyncMock()
        match_repo.get_by_id = AsyncMock(return_value=_match())

        uc = CotizacionUseCase(
            cotizacion_repo=AsyncMock(),
            match_repo=match_repo,
            user_repo=AsyncMock(),
        )
        with pytest.raises(NotFound, match="Match with id 'match-1' not found"):
            await uc.accept(
                match_id="match-1",
                cotizacion_id="cotizacion-1",
                user_id="stranger-1",
            )

    @pytest.mark.asyncio
    async def test_accept_cotizacion_by_changador(self) -> None:
        match_repo = AsyncMock()
        match_repo.get_by_id = AsyncMock(return_value=_match())
        user_repo = AsyncMock()
        user_repo.get_by_id = AsyncMock(
            return_value=_usuario(id="changador-1", rol="CHANGADOR")
        )

        uc = CotizacionUseCase(
            cotizacion_repo=AsyncMock(),
            match_repo=match_repo,
            user_repo=user_repo,
        )
        with pytest.raises(
            Forbidden, match="Only the client can accept or reject a cotizacion"
        ):
            await uc.accept(
                match_id="match-1",
                cotizacion_id="cotizacion-1",
                user_id="changador-1",
            )

    @pytest.mark.asyncio
    async def test_reject_cotizacion_happy_path(self) -> None:
        match_repo = AsyncMock()
        match_repo.get_by_id = AsyncMock(return_value=_match())
        user_repo = AsyncMock()
        user_repo.get_by_id = AsyncMock(
            return_value=_usuario(id="cliente-1", rol="CLIENTE")
        )
        cotizacion_repo = AsyncMock()
        cotizacion_repo.get_by_id = AsyncMock(return_value=_cotizacion())
        rejected = _cotizacion(estado="RECHAZADA")
        cotizacion_repo.update = AsyncMock(return_value=rejected)

        uc = CotizacionUseCase(
            cotizacion_repo=cotizacion_repo,
            match_repo=match_repo,
            user_repo=user_repo,
        )
        result = await uc.reject(
            match_id="match-1",
            cotizacion_id="cotizacion-1",
            user_id="cliente-1",
        )

        assert result.estado == "RECHAZADA"

    @pytest.mark.asyncio
    async def test_accept_already_accepted(self) -> None:
        match_repo = AsyncMock()
        match_repo.get_by_id = AsyncMock(return_value=_match())
        user_repo = AsyncMock()
        user_repo.get_by_id = AsyncMock(
            return_value=_usuario(id="cliente-1", rol="CLIENTE")
        )
        cotizacion_repo = AsyncMock()
        cotizacion_repo.get_by_id = AsyncMock(
            return_value=_cotizacion(estado="ACEPTADA")
        )

        uc = CotizacionUseCase(
            cotizacion_repo=cotizacion_repo,
            match_repo=match_repo,
            user_repo=user_repo,
        )
        with pytest.raises(
            InvalidTransition, match="Invalid transition for Cotizacion"
        ):
            await uc.accept(
                match_id="match-1",
                cotizacion_id="cotizacion-1",
                user_id="cliente-1",
            )
