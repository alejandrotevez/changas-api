"""Unit tests for swipe use case."""

from __future__ import annotations

from datetime import datetime
from unittest.mock import AsyncMock

import pytest

from app.domain.entities import Match, Swipe
from app.domain.exceptions import DuplicateSwipe, NotFound
from app.usecases.swipe import SwipeUseCase


class TestSwipeUseCase:
    @pytest.mark.asyncio
    async def test_swipe_like_missing_item(self) -> None:
        feed_repo = AsyncMock()
        feed_repo.get_item_owner_id = AsyncMock(return_value=None)

        uc = SwipeUseCase(
            swipe_repo=AsyncMock(),
            match_repo=AsyncMock(),
            feed_repo=feed_repo,
        )
        with pytest.raises(NotFound, match="Item with id 'nonexistent' not found"):
            await uc.execute(user_id="user-a", item_id="nonexistent", liked=True)

    @pytest.mark.asyncio
    async def test_swipe_duplicate(self) -> None:
        feed_repo = AsyncMock()
        feed_repo.get_item_owner_id = AsyncMock(return_value="owner-id")
        swipe_repo = AsyncMock()
        swipe_repo.exists = AsyncMock(return_value=True)

        uc = SwipeUseCase(
            swipe_repo=swipe_repo,
            match_repo=AsyncMock(),
            feed_repo=feed_repo,
        )
        with pytest.raises(DuplicateSwipe):
            await uc.execute(user_id="user-a", item_id="item-1", liked=True)

    @pytest.mark.asyncio
    async def test_swipe_like_no_match(self) -> None:
        feed_repo = AsyncMock()
        feed_repo.get_item_owner_id = AsyncMock(return_value="owner-id")
        swipe_repo = AsyncMock()
        swipe_repo.exists = AsyncMock(return_value=False)
        swipe_repo.get_mutual_like = AsyncMock(return_value=None)
        swipe_repo.create = AsyncMock(return_value=Swipe(
            id="swipe-1", user_id="user-a", item_id="item-1", liked=True,
            created_at=datetime(2025, 1, 1),
        ))

        uc = SwipeUseCase(
            swipe_repo=swipe_repo,
            match_repo=AsyncMock(),
            feed_repo=feed_repo,
        )
        result = await uc.execute(user_id="user-a", item_id="item-1", liked=True)

        assert result.es_match is False
        assert result.match_id is None
        swipe_repo.get_mutual_like.assert_awaited_once_with("user-a", "owner-id")

    @pytest.mark.asyncio
    async def test_swipe_dislike(self) -> None:
        feed_repo = AsyncMock()
        feed_repo.get_item_owner_id = AsyncMock(return_value="owner-id")
        swipe_repo = AsyncMock()
        swipe_repo.exists = AsyncMock(return_value=False)
        swipe_repo.create = AsyncMock()

        match_repo = AsyncMock()

        uc = SwipeUseCase(
            swipe_repo=swipe_repo,
            match_repo=match_repo,
            feed_repo=feed_repo,
        )
        result = await uc.execute(user_id="user-a", item_id="item-1", liked=False)

        assert result.es_match is False
        assert result.match_id is None
        match_repo.create.assert_not_called()

    @pytest.mark.asyncio
    async def test_swipe_mutual_like_creates_match(self) -> None:
        feed_repo = AsyncMock()
        feed_repo.get_item_owner_id = AsyncMock(return_value="owner-b")

        mutual_swipe = Swipe(
            id="swipe-0", user_id="owner-b", item_id="user-a-item",
            liked=True, created_at=datetime(2025, 1, 1),
        )
        swipe_repo = AsyncMock()
        swipe_repo.exists = AsyncMock(return_value=False)
        swipe_repo.get_mutual_like = AsyncMock(return_value=mutual_swipe)
        swipe_repo.create = AsyncMock(return_value=Swipe(
            id="swipe-1", user_id="user-a", item_id="item-1", liked=True,
            created_at=datetime(2025, 1, 1),
        ))

        match_repo = AsyncMock()
        match_repo.exists = AsyncMock(return_value=False)
        created_match = Match(
            id="match-abc", user_a_id="owner-b", user_b_id="user-a",
            created_at=datetime(2025, 1, 1),
        )
        match_repo.create = AsyncMock(return_value=created_match)

        uc = SwipeUseCase(
            swipe_repo=swipe_repo,
            match_repo=match_repo,
            feed_repo=feed_repo,
        )

        result = await uc.execute(
            user_id="user-a", item_id="item-1", liked=True
        )

        assert result.es_match is True
        assert result.match_id == "match-abc"
        match_repo.exists.assert_awaited_once_with("owner-b", "user-a")
        match_repo.create.assert_awaited_once()
        created_match = match_repo.create.await_args.args[0]
        assert created_match.user_a_id == "owner-b"
        assert created_match.user_b_id == "user-a"
