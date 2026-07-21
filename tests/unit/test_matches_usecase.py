"""Unit tests for matches use case."""

from __future__ import annotations

from datetime import datetime
from unittest.mock import AsyncMock

import pytest

from app.domain.entities import ChangadorPerfil, ChangaPost, Match, Mensaje
from app.usecases.matches import MatchUseCase


def _changa_post(user_id: str = "user-other", **overrides: object) -> ChangaPost:
    return ChangaPost(
        id="post-1",
        titulo="Caño roto",
        descripcion_corta="Arreglo urgente",
        user_id=user_id,
        created_at=datetime(2025, 1, 1),
        **overrides,  # type: ignore[arg-type]
    )


def _changador_perfil(user_id: str = "user-other", **overrides: object) -> ChangadorPerfil:
    return ChangadorPerfil(
        id="perfil-1",
        nombre="Roberto Gómez",
        user_id=user_id,
        created_at=datetime(2025, 1, 1),
        **overrides,  # type: ignore[arg-type]
    )


class TestMatchUseCase:
    @pytest.mark.asyncio
    async def test_list_matches_empty(self) -> None:
        match_repo = AsyncMock()
        match_repo.get_by_user = AsyncMock(return_value=[])

        uc = MatchUseCase(
            match_repo=match_repo,
            feed_repo=AsyncMock(),
            message_repo=AsyncMock(),
        )
        result = await uc.list_user_matches("user-a")
        assert result == []

    @pytest.mark.asyncio
    async def test_list_matches_with_changa_post(self) -> None:
        match = Match(
            id="match-1", user_a_id="user-a", user_b_id="user-b",
            created_at=datetime(2025, 1, 1),
        )
        match_repo = AsyncMock()
        match_repo.get_by_user = AsyncMock(return_value=[match])

        post = _changa_post(user_id="user-b")
        feed_repo = AsyncMock()
        feed_repo.get_changa_post_by_user_id = AsyncMock(return_value=post)
        feed_repo.get_changador_perfil_by_user_id = AsyncMock(return_value=None)

        message_repo = AsyncMock()
        message_repo.get_by_match = AsyncMock(return_value=[])

        uc = MatchUseCase(
            match_repo=match_repo,
            feed_repo=feed_repo,
            message_repo=message_repo,
        )
        result = await uc.list_user_matches("user-a")

        assert len(result) == 1
        assert result[0].id == "match-1"
        assert result[0].item == post
        assert result[0].ultimo_mensaje is None

    @pytest.mark.asyncio
    async def test_list_matches_with_changador_perfil(self) -> None:
        match = Match(
            id="match-1", user_a_id="user-b", user_b_id="user-a",
            created_at=datetime(2025, 1, 1),
        )
        match_repo = AsyncMock()
        match_repo.get_by_user = AsyncMock(return_value=[match])

        perfil = _changador_perfil(user_id="user-b")
        feed_repo = AsyncMock()
        feed_repo.get_changa_post_by_user_id = AsyncMock(return_value=None)
        feed_repo.get_changador_perfil_by_user_id = AsyncMock(return_value=perfil)

        message_repo = AsyncMock()
        message_repo.get_by_match = AsyncMock(return_value=[])

        uc = MatchUseCase(
            match_repo=match_repo,
            feed_repo=feed_repo,
            message_repo=message_repo,
        )
        result = await uc.list_user_matches("user-a")

        assert len(result) == 1
        assert result[0].id == "match-1"
        # user-a is user_b_id, other is user-b (user_a_id)
        feed_repo.get_changa_post_by_user_id.assert_awaited_once_with("user-b")
        feed_repo.get_changador_perfil_by_user_id.assert_awaited_once_with("user-b")

    @pytest.mark.asyncio
    async def test_list_matches_includes_last_message(self) -> None:
        match = Match(
            id="match-1", user_a_id="user-a", user_b_id="user-b",
            created_at=datetime(2025, 1, 1),
        )
        match_repo = AsyncMock()
        match_repo.get_by_user = AsyncMock(return_value=[match])

        feed_repo = AsyncMock()
        feed_repo.get_changa_post_by_user_id = AsyncMock(
            return_value=_changa_post(user_id="user-b")
        )
        feed_repo.get_changador_perfil_by_user_id = AsyncMock(return_value=None)

        messages = [
            Mensaje(
                id="m1", match_id="match-1", autor_id="user-a",
                texto="Hola", created_at=datetime(2025, 1, 2),
            ),
            Mensaje(
                id="m2", match_id="match-1", autor_id="user-b",
                texto="Que onda", created_at=datetime(2025, 1, 3),
            ),
        ]
        message_repo = AsyncMock()
        message_repo.get_by_match = AsyncMock(return_value=messages)

        uc = MatchUseCase(
            match_repo=match_repo,
            feed_repo=feed_repo,
            message_repo=message_repo,
        )
        result = await uc.list_user_matches("user-a")

        assert len(result) == 1
        assert result[0].ultimo_mensaje == "Que onda"

    @pytest.mark.asyncio
    async def test_list_matches_ordered_by_recency(self) -> None:
        match_old = Match(
            id="match-old", user_a_id="user-a", user_b_id="user-b",
            created_at=datetime(2025, 1, 1),
        )
        match_recent = Match(
            id="match-recent", user_a_id="user-a", user_b_id="user-c",
            created_at=datetime(2025, 1, 10),
        )
        match_repo = AsyncMock()
        match_repo.get_by_user = AsyncMock(return_value=[match_old, match_recent])

        feed_repo = AsyncMock()
        feed_repo.get_changa_post_by_user_id = AsyncMock(
            side_effect=lambda uid: _changa_post(user_id=uid)
        )
        feed_repo.get_changador_perfil_by_user_id = AsyncMock(return_value=None)

        message_repo = AsyncMock()
        message_repo.get_by_match = AsyncMock(
            side_effect=lambda mid: [
                Mensaje(
                    id="m1", match_id=mid, autor_id="user-a",
                    texto="Hi", created_at=datetime(2025, 1, 5),
                ),
            ] if mid == "match-old" else []
        )

        uc = MatchUseCase(
            match_repo=match_repo,
            feed_repo=feed_repo,
            message_repo=message_repo,
        )
        result = await uc.list_user_matches("user-a")

        assert len(result) == 2
        # match-recent (1/10) should come before match-old (1/5 via message)
        assert result[0].id == "match-recent"
        assert result[1].id == "match-old"

    @pytest.mark.asyncio
    async def test_list_matches_skips_if_no_feed_item(self) -> None:
        match = Match(
            id="match-1", user_a_id="user-a", user_b_id="user-ghost",
            created_at=datetime(2025, 1, 1),
        )
        match_repo = AsyncMock()
        match_repo.get_by_user = AsyncMock(return_value=[match])

        feed_repo = AsyncMock()
        feed_repo.get_changa_post_by_user_id = AsyncMock(return_value=None)
        feed_repo.get_changador_perfil_by_user_id = AsyncMock(return_value=None)

        uc = MatchUseCase(
            match_repo=match_repo,
            feed_repo=feed_repo,
            message_repo=AsyncMock(),
        )
        result = await uc.list_user_matches("user-a")

        assert result == []
