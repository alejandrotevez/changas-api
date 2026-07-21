"""Test fixtures for changas-api integration tests."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import Settings
from app.framework.database import Base, get_db
from app.framework.models import (
    ChangaPostModel,
    ChangadorPerfilModel,
    UserModel,
)
from app.main import create_app
from app.usecases.auth import TokenService

# ---------------------------------------------------------------------------
# Test settings — in-memory SQLite
# ---------------------------------------------------------------------------

import os
import tempfile

TEST_SECRET = "test-secret-not-for-prod"
_TEST_DB_PATH = os.path.join(tempfile.gettempdir(), f"changas_test_{uuid.uuid4().hex}.db")
_DB_URL = f"sqlite+aiosqlite:///{_TEST_DB_PATH}"

TEST_SETTINGS = Settings(
    DATABASE_URL=_DB_URL,
    JWT_SECRET=TEST_SECRET,
    GOOGLE_CLIENT_ID="test-google-client-id",
)

_test_engine = create_async_engine(_DB_URL, echo=False)
_test_session_factory = async_sessionmaker(
    _test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@pytest_asyncio.fixture(loop_scope="function")
async def _setup_db():
    """Create all tables before each test, drop after."""
    async with _test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with _test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    # Clean up the test DB file
    try:
        os.remove(_TEST_DB_PATH)
    except OSError:
        pass


async def _override_get_db() -> AsyncGenerator[AsyncSession, None]:
    async with _test_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# ---------------------------------------------------------------------------
# App + client
# ---------------------------------------------------------------------------


@pytest.fixture
def test_app():
    app = create_app(settings_override=TEST_SETTINGS)
    app.dependency_overrides[get_db] = _override_get_db
    return app


@pytest_asyncio.fixture(loop_scope="function")
async def async_client(test_app, _setup_db):
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest_asyncio.fixture(loop_scope="function")
async def db_session(_setup_db):
    """Fixture for seeding test data.
    
    Uses a separate session from the app's request session, but since they
    share the same engine (in-memory SQLite with aiosqlite), committed data
    is visible to both. The caller MUST ensure data is committed before the
    test runs — seed fixture functions call commit() when done.
    """
    session = _test_session_factory()
    try:
        yield session
    finally:
        await session.close()


# ---------------------------------------------------------------------------
# Token service
# ---------------------------------------------------------------------------


@pytest.fixture
def token_service():
    return TokenService(secret_override=TEST_SECRET)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _uuid() -> str:
    return uuid.uuid4().hex


# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------


async def _insert_user(session: AsyncSession, **overrides) -> UserModel:
    defaults = dict(
        id=_uuid(),
        nombre="Test User",
        email=f"test{_uuid()[:6]}@example.com",
        password_hash="$2b$12$2Nt0XI8aeboPRX6po0rE7enR8B26T/YXuTtlIcKBvnD38yiVhOb4m",
        google_id=None,
        rol_actual="CLIENTE",
        tags="[]",
        created_at=datetime.now(timezone.utc),
    )
    defaults.update(overrides)
    model = UserModel(**defaults)
    session.add(model)
    await session.commit()
    return model


async def _insert_changa_post(session: AsyncSession, **overrides) -> ChangaPostModel:
    defaults = dict(
        id=_uuid(),
        titulo="Caño roto",
        descripcion_corta="Arreglo urgente",
        fotos="[]",
        tags='["#Plomero"]',
        barrio="Villa Urquiza",
        user_id="",
        created_at=datetime.now(timezone.utc),
    )
    defaults.update(overrides)
    model = ChangaPostModel(**defaults)
    session.add(model)
    await session.commit()
    return model


async def _insert_changador_perfil(
    session: AsyncSession, **overrides
) -> ChangadorPerfilModel:
    defaults = dict(
        id=_uuid(),
        nombre="Roberto Gómez",
        fotos_trabajos="[]",
        especialidades='["Plomería"]',
        user_id="",
        created_at=datetime.now(timezone.utc),
    )
    defaults.update(overrides)
    model = ChangadorPerfilModel(**defaults)
    session.add(model)
    await session.commit()
    return model


# ---------------------------------------------------------------------------
# Composite fixtures
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture(loop_scope="function")
async def cliente_user(db_session: AsyncSession) -> UserModel:
    user = await _insert_user(
        db_session,
        id="cliente-001",
        email="cliente@test.com",
        password_hash="$2b$12$2Nt0XI8aeboPRX6po0rE7enR8B26T/YXuTtlIcKBvnD38yiVhOb4m",
        rol_actual="CLIENTE",
        tags='["#Cliente"]',
    )
    await db_session.commit()
    return user


@pytest_asyncio.fixture(loop_scope="function")
async def changador_user(db_session: AsyncSession) -> UserModel:
    user = await _insert_user(
        db_session,
        id="changador-001",
        email="changador@test.com",
        password_hash="$2b$12$2Nt0XI8aeboPRX6po0rE7enR8B26T/YXuTtlIcKBvnD38yiVhOb4m",
        rol_actual="CHANGADOR",
        tags='["#GasistaMatriculado"]',
    )
    await db_session.commit()
    return user


@pytest_asyncio.fixture
async def auth_header_cliente(
    cliente_user: UserModel,
    token_service: TokenService,
) -> dict[str, str]:
    token = token_service.encode(cliente_user.id, cliente_user.email)
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def auth_header_changador(
    changador_user: UserModel,
    token_service: TokenService,
) -> dict[str, str]:
    token = token_service.encode(changador_user.id, changador_user.email)
    return {"Authorization": f"Bearer {token}"}
