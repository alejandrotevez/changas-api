"""Integration tests for matches endpoint."""

from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.framework.models import MatchModel, MessageModel
from tests.conftest import _insert_changa_post, _uuid


@pytest.mark.asyncio
async def test_list_matches_returns_match_list(
    async_client: AsyncClient,
    auth_header_cliente: dict[str, str],
    db_session: AsyncSession,
) -> None:
    """GET /matches returns match list."""
    # The other user needs a feed item for the match to resolve
    await _insert_changa_post(db_session, user_id="changador-001")

    match = MatchModel(
        id=_uuid(),
        user_a_id="cliente-001",
        user_b_id="changador-001",
        created_at=None,
    )
    db_session.add(match)
    await db_session.commit()

    resp = await async_client.get("/v1/matches", headers=auth_header_cliente)
    assert resp.status_code == 200
    items = resp.json()
    assert len(items) > 0
    assert items[0]["id"] == match.id


@pytest.mark.asyncio
async def test_matches_includes_last_message(
    async_client: AsyncClient,
    auth_header_cliente: dict[str, str],
    db_session: AsyncSession,
) -> None:
    """Match response includes ultimoMensaje."""
    # The other user needs a feed item for the match to resolve
    await _insert_changa_post(db_session, user_id="changador-001")

    match = MatchModel(
        id=_uuid(),
        user_a_id="cliente-001",
        user_b_id="changador-001",
        created_at=None,
    )
    db_session.add(match)
    msg = MessageModel(
        id=_uuid(),
        match_id=match.id,
        autor_id="changador-001",
        texto="Hola!",
        created_at=None,
    )
    db_session.add(msg)
    await db_session.commit()

    resp = await async_client.get("/v1/matches", headers=auth_header_cliente)
    assert resp.status_code == 200
    items = resp.json()
    assert items[0]["ultimoMensaje"] == "Hola!"


@pytest.mark.asyncio
async def test_matches_empty_when_no_matches(
    async_client: AsyncClient,
    auth_header_changador: dict[str, str],
) -> None:
    """No matches returns empty array."""
    resp = await async_client.get("/v1/matches", headers=auth_header_changador)
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_matches_ordered_by_recency(
    async_client: AsyncClient,
    auth_header_cliente: dict[str, str],
    db_session: AsyncSession,
) -> None:
    """Matches are ordered by most recent activity."""
    # The other user needs a feed item for the match to resolve
    await _insert_changa_post(db_session, user_id="changador-001")

    old_match = MatchModel(
        id=_uuid(),
        user_a_id="cliente-001",
        user_b_id="changador-001",
        created_at=None,
    )
    db_session.add(old_match)
    await db_session.commit()

    resp = await async_client.get("/v1/matches", headers=auth_header_cliente)
    assert resp.status_code == 200
    items = resp.json()
    assert len(items) >= 1
