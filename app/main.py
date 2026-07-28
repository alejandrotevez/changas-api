from __future__ import annotations

from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

from app.adapters.middleware.security import SecurityHeadersMiddleware
from app.adapters.routers import auth, chat, cotizaciones, feed, matches
from app.config import Settings, settings
from app.framework.database import init_db
from app.limiter import limiter


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    await init_db()
    yield


def create_app(settings_override: Optional[Settings] = None) -> FastAPI:
    if settings_override is not None:
        import app.config as config_module

        config_module.settings = settings_override
        cfg = settings_override
    else:
        cfg = settings

    app = FastAPI(
        title="Changas API",
        version="0.1.0",
        lifespan=lifespan,
    )

    # Rate limiting
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore[arg-type]
    app.add_middleware(SlowAPIMiddleware)

    # CORS — whitelist from settings
    origins = [o.strip() for o in cfg.CORS_ORIGINS.split(",") if o.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Security headers
    app.add_middleware(SecurityHeadersMiddleware)

    app.include_router(auth.router, prefix="/v1")
    app.include_router(feed.router, prefix="/v1")
    app.include_router(matches.router, prefix="/v1")
    app.include_router(chat.router, prefix="/v1")
    app.include_router(cotizaciones.router, prefix="/v1")

    @app.get("/v1/health", tags=["health"])
    async def health():
        return {"status": "ok", "version": "0.1.0"}

    return app


app = create_app()
