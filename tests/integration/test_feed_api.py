"""Integration tests for feed endpoints."""

from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.framework.models import SwipeModel
from tests.conftest import (
    _insert_changa_post,
    _insert_changador_perfil,
    _insert_user,
    _uuid,
)


@pytest.mark.asyncio
async def test_feed_as_changador_returns_changa_posts(
    async_client: AsyncClient,
    auth_header_changador: dict[str, str],
    db_session: AsyncSession,
) -> None:
    """Changador sees ChangaPost items."""
    user = await _insert_user(db_session, id=_uuid(), email=f"{_uuid()[:6]}@c.com")
    await _insert_changa_post(db_session, user_id=user.id)
    await _insert_changa_post(db_session, user_id=user.id)

    resp = await async_client.get("/v1/feed", headers=auth_header_changador)
    assert resp.status_code == 200
    items = resp.json()
    assert len(items) > 0
    for item in items:
        assert item["tipo"] == "CHANGA"
        assert "titulo" in item
        assert "descripcionCorta" in item
        assert "barrio" in item


@pytest.mark.asyncio
async def test_feed_as_cliente_returns_changador_perfiles(
    async_client: AsyncClient,
    auth_header_cliente: dict[str, str],
    db_session: AsyncSession,
) -> None:
    """Cliente sees ChangadorPerfil items."""
    user = await _insert_user(db_session, id=_uuid(), email=f"{_uuid()[:6]}@c.com")
    await _insert_changador_perfil(db_session, user_id=user.id)

    resp = await async_client.get("/v1/feed", headers=auth_header_cliente)
    assert resp.status_code == 200
    items = resp.json()
    assert len(items) > 0
    for item in items:
        assert item["tipo"] == "CHANGADOR_PERFIL"
        assert "nombre" in item
        assert "especialidades" in item
        assert "fotosTrabajos" in item


@pytest.mark.asyncio
async def test_feed_excludes_swiped_items(
    async_client: AsyncClient,
    auth_header_cliente: dict[str, str],
    db_session: AsyncSession,
) -> None:
    """Swiped items are excluded from feed."""
    user1 = await _insert_user(db_session, id=_uuid(), email=f"{_uuid()[:6]}@a.com")
    profile = await _insert_changador_perfil(db_session, user_id=user1.id)
    user2 = await _insert_user(db_session, id=_uuid(), email=f"{_uuid()[:6]}@b.com")
    profile2 = await _insert_changador_perfil(db_session, user_id=user2.id)

    # Swipe on first profile
    swipe = SwipeModel(
        id=_uuid(),
        user_id="cliente-001",
        item_id=profile.id,
        liked=False,
        created_at=None,
    )
    db_session.add(swipe)
    await db_session.commit()

    resp = await async_client.get("/v1/feed", headers=auth_header_cliente)
    assert resp.status_code == 200
    items = resp.json()
    ids = [i["id"] for i in items]
    assert profile.id not in ids
    assert profile2.id in ids


@pytest.mark.asyncio
async def test_feed_empty_when_all_swiped(
    async_client: AsyncClient,
    auth_header_cliente: dict[str, str],
    db_session: AsyncSession,
) -> None:
    """All items swiped returns empty array."""
    user = await _insert_user(db_session, id=_uuid(), email=f"{_uuid()[:6]}@c.com")
    profile = await _insert_changador_perfil(db_session, user_id=user.id)

    swipe = SwipeModel(
        id=_uuid(),
        user_id="cliente-001",
        item_id=profile.id,
        liked=False,
        created_at=None,
    )
    db_session.add(swipe)
    await db_session.commit()

    resp = await async_client.get("/v1/feed", headers=auth_header_cliente)
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_feed_pagination(
    async_client: AsyncClient,
    auth_header_changador: dict[str, str],
    db_session: AsyncSession,
) -> None:
    """Feed respects page and limit query params."""
    user = await _insert_user(db_session, id=_uuid(), email=f"{_uuid()[:6]}@c.com")
    for _ in range(3):
        await _insert_changa_post(db_session, user_id=user.id)

    resp = await async_client.get(
        "/v1/feed?page=1&limit=2", headers=auth_header_changador
    )
    assert resp.status_code == 200
    assert len(resp.json()) == 2
