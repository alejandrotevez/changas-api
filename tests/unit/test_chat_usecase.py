"""Unit tests for chat use case."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest

from app.domain.entities import Match, Mensaje
from app.domain.exceptions import NotFound
from app.usecases.chat import ChatUseCase


def _match(**overrides: object) -> Match:
    return Match(
        id="match-1",
        user_a_id="user-a",
        user_b_id="user-b",
        created_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
        **overrides,  # type: ignore[arg-type]
    )


def _mensaje(**overrides: object) -> Mensaje:
    params = dict(
        id="msg-1",
        match_id="match-1",
        autor_id="user-a",
        texto="Hola!",
        created_at=datetime(2025, 1, 2, tzinfo=timezone.utc),
    )
    params.update(overrides)
    return Mensaje(**params)  # type: ignore[arg-type]


class TestChatUseCase:
    @pytest.mark.asyncio
    async def test_get_messages_happy_path(self) -> None:
        mensajes = [_mensaje(id="m1"), _mensaje(id="m2")]
        match_repo = AsyncMock()
        match_repo.get_by_id = AsyncMock(return_value=_match())
        message_repo = AsyncMock()
        message_repo.get_by_match = AsyncMock(return_value=mensajes)

        uc = ChatUseCase(match_repo=match_repo, message_repo=message_repo)
        result = await uc.get_messages(match_id="match-1", user_id="user-a")

        assert result == mensajes
        message_repo.get_by_match.assert_awaited_once_with("match-1")

    @pytest.mark.asyncio
    async def test_get_messages_non_participant(self) -> None:
        match_repo = AsyncMock()
        match_repo.get_by_id = AsyncMock(return_value=_match())

        uc = ChatUseCase(match_repo=match_repo, message_repo=AsyncMock())
        with pytest.raises(NotFound, match="Match with id 'match-1' not found"):
            await uc.get_messages(match_id="match-1", user_id="user-c")

    @pytest.mark.asyncio
    async def test_get_messages_nonexistent_match(self) -> None:
        match_repo = AsyncMock()
        match_repo.get_by_id = AsyncMock(return_value=None)

        uc = ChatUseCase(match_repo=match_repo, message_repo=AsyncMock())
        with pytest.raises(NotFound, match="Match with id 'bad-id' not found"):
            await uc.get_messages(match_id="bad-id", user_id="user-a")

    @pytest.mark.asyncio
    async def test_get_messages_empty(self) -> None:
        match_repo = AsyncMock()
        match_repo.get_by_id = AsyncMock(return_value=_match())
        message_repo = AsyncMock()
        message_repo.get_by_match = AsyncMock(return_value=[])

        uc = ChatUseCase(match_repo=match_repo, message_repo=message_repo)
        result = await uc.get_messages(match_id="match-1", user_id="user-a")

        assert result == []

    @pytest.mark.asyncio
    async def test_send_message_happy_path(self) -> None:
        match_repo = AsyncMock()
        match_repo.get_by_id = AsyncMock(return_value=_match())
        message_repo = AsyncMock()

        expected = _mensaje(id="new-msg", texto="Que onda")
        message_repo.create = AsyncMock(return_value=expected)

        uc = ChatUseCase(match_repo=match_repo, message_repo=message_repo)

        result = await uc.send_message(
            match_id="match-1", user_id="user-a", texto="Que onda"
        )

        assert result.texto == "Que onda"
        assert result.autor_id == "user-a"
        assert result.match_id == "match-1"
        message_repo.create.assert_awaited_once()
        created = message_repo.create.await_args.args[0]
        assert created.texto == "Que onda"
        assert created.autor_id == "user-a"
        assert created.match_id == "match-1"

    @pytest.mark.asyncio
    async def test_send_message_non_participant(self) -> None:
        match_repo = AsyncMock()
        match_repo.get_by_id = AsyncMock(return_value=_match())

        uc = ChatUseCase(match_repo=match_repo, message_repo=AsyncMock())
        with pytest.raises(NotFound, match="Match with id 'match-1' not found"):
            await uc.send_message(
                match_id="match-1", user_id="user-c", texto="Hola"
            )

    @pytest.mark.asyncio
    async def test_send_message_empty_text(self) -> None:
        match_repo = AsyncMock()
        match_repo.get_by_id = AsyncMock(return_value=_match())

        message_repo = AsyncMock()
        expected = _mensaje(id="m1", texto="")
        message_repo.create = AsyncMock(return_value=expected)

        uc = ChatUseCase(match_repo=match_repo, message_repo=message_repo)
        result = await uc.send_message(
            match_id="match-1", user_id="user-b", texto=""
        )

        assert result.texto == ""
