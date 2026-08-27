from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class UsuarioCertificadoArl(Base):
    __tablename__ = "usuario_certificados_arl"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    usuario_id: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id"),
        nullable=False,
        index=True,
    )

    nombre_archivo: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    url_archivo: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    fecha_vigencia: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    activo: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )

    created_by: Mapped[int | None] = mapped_column(
        ForeignKey("usuarios.id"),
        nullable=True,
        index=True,
    )

    updated_by: Mapped[int | None] = mapped_column(
        ForeignKey("usuarios.id"),
        nullable=True,
        index=True,
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

    # Relación de un solo sentido: no requiere modificar
    # app/models/usuario.py ni agregar back_populates ahí.
    usuario = relationship(
        "Usuario",
        foreign_keys=[usuario_id],
        lazy="selectin",
    )
