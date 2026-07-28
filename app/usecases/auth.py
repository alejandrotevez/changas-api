from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import bcrypt as _bcrypt
import jwt

from typing import Optional

from app.config import Settings, settings
from app.domain.entities import Usuario
from app.domain.exceptions import AuthenticationError
from app.domain.interfaces import UserRepository

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class LoginResult:
    usuario: Usuario
    token: str


class TokenService:
    """JWT encode/decode helper.

    Stateless — one instance is safe to reuse across the app.
    """

    def __init__(
        self,
        secret_override: Optional[str] = None,
        settings_override: Optional[Settings] = None,
    ) -> None:
        self._secret = secret_override
        self._settings = settings_override

    @property
    def _cfg(self) -> Settings:
        return self._settings or settings

    def encode(self, user_id: str, email: str) -> str:
        secret = self._secret or self._cfg.JWT_SECRET
        payload = {
            "sub": user_id,
            "email": email,
            "iat": datetime.now(timezone.utc),
            "exp": datetime.now(timezone.utc) + timedelta(minutes=self._cfg.JWT_EXPIRATION_MINUTES),
        }
        return jwt.encode(payload, secret, algorithm=self._cfg.JWT_ALGORITHM)

    def decode(self, token: str) -> dict:
        secret = self._secret or self._cfg.JWT_SECRET
        return jwt.decode(
            token,
            secret,
            algorithms=[self._cfg.JWT_ALGORITHM],
        )


class LoginUseCase:
    """Authenticate users via email+password or Google sign-in."""

    def __init__(
        self,
        user_repo: UserRepository,
        token_service: TokenService,
    ) -> None:
        self._user_repo = user_repo
        self._token_service = token_service

    async def execute_email(self, email: str, password: str) -> LoginResult:
        user = await self._user_repo.get_by_email(email)

        if user is None or not user.password_hash:
            # Constant-time dummy check to prevent timing-based user enumeration.
            # Always call checkpw regardless of whether the user exists.
            _bcrypt.checkpw(
                password.encode(),
                b"$2b$12$2Nt0XI8aeboPRX6po0rE7enR8B26T/YXuTtlIcKBvnD38yiVhOb4m",
            )
            raise AuthenticationError("Invalid email or password")

        if not _bcrypt.checkpw(password.encode(), user.password_hash.encode()):
            raise AuthenticationError("Invalid email or password")

        token = self._token_service.encode(user.id, user.email)
        return LoginResult(usuario=user, token=token)

    async def execute_google(self, id_token_str: str) -> LoginResult:
        from google.auth.transport import requests
        from google.oauth2 import id_token as google_id_token

        try:
            info = google_id_token.verify_oauth2_token(
                id_token_str,
                requests.Request(),
                settings.GOOGLE_CLIENT_ID,
            )
        except ValueError as exc:
            logger.warning("Google token verification failed", exc_info=True)
            raise AuthenticationError("Invalid Google id token") from exc

        google_id = info.get("sub")
        email = info.get("email")
        if not email:
            raise AuthenticationError("Google token missing email")

        # Look up existing user by google_id first, then by email
        user = await self._user_repo.get_by_google_id(google_id)
        if user is None:
            user = await self._user_repo.get_by_email(email)

        if user is None:
            # Create a new user from Google profile data
            nombre = info.get("name") or email.split("@")[0]
            user = Usuario(
                id=uuid.uuid4().hex,
                nombre=nombre,
                email=email,
                password_hash="",
                google_id=google_id,
                rol_actual="CLIENTE",
                tags=[],
                created_at=datetime.now(timezone.utc),
            )
            user = await self._user_repo.create(user)

        token = self._token_service.encode(user.id, user.email)
        return LoginResult(usuario=user, token=token)
