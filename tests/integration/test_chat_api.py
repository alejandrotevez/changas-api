"""Integration tests for chat endpoints."""

from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.framework.models import MatchModel, MessageModel
from tests.conftest import _uuid


@pytest.mark.asyncio
async def test_get_messages_returns_history(
    async_client: AsyncClient,
    auth_header_cliente: dict[str, str],
    db_session: AsyncSession,
) -> None:
    """GET /matches/{id}/messages returns message history."""
    match = MatchModel(
        id="match-chat-001",
        user_a_id="cliente-001",
        user_b_id="changador-001",
        created_at=None,
    )
    db_session.add(match)
    msg = MessageModel(
        id=_uuid(),
        match_id="match-chat-001",
        autor_id="changador-001",
        texto="Hola!",
        created_at=None,
    )
    db_session.add(msg)
    await db_session.commit()

    resp = await async_client.get(
        "/v1/matches/match-chat-001/messages",
        headers=auth_header_cliente,
    )
    assert resp.status_code == 200
    items = resp.json()
    assert len(items) > 0
    assert items[0]["texto"] == "Hola!"
    assert "autorId" in items[0]
    assert "enviadoEn" in items[0]


@pytest.mark.asyncio
async def test_send_message_creates_message(
    async_client: AsyncClient,
    auth_header_cliente: dict[str, str],
    db_session: AsyncSession,
) -> None:
    """POST /matches/{id}/messages creates and returns message."""
    match = MatchModel(
        id="match-send-001",
        user_a_id="cliente-001",
        user_b_id="changador-001",
        created_at=None,
    )
    db_session.add(match)
    await db_session.commit()

    resp = await async_client.post(
        "/v1/matches/match-send-001/messages",
        json={"texto": "Hola, cómo estás?"},
        headers=auth_header_cliente,
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["texto"] == "Hola, cómo estás?"
    assert body["autorId"] == "cliente-001"
    assert "enviadoEn" in body


@pytest.mark.asyncio
async def test_send_message_empty_texto_returns_422(
    async_client: AsyncClient,
    auth_header_cliente: dict[str, str],
) -> None:
    """Empty texto returns 422."""
    resp = await async_client.post(
        "/v1/matches/match-nonexistent/messages",
        json={"texto": ""},
        headers=auth_header_cliente,
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_get_messages_non_participant_returns_404(
    async_client: AsyncClient,
    db_session: AsyncSession,
    changador_user,
) -> None:
    """Non-participant gets 404."""
    # Create a match between user-1 and user-2
    match = MatchModel(
        id="match-excl-001",
        user_a_id="user-1",
        user_b_id="user-2",
        created_at=None,
    )
    db_session.add(match)
    await db_session.commit()

    # user-3 (changador) tries to access
    ts = _make_token("changador-001")
    resp = await async_client.get(
        "/v1/matches/match-excl-001/messages",
        headers={"Authorization": f"Bearer {ts}"},
    )
    assert resp.status_code == 404


def _make_token(user_id: str) -> str:
    from app.usecases.auth import TokenService

    return TokenService(secret_override="test-secret-not-for-prod").encode(
        user_id, f"{user_id}@test.com"
    )
