from datetime import datetime

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
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class PreferenciaNotificacion(Base):
    """Consentimiento y preferencias de contacto por WhatsApp."""

    __tablename__ = "preferencias_notificacion"

    __table_args__ = (
        CheckConstraint(
            "tipo_destinatario IN ('ASESOR', 'CLIENTE', 'SUPERVISOR', 'USUARIO')",
            name="ck_preferencias_tipo_destinatario",
        ),
        UniqueConstraint(
            "tipo_destinatario",
            "asesor_id",
            "tercero_id",
            "telefono_whatsapp",
            name="uq_preferencia_notificacion_destinatario",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tipo_destinatario: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    asesor_id: Mapped[int | None] = mapped_column(
        ForeignKey("asesores.id", ondelete="CASCADE"), nullable=True, index=True
    )
    tercero_id: Mapped[int | None] = mapped_column(
        ForeignKey("terceros.id", ondelete="CASCADE"), nullable=True, index=True
    )
    telefono_whatsapp: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    acepta_whatsapp: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    whatsapp_activo: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )
    fecha_consentimiento: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    origen_consentimiento: Mapped[str | None] = mapped_column(String(100), nullable=True)
    fecha_retiro: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    motivo_retiro: Mapped[str | None] = mapped_column(String(250), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
