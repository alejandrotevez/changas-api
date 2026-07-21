import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.framework.database import Base


def _uuid_hex() -> str:
    return uuid.uuid4().hex


class UserModel(Base):
    __tablename__ = "usuarios"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid_hex)
    nombre: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    google_id: Mapped[str] = mapped_column(String(255), nullable=True, unique=True, index=True)
    rol_actual: Mapped[str] = mapped_column(String(20), nullable=False, default="CLIENTE")
    tags: Mapped[str] = mapped_column(Text, nullable=False, default="[]")  # JSON array
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

    changa_posts = relationship("ChangaPostModel", back_populates="user", lazy="selectin")
    changador_perfil = relationship("ChangadorPerfilModel", back_populates="user", uselist=False, lazy="selectin")


class ChangaPostModel(Base):
    __tablename__ = "changas_posts"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid_hex)
    titulo: Mapped[str] = mapped_column(String(255), nullable=False)
    descripcion_corta: Mapped[str] = mapped_column(String(500), nullable=False)
    fotos: Mapped[str] = mapped_column(Text, nullable=False, default="[]")  # JSON array
    tags: Mapped[str] = mapped_column(Text, nullable=False, default="[]")  # JSON array
    barrio: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    user_id: Mapped[str] = mapped_column(String(32), ForeignKey("usuarios.id"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

    user = relationship("UserModel", back_populates="changa_posts")


class ChangadorPerfilModel(Base):
    __tablename__ = "changadores_perfiles"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid_hex)
    nombre: Mapped[str] = mapped_column(String(255), nullable=False)
    fotos_trabajos: Mapped[str] = mapped_column(Text, nullable=False, default="[]")  # JSON array
    especialidades: Mapped[str] = mapped_column(Text, nullable=False, default="[]")  # JSON array
    user_id: Mapped[str] = mapped_column(String(32), ForeignKey("usuarios.id"), nullable=False, unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

    user = relationship("UserModel", back_populates="changador_perfil")


class MatchModel(Base):
    __tablename__ = "matches"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid_hex)
    user_a_id: Mapped[str] = mapped_column(String(32), ForeignKey("usuarios.id"), nullable=False, index=True)
    user_b_id: Mapped[str] = mapped_column(String(32), ForeignKey("usuarios.id"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

    messages = relationship("MessageModel", back_populates="match", lazy="selectin")
    cotizaciones = relationship("CotizacionModel", back_populates="match", lazy="selectin")


class MessageModel(Base):
    __tablename__ = "mensajes"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid_hex)
    match_id: Mapped[str] = mapped_column(String(32), ForeignKey("matches.id"), nullable=False, index=True)
    autor_id: Mapped[str] = mapped_column(String(32), ForeignKey("usuarios.id"), nullable=False, index=True)
    texto: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

    match = relationship("MatchModel", back_populates="messages")


class CotizacionModel(Base):
    __tablename__ = "cotizaciones"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid_hex)
    match_id: Mapped[str] = mapped_column(String(32), ForeignKey("matches.id"), nullable=False, index=True)
    monto_estimado: Mapped[float] = mapped_column(Float, nullable=False)
    detalle: Mapped[str] = mapped_column(Text, nullable=False)
    fecha_disponible: Mapped[str] = mapped_column(String(20), nullable=False)
    estado: Mapped[str] = mapped_column(String(20), nullable=False, default="PENDIENTE")
    creado_por_id: Mapped[str] = mapped_column(String(32), ForeignKey("usuarios.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

    match = relationship("MatchModel", back_populates="cotizaciones")


class SwipeModel(Base):
    __tablename__ = "swipes"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid_hex)
    user_id: Mapped[str] = mapped_column(String(32), ForeignKey("usuarios.id"), nullable=False, index=True)
    item_id: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    liked: Mapped[bool] = mapped_column(Boolean, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
