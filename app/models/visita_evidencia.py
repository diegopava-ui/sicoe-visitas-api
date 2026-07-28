from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class VisitaEvidencia(Base):
    __tablename__ = "visita_evidencias"

    __table_args__ = (
        CheckConstraint(
            """
            tipo_archivo IN (
                'FOTO',
                'PDF',
                'VIDEO',
                'AUDIO',
                'OTRO'
            )
            """,
            name="ck_visita_evidencia_tipo",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    visita_id: Mapped[int] = mapped_column(
        ForeignKey("visitas.id"),
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

    tipo_archivo: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    descripcion: Mapped[str | None] = mapped_column(
        Text,
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

    visita = relationship(
        "Visita",
        back_populates="evidencias",
        lazy="selectin",
    )