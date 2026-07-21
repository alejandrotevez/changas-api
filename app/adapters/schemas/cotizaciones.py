from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


def _snake_to_camel(name: str) -> str:
    parts = name.split("_")
    return parts[0] + "".join(p.capitalize() for p in parts[1:])


class CotizacionRequest(BaseModel):
    monto_estimado: float = Field(alias="montoEstimado", gt=0)
    detalle: str = Field(..., min_length=1)
    fecha_disponible: str = Field(alias="fechaDisponible")

    model_config = ConfigDict(
        alias_generator=_snake_to_camel,
        populate_by_name=True,
    )


class CotizacionResponse(BaseModel):
    id: str
    match_id: str = Field(alias="matchId")
    monto_estimado: float = Field(alias="montoEstimado")
    detalle: str
    fecha_disponible: str = Field(alias="fechaDisponible")
    estado: str
    creado_en: datetime = Field(alias="creadoEn")

    model_config = ConfigDict(
        alias_generator=_snake_to_camel,
        populate_by_name=True,
    )
