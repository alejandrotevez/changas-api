from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


def _snake_to_camel(name: str) -> str:
    parts = name.split("_")
    return parts[0] + "".join(p.capitalize() for p in parts[1:])


class SendMessageRequest(BaseModel):
    texto: str = Field(..., min_length=1, max_length=2000)

    model_config = ConfigDict(
        alias_generator=_snake_to_camel,
        populate_by_name=True,
    )


class MessageResponse(BaseModel):
    id: str
    autor_id: str = Field(alias="autorId")
    texto: str
    enviado_en: datetime = Field(alias="enviadoEn")

    model_config = ConfigDict(
        alias_generator=_snake_to_camel,
        populate_by_name=True,
    )
