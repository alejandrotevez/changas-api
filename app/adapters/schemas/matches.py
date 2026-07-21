from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.adapters.schemas.feed import FeedItemResponse


def _snake_to_camel(name: str) -> str:
    parts = name.split("_")
    return parts[0] + "".join(p.capitalize() for p in parts[1:])


class MatchResponse(BaseModel):
    id: str
    item: FeedItemResponse
    creado_en: datetime = Field(alias="creadoEn")
    ultimo_mensaje: Optional[str] = Field(
        alias="ultimoMensaje", default=None
    )

    model_config = ConfigDict(
        alias_generator=_snake_to_camel,
        populate_by_name=True,
    )
