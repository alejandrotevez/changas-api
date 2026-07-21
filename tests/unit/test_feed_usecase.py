"""Unit tests for feed use case."""

from __future__ import annotations

from datetime import datetime
from unittest.mock import AsyncMock

import pytest

from app.domain.entities import ChangadorPerfil, ChangaPost
from app.usecases.feed import FeedUseCase


def _changa_post(id: str = "post-1", **overrides: object) -> ChangaPost:
    return ChangaPost(
        id=id,
        titulo="Caño roto",
        descripcion_corta="Arreglo urgente",
        user_id="user-cliente",
        created_at=datetime(2025, 1, 1),
        **overrides,  # type: ignore[arg-type]
    )


def _changador_perfil(id: str = "perfil-1", **overrides: object) -> ChangadorPerfil:
    return ChangadorPerfil(
        id=id,
        nombre="Roberto Gómez",
        user_id="user-changador",
        created_at=datetime(2025, 1, 1),
        **overrides,  # type: ignore[arg-type]
    )


class TestFeedUseCase:
    @pytest.mark.asyncio
    async def test_feed_for_changador_returns_changa_posts(self) -> None:
        posts = [_changa_post(id="p1"), _changa_post(id="p2")]
        feed_repo = AsyncMock()
        feed_repo.get_changa_posts = AsyncMock(return_value=posts)
        feed_repo.get_changador_perfiles = AsyncMock(return_value=[])
        swipe_repo = AsyncMock()
        swipe_repo.get_swiped_item_ids = AsyncMock(return_value=[])

        uc = FeedUseCase(feed_repo=feed_repo, swipe_repo=swipe_repo)
        result = await uc.execute(user_id="user-c", rol="CHANGADOR", page=1, limit=20)

        assert result == posts
        feed_repo.get_changa_posts.assert_awaited_once_with(
            exclude_swiped_ids=[], limit=20, offset=0
        )

    @pytest.mark.asyncio
    async def test_feed_for_cliente_returns_changador_perfiles(self) -> None:
        perfiles = [_changador_perfil(id="pf1")]
        feed_repo = AsyncMock()
        feed_repo.get_changador_perfiles = AsyncMock(return_value=perfiles)
        feed_repo.get_changa_posts = AsyncMock(return_value=[])
        swipe_repo = AsyncMock()
        swipe_repo.get_swiped_item_ids = AsyncMock(return_value=[])

        uc = FeedUseCase(feed_repo=feed_repo, swipe_repo=swipe_repo)
        result = await uc.execute(user_id="user-c", rol="CLIENTE", page=1, limit=20)

        assert result == perfiles
        feed_repo.get_changador_perfiles.assert_awaited_once_with(
            exclude_swiped_ids=[], limit=20, offset=0
        )

    @pytest.mark.asyncio
    async def test_feed_excludes_swiped(self) -> None:
        posts = [_changa_post(id="p2")]
        feed_repo = AsyncMock()
        feed_repo.get_changa_posts = AsyncMock(return_value=posts)
        feed_repo.get_changador_perfiles = AsyncMock(return_value=[])
        swipe_repo = AsyncMock()
        swipe_repo.get_swiped_item_ids = AsyncMock(return_value=["p1"])

        uc = FeedUseCase(feed_repo=feed_repo, swipe_repo=swipe_repo)
        result = await uc.execute(user_id="user-c", rol="CHANGADOR", page=1, limit=20)

        assert result == posts
        feed_repo.get_changa_posts.assert_awaited_once_with(
            exclude_swiped_ids=["p1"], limit=20, offset=0
        )

    @pytest.mark.asyncio
    async def test_feed_pagination(self) -> None:
        feed_repo = AsyncMock()
        feed_repo.get_changa_posts = AsyncMock(return_value=[])
        feed_repo.get_changador_perfiles = AsyncMock(return_value=[])
        swipe_repo = AsyncMock()
        swipe_repo.get_swiped_item_ids = AsyncMock(return_value=[])

        uc = FeedUseCase(feed_repo=feed_repo, swipe_repo=swipe_repo)
        await uc.execute(user_id="user-c", rol="CHANGADOR", page=3, limit=10)

        feed_repo.get_changa_posts.assert_awaited_once_with(
            exclude_swiped_ids=[], limit=10, offset=20
        )

    @pytest.mark.asyncio
    async def test_feed_empty_when_all_swiped(self) -> None:
        feed_repo = AsyncMock()
        feed_repo.get_changa_posts = AsyncMock(return_value=[])
        feed_repo.get_changador_perfiles = AsyncMock(return_value=[])
        swipe_repo = AsyncMock()
        swipe_repo.get_swiped_item_ids = AsyncMock(return_value=["p1", "p2", "p3"])

        uc = FeedUseCase(feed_repo=feed_repo, swipe_repo=swipe_repo)
        result = await uc.execute(user_id="user-c", rol="CHANGADOR", page=1, limit=20)

        assert result == []
        feed_repo.get_changa_posts.assert_awaited_once_with(
            exclude_swiped_ids=["p1", "p2", "p3"], limit=20, offset=0
        )
