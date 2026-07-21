"""Integration tests for swipe endpoints."""

from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.conftest import _insert_changa_post, _uuid


@pytest.mark.asyncio
async def test_swipe_like(
    async_client: AsyncClient,
    auth_header_changador: dict[str, str],
    db_session: AsyncSession,
    changador_user,
) -> None:
    """User likes a feed item."""
    post = await _insert_changa_post(db_session, user_id=changador_user.id)

    resp = await async_client.post(
        "/v1/feed/swipe",
        json={"itemId": post.id, "liked": True},
        headers=auth_header_changador,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "esMatch" in body


@pytest.mark.asyncio
async def test_swipe_dislike(
    async_client: AsyncClient,
    auth_header_changador: dict[str, str],
    db_session: AsyncSession,
    changador_user,
) -> None:
    """User dislikes a feed item."""
    post = await _insert_changa_post(db_session, user_id=changador_user.id)

    resp = await async_client.post(
        "/v1/feed/swipe",
        json={"itemId": post.id, "liked": False},
        headers=auth_header_changador,
    )
    assert resp.status_code == 200
    assert resp.json()["esMatch"] is False


@pytest.mark.asyncio
async def test_swipe_duplicate_returns_409(
    async_client: AsyncClient,
    auth_header_changador: dict[str, str],
    db_session: AsyncSession,
    changador_user,
) -> None:
    """Duplicate swipe returns 409."""
    post = await _insert_changa_post(db_session, user_id=changador_user.id)

    await async_client.post(
        "/v1/feed/swipe",
        json={"itemId": post.id, "liked": True},
        headers=auth_header_changador,
    )
    resp = await async_client.post(
        "/v1/feed/swipe",
        json={"itemId": post.id, "liked": True},
        headers=auth_header_changador,
    )
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_swipe_non_existent_returns_404(
    async_client: AsyncClient,
    auth_header_changador: dict[str, str],
) -> None:
    """Swipe on non-existent item returns 404."""
    resp = await async_client.post(
        "/v1/feed/swipe",
        json={"itemId": "nonexistent", "liked": True},
        headers=auth_header_changador,
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_swipe_mutual_like_creates_match(
    async_client: AsyncClient,
    db_session: AsyncSession,
    cliente_user,
    changador_user,
) -> None:
    """Mutual like creates match and returns esMatch=true with matchId."""
    # Changador likes changa belonging to cliente
    post = await _insert_changa_post(db_session, user_id=cliente_user.id)

    # Changador likes cliente's changa (one-sided, no match yet)
    ts = _make_token(changador_user.id)
    resp1 = await async_client.post(
        "/v1/feed/swipe",
        json={"itemId": post.id, "liked": True},
        headers={"Authorization": f"Bearer {ts}"},
    )
    assert resp1.status_code == 200
    assert resp1.json()["esMatch"] is False

    # Cliente likes changador's profile → mutual!
    from app.framework.models import ChangadorPerfilModel

    profile_id = _uuid()
    profile = ChangadorPerfilModel(
        id=profile_id,
        nombre="Changador",
        fotos_trabajos="[]",
        especialidades="[]",
        user_id=changador_user.id,
        created_at=None,
    )
    db_session.add(profile)
    await db_session.commit()

    ts2 = _make_token(cliente_user.id)
    resp2 = await async_client.post(
        "/v1/feed/swipe",
        json={"itemId": profile_id, "liked": True},
        headers={"Authorization": f"Bearer {ts2}"},
    )
    assert resp2.status_code == 200
    body = resp2.json()
    assert body["esMatch"] is True
    assert body["matchId"] is not None


def _make_token(user_id: str) -> str:
    from app.usecases.auth import TokenService

    return TokenService(secret_override="test-secret-not-for-prod").encode(
        user_id, f"{user_id}@test.com"
    )
