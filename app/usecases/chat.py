from __future__ import annotations

import uuid
from datetime import datetime, timezone
from app.domain.entities import Mensaje
from app.domain.exceptions import NotFound
from app.domain.interfaces import MatchRepository, MessageRepository


class ChatUseCase:
    """Send and retrieve messages within a confirmed match."""

    def __init__(
        self,
        match_repo: MatchRepository,
        message_repo: MessageRepository,
    ) -> None:
        self._match_repo = match_repo
        self._message_repo = message_repo

    async def get_messages(
        self, match_id: str, user_id: str
    ) -> list[Mensaje]:
        match = await self._match_repo.get_by_id(match_id)
        if match is None:
            raise NotFound(entity="Match", id=match_id)

        if not self._is_participant(match, user_id):
            raise NotFound(entity="Match", id=match_id)

        return await self._message_repo.get_by_match(match_id)

    async def send_message(
        self, match_id: str, user_id: str, texto: str
    ) -> Mensaje:
        match = await self._match_repo.get_by_id(match_id)
        if match is None:
            raise NotFound(entity="Match", id=match_id)

        if not self._is_participant(match, user_id):
            raise NotFound(entity="Match", id=match_id)

        mensaje = Mensaje(
            id=uuid.uuid4().hex,
            match_id=match_id,
            autor_id=user_id,
            texto=texto,
            created_at=datetime.now(timezone.utc),
        )
        return await self._message_repo.create(mensaje)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _is_participant(match, user_id: str) -> bool:
        return match.user_a_id == user_id or match.user_b_id == user_id
