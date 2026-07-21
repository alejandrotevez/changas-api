from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict


def _snake_to_camel(name: str) -> str:
    parts = name.split("_")
    return parts[0] + "".join(p.capitalize() for p in parts[1:])


class SwipeRequest(BaseModel):
    item_id: str
    liked: bool

    model_config = ConfigDict(
        alias_generator=_snake_to_camel,
        populate_by_name=True,
    )


class SwipeResponse(BaseModel):
    es_match: bool
    match_id: Optional[str] = None

    model_config = ConfigDict(
        alias_generator=_snake_to_camel,
        populate_by_name=True,
    )
