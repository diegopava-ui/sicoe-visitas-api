from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

from sqlalchemy.orm import Mapped, mapped_column, relationship


class Asesor(Base):
    __tablename__ = "asesores"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    identificacion: Mapped[str] = mapped_column(
        String(30),
        unique=True,
        nullable=False,
    )

    primer_nombre: Mapped[str] = mapped_column(
        String(80),
        nullable=False,
    )

    segundo_nombre: Mapped[str | None] = mapped_column(
        String(80),
        nullable=True,
    )

    primer_apellido: Mapped[str] = mapped_column(
        String(80),
        nullable=False,
    )

    segundo_apellido: Mapped[str | None] = mapped_column(
        String(80),
        nullable=True,
    )

    email: Mapped[str] = mapped_column(
        String(150),
        unique=True,
        nullable=False,
    )

    telefono: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )

    cargo: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    activo: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    usuario = relationship(
    "Usuario",
    back_populates="asesor",
    uselist=False,
    lazy="selectin",
)