from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    func,
)


class Usuario(Base):
    __tablename__ = "usuarios"

    __table_args__ = (
        UniqueConstraint(
            "asesor_id",
            name="uq_usuarios_asesor",
        ),
        CheckConstraint(
            "rol IN ('ADMINISTRADOR', 'COORDINADOR', 'ASESOR')",
            name="ck_usuarios_rol",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    asesor_id: Mapped[int | None] = mapped_column(
        ForeignKey("asesores.id"),
        nullable=True,
        index=True,
    )

    username: Mapped[str] = mapped_column(
        String(80),
        nullable=False,
        unique=True,
        index=True,
    )

    email: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        unique=True,
        index=True,
    )

    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    rol: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="ASESOR",
        server_default="ASESOR",
    )

    activo: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )

    ultimo_acceso: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
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

    asesor = relationship(
        "Asesor",
        back_populates="usuario",
        lazy="selectin",
    )
   