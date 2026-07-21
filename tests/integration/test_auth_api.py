"""Integration tests for auth endpoints."""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.framework.models import UserModel
from tests.conftest import TEST_SECRET, _insert_user, _uuid


@pytest.mark.asyncio
async def test_login_email_success(
    async_client: AsyncClient,
    cliente_user,
) -> None:
    """Valid credentials return 200 with usuario + token."""
    resp = await async_client.post(
        "/v1/auth/login/email",
        json={"email": "cliente@test.com", "password": "password123"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "usuario" in body
    assert "token" in body
    assert body["usuario"]["rolActual"] == "CLIENTE"


@pytest.mark.asyncio
async def test_login_email_invalid_password(
    async_client: AsyncClient,
) -> None:
    """Invalid password returns 401."""
    resp = await async_client.post(
        "/v1/auth/login/email",
        json={"email": "cliente@test.com", "password": "wrongpass"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_login_email_unknown_user(async_client: AsyncClient) -> None:
    """Unknown email returns 401 without revealing whether email exists."""
    resp = await async_client.post(
        "/v1/auth/login/email",
        json={"email": "unknown@test.com", "password": "anything"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_feed_without_token_returns_401(
    async_client: AsyncClient,
) -> None:
    """Missing Authorization header returns 401."""
    resp = await async_client.get("/v1/feed")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_feed_with_invalid_token_returns_401(
    async_client: AsyncClient,
) -> None:
    """Malformed token returns 401."""
    resp = await async_client.get(
        "/v1/feed", headers={"Authorization": "Bearer invalid-token"}
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_update_user_profile(
    async_client: AsyncClient,
    auth_header_cliente: dict[str, str],
) -> None:
    """PATCH /users/me updates rol and returns updated user."""
    resp = await async_client.patch(
        "/v1/users/me",
        json={"rolActual": "CHANGADOR", "tags": ["#Plomero"]},
        headers=auth_header_cliente,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["rolActual"] == "CHANGADOR"
    assert "#Plomero" in body["tags"]


@pytest.mark.asyncio
async def test_update_user_partial_preserves_fields(
    async_client: AsyncClient,
    auth_header_cliente: dict[str, str],
    db_session,
) -> None:
    """Partial update preserves unset fields."""
    resp = await async_client.patch(
        "/v1/users/me",
        json={"rolActual": "CHANGADOR"},
        headers=auth_header_cliente,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["rolActual"] == "CHANGADOR"
    assert isinstance(body["tags"], list)
