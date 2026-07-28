from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

from sqlalchemy.orm import Mapped, mapped_column, relationship

class Tercero(Base):
    __tablename__ = "terceros"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    tipo_tercero: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="cliente",
        index=True,
    )

    tipo_identificacion: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="NIT",
    )

    identificacion: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        unique=True,
        index=True,
    )

    razon_social: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        index=True,
    )

    nombre_comercial: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )

    email: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    telefono: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )

    direccion: Mapped[str | None] = mapped_column(
        String(250),
        nullable=True,
    )

    ciudad: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    departamento: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    contacto_nombre: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    contacto_email: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    contacto_telefono: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )

    observaciones: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    activo: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    visitas = relationship(
        "Visita",
        back_populates="tercero",
        lazy="selectin",
    )