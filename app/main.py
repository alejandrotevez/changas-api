from __future__ import annotations

from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.adapters.routers import auth, chat, cotizaciones, feed, matches
from app.config import Settings
from app.framework.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    await init_db()
    yield


def create_app(settings_override: Optional[Settings] = None) -> FastAPI:
    if settings_override is not None:
        import app.config as config_module

        config_module.settings = settings_override

    app = FastAPI(
        title="Changas API",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(auth.router, prefix="/v1")
    app.include_router(feed.router, prefix="/v1")
    app.include_router(matches.router, prefix="/v1")
    app.include_router(chat.router, prefix="/v1")
    app.include_router(cotizaciones.router, prefix="/v1")

    @app.get("/v1/health", tags=["health"])
    async def health():
        return {"status": "ok", "version": "0.1.0"}

    return app

    return app


app = create_app()
