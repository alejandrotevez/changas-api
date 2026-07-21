from __future__ import annotations

from typing import Optional, Protocol

from app.domain.entities import (
    ChangadorPerfil,
    ChangaPost,
    Cotizacion,
    Match,
    Mensaje,
    Swipe,
    Usuario,
)


class UserRepository(Protocol):
    async def get_by_email(self, email: str) -> Optional[Usuario]: ...

    async def get_by_google_id(self, google_id: str) -> Optional[Usuario]: ...

    async def get_by_id(self, user_id: str) -> Optional[Usuario]: ...

    async def create(self, user: Usuario) -> Usuario: ...

    async def update(self, user: Usuario) -> Usuario: ...


class FeedRepository(Protocol):
    async def get_changa_posts(
        self,
        exclude_swiped_ids: list[str],
        limit: int = 20,
        offset: int = 0,
    ) -> list[ChangaPost]: ...

    async def get_changador_perfiles(
        self,
        exclude_swiped_ids: list[str],
        limit: int = 20,
        offset: int = 0,
    ) -> list[ChangadorPerfil]: ...

    async def get_item_owner_id(self, item_id: str) -> Optional[str]: ...

    async def get_changa_post_by_user_id(
        self, user_id: str
    ) -> Optional[ChangaPost]: ...

    async def get_changador_perfil_by_user_id(
        self, user_id: str
    ) -> Optional[ChangadorPerfil]: ...


class SwipeRepository(Protocol):
    async def create(self, swipe: Swipe) -> Swipe: ...

    async def exists(self, user_id: str, item_id: str) -> bool: ...

    async def get_by_user_and_item(
        self, user_id: str, item_id: str
    ) -> Optional[Swipe]: ...

    async def get_mutual_like(
        self, user_id: str, item_owner_id: str
    ) -> Optional[Swipe]: ...

    async def get_swiped_item_ids(self, user_id: str) -> list[str]: ...


class MatchRepository(Protocol):
    async def get_by_user(self, user_id: str) -> list[Match]: ...

    async def get_by_id(self, match_id: str) -> Optional[Match]: ...

    async def create(self, match: Match) -> Match: ...

    async def exists(self, user_a_id: str, user_b_id: str) -> bool: ...


class MessageRepository(Protocol):
    async def get_by_match(self, match_id: str) -> list[Mensaje]: ...

    async def create(self, mensaje: Mensaje) -> Mensaje: ...


class CotizacionRepository(Protocol):
    async def get_by_match(self, match_id: str) -> list[Cotizacion]: ...

    async def get_by_id(self, cotizacion_id: str) -> Optional[Cotizacion]: ...

    async def create(self, cotizacion: Cotizacion) -> Cotizacion: ...

    async def update(self, cotizacion: Cotizacion) -> Cotizacion: ...
