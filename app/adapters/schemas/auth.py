from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict


def _snake_to_camel(name: str) -> str:
    parts = name.split("_")
    return parts[0] + "".join(p.capitalize() for p in parts[1:])


class LoginRequest(BaseModel):
    email: str
    password: str

    model_config = ConfigDict(
        alias_generator=_snake_to_camel,
        populate_by_name=True,
    )


class GoogleLoginRequest(BaseModel):
    id_token: str

    model_config = ConfigDict(
        alias_generator=_snake_to_camel,
        populate_by_name=True,
    )


class UsuarioResponse(BaseModel):
    id: str
    nombre: str
    email: str
    rol_actual: str
    tags: list[str]

    model_config = ConfigDict(
        alias_generator=_snake_to_camel,
        populate_by_name=True,
        from_attributes=True,
    )


class LoginResponse(BaseModel):
    usuario: UsuarioResponse
    token: str

    model_config = ConfigDict(
        alias_generator=_snake_to_camel,
        populate_by_name=True,
    )


class UpdateUserRequest(BaseModel):
    rol_actual: Optional[Literal["CLIENTE", "CHANGADOR"]] = None
    tags: Optional[list[str]] = None

    model_config = ConfigDict(
        alias_generator=_snake_to_camel,
        populate_by_name=True,
    )
