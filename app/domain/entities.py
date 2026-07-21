from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class Usuario:
    id: str
    nombre: str
    email: str
    password_hash: str
    google_id: Optional[str] = None
    rol_actual: str = "CLIENTE"  # CLIENTE | CHANGADOR
    tags: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass(frozen=True)
class ChangaPost:
    id: str
    titulo: str
    descripcion_corta: str
    fotos: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    barrio: str = ""
    user_id: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass(frozen=True)
class ChangadorPerfil:
    id: str
    nombre: str
    fotos_trabajos: list[str] = field(default_factory=list)
    especialidades: list[str] = field(default_factory=list)
    user_id: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass(frozen=True)
class Match:
    id: str
    user_a_id: str
    user_b_id: str
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass(frozen=True)
class Mensaje:
    id: str
    match_id: str
    autor_id: str
    texto: str
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass(frozen=True)
class Cotizacion:
    id: str
    match_id: str
    monto_estimado: float
    detalle: str
    fecha_disponible: str
    estado: str = "PENDIENTE"  # PENDIENTE | ACEPTADA | RECHAZADA
    creado_por_id: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass(frozen=True)
class Swipe:
    id: str
    user_id: str
    item_id: str
    liked: bool
    created_at: datetime = field(default_factory=datetime.utcnow)
