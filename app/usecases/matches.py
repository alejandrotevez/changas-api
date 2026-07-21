from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Union

from app.domain.entities import ChangadorPerfil, ChangaPost, Match
from app.domain.interfaces import (
    FeedRepository,
    MatchRepository,
    MessageRepository,
)


@dataclass(frozen=True)
class MatchItem:
    id: str
    item: Union[ChangaPost, ChangadorPerfil]
    creado_en: datetime
    ultimo_mensaje: Optional[str]
    ultima_actividad: datetime  # For sorting: max(last_msg_time, match_creation)


class MatchUseCase:
    """List a user's matches with last-message preview, sorted by recency."""

    def __init__(
        self,
        match_repo: MatchRepository,
        feed_repo: FeedRepository,
        message_repo: MessageRepository,
    ) -> None:
        self._match_repo = match_repo
        self._feed_repo = feed_repo
        self._message_repo = message_repo

    async def list_user_matches(self, user_id: str) -> list[MatchItem]:
        matches = await self._match_repo.get_by_user(user_id)

        items: list[MatchItem] = []
        for match in matches:
            # Resolve the other user's feed item
            other_user_id = (
                match.user_b_id
                if match.user_a_id == user_id
                else match.user_a_id
            )
            item = await self._resolve_other_item(other_user_id)
            if item is None:
                continue

            # Get last message (full object for timestamp)
            messages = await self._message_repo.get_by_match(match.id)
            ultimo_mensaje: Optional[str] = (
                messages[-1].texto if messages else None
            )
            last_msg_time: Optional[datetime] = (
                messages[-1].created_at if messages else None
            )

            # Sort key: most recent of last message time or match creation
            ultima_actividad = (
                last_msg_time
                if last_msg_time and last_msg_time > match.created_at
                else match.created_at
            )

            items.append(
                MatchItem(
                    id=match.id,
                    item=item,
                    creado_en=match.created_at,
                    ultimo_mensaje=ultimo_mensaje,
                    ultima_actividad=ultima_actividad,
                )
            )

        # Sort by most recent activity descending
        items.sort(key=lambda mi: mi.ultima_actividad, reverse=True)
        return items

    async def _resolve_other_item(
        self, other_user_id: str
    ) -> Optional[Union[ChangaPost, ChangadorPerfil]]:
        """Get the feed item (ChangaPost or ChangadorPerfil) of another user."""
        post = await self._feed_repo.get_changa_post_by_user_id(other_user_id)
        if post is not None:
            return post
        return await self._feed_repo.get_changador_perfil_by_user_id(
            other_user_id
        )
