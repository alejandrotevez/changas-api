from __future__ import annotations

from typing import Annotated, Literal, Union

from pydantic import BaseModel, ConfigDict, Field


def _snake_to_camel(name: str) -> str:
    parts = name.split("_")
    return parts[0] + "".join(p.capitalize() for p in parts[1:])


class ChangaPostResponse(BaseModel):
    tipo: Literal["CHANGA"] = "CHANGA"
    id: str
    fotos: list[str]
    titulo: str
    descripcion_corta: str
    tags: list[str]
    barrio: str

    model_config = ConfigDict(
        alias_generator=_snake_to_camel,
        populate_by_name=True,
        from_attributes=True,
    )


class ChangadorPerfilResponse(BaseModel):
    tipo: Literal["CHANGADOR_PERFIL"] = "CHANGADOR_PERFIL"
    id: str
    fotos_trabajos: list[str]
    nombre: str
    especialidades: list[str]

    model_config = ConfigDict(
        alias_generator=_snake_to_camel,
        populate_by_name=True,
        from_attributes=True,
    )


FeedItemResponse = Annotated[
    Union[ChangaPostResponse, ChangadorPerfilResponse],
    Field(discriminator="tipo"),
]
