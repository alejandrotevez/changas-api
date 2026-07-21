from __future__ import annotations

from typing import Union

from app.domain.entities import ChangadorPerfil, ChangaPost
from app.domain.interfaces import FeedRepository, SwipeRepository


class FeedUseCase:
    """Load role-filtered feed items, excluding already-swiped content."""

    def __init__(
        self,
        feed_repo: FeedRepository,
        swipe_repo: SwipeRepository,
    ) -> None:
        self._feed_repo = feed_repo
        self._swipe_repo = swipe_repo

    async def execute(
        self,
        user_id: str,
        rol: str,
        page: int = 1,
        limit: int = 20,
    ) -> list[Union[ChangaPost, ChangadorPerfil]]:
        swiped_ids = await self._swipe_repo.get_swiped_item_ids(user_id)
        offset = (page - 1) * limit

        if rol == "CHANGADOR":
            return await self._feed_repo.get_changa_posts(
                exclude_swiped_ids=swiped_ids,
                limit=limit,
                offset=offset,
            )
        else:
            return await self._feed_repo.get_changador_perfiles(
                exclude_swiped_ids=swiped_ids,
                limit=limit,
                offset=offset,
            )
