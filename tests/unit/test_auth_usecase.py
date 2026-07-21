"""Unit tests for auth use cases."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock

import jwt
import pytest

from app.domain.entities import Usuario
from app.domain.exceptions import AuthenticationError
from app.usecases.auth import LoginUseCase, TokenService

TEST_SECRET = "test-secret-for-unit-tests"
BCRYPT_HASH = "$2b$12$qjn6joQCb1c0ahEpnW18re7brMZYOtfmrpb6lwFEB8kbw1akkzmmq"


class TestTokenService:
    def test_token_encode_decode(self) -> None:
        svc = TokenService(secret_override=TEST_SECRET)
        token = svc.encode("user-1", "test@example.com")
        payload = svc.decode(token)
        assert payload["sub"] == "user-1"
        assert payload["email"] == "test@example.com"

    def test_token_expired(self) -> None:
        now = datetime.now(timezone.utc)
        payload = {
            "sub": "user-1",
            "email": "test@example.com",
            "iat": now - timedelta(hours=2),
            "exp": now - timedelta(hours=1),
        }
        token = jwt.encode(payload, TEST_SECRET, algorithm="HS256")
        svc = TokenService(secret_override=TEST_SECRET)
        with pytest.raises(jwt.ExpiredSignatureError):
            svc.decode(token)


class TestLoginEmail:
    @pytest.mark.asyncio
    async def test_login_email_success(self) -> None:
        user = Usuario(
            id="user-1",
            nombre="Test User",
            email="test@example.com",
            password_hash=BCRYPT_HASH,
        )
        user_repo = AsyncMock()
        user_repo.get_by_email = AsyncMock(return_value=user)

        token_svc = TokenService(secret_override=TEST_SECRET)
        uc = LoginUseCase(user_repo=user_repo, token_service=token_svc)

        result = await uc.execute_email("test@example.com", "test-password")
        assert result.usuario == user
        payload = token_svc.decode(result.token)
        assert payload["sub"] == "user-1"
        assert payload["email"] == "test@example.com"

    @pytest.mark.asyncio
    async def test_login_email_unknown_user(self) -> None:
        user_repo = AsyncMock()
        user_repo.get_by_email = AsyncMock(return_value=None)

        uc = LoginUseCase(
            user_repo=user_repo,
            token_service=TokenService(secret_override=TEST_SECRET),
        )
        with pytest.raises(AuthenticationError, match="Invalid email or password"):
            await uc.execute_email("unknown@example.com", "any-password")

    @pytest.mark.asyncio
    async def test_login_email_wrong_password(self) -> None:
        user = Usuario(
            id="user-1",
            nombre="Test User",
            email="test@example.com",
            password_hash=BCRYPT_HASH,
        )
        user_repo = AsyncMock()
        user_repo.get_by_email = AsyncMock(return_value=user)

        uc = LoginUseCase(
            user_repo=user_repo,
            token_service=TokenService(secret_override=TEST_SECRET),
        )
        with pytest.raises(AuthenticationError, match="Invalid email or password"):
            await uc.execute_email("test@example.com", "wrong-password")

    @pytest.mark.asyncio
    async def test_login_email_no_password_hash(self) -> None:
        user = Usuario(
            id="user-2",
            nombre="Google User",
            email="google@example.com",
            password_hash="",
            google_id="g123",
            rol_actual="CLIENTE",
        )
        user_repo = AsyncMock()
        user_repo.get_by_email = AsyncMock(return_value=user)

        uc = LoginUseCase(
            user_repo=user_repo,
            token_service=TokenService(secret_override=TEST_SECRET),
        )
        with pytest.raises(AuthenticationError, match="Invalid email or password"):
            await uc.execute_email("google@example.com", "any-password")
