from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from app.domain.entities import Match, Swipe
from app.domain.exceptions import DuplicateSwipe, NotFound
from app.domain.interfaces import FeedRepository, MatchRepository, SwipeRepository


@dataclass(frozen=True)
class SwipeResult:
    es_match: bool
    match_id: Optional[str]


class SwipeUseCase:
    """Record a swipe vote and detect mutual likes (matches) atomically."""

    def __init__(
        self,
        swipe_repo: SwipeRepository,
        match_repo: MatchRepository,
        feed_repo: FeedRepository,
    ) -> None:
        self._swipe_repo = swipe_repo
        self._match_repo = match_repo
        self._feed_repo = feed_repo

    async def execute(
        self,
        user_id: str,
        item_id: str,
        liked: bool,
    ) -> SwipeResult:
        # 1. Validate item exists
        item_owner_id = await self._feed_repo.get_item_owner_id(item_id)
        if item_owner_id is None:
            raise NotFound(entity="Item", id=item_id)

        # 2. Check no duplicate swipe
        exists = await self._swipe_repo.exists(user_id, item_id)
        if exists:
            raise DuplicateSwipe(user_id=user_id, item_id=item_id)

        # 3. INSERT swipe record
        swipe = Swipe(
            id=uuid.uuid4().hex,
            user_id=user_id,
            item_id=item_id,
            liked=liked,
            created_at=datetime.now(timezone.utc),
        )
        await self._swipe_repo.create(swipe)

        es_match = False
        match_id: Optional[str] = None

        # 4. If liked, check for mutual like
        if liked:
            mutual = await self._swipe_repo.get_mutual_like(user_id, item_owner_id)
            if mutual is not None:
                # 5. Check match doesn't already exist, then create
                a_id, b_id = sorted([user_id, item_owner_id])
                already_matched = await self._match_repo.exists(a_id, b_id)
                if not already_matched:
                    match = Match(
                        id=uuid.uuid4().hex,
                        user_a_id=a_id,
                        user_b_id=b_id,
                        created_at=datetime.now(timezone.utc),
                    )
                    match = await self._match_repo.create(match)
                    es_match = True
                    match_id = match.id

        return SwipeResult(es_match=es_match, match_id=match_id)
