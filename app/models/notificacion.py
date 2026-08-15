from datetime import datetime
from typing import Any

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Notificacion(Base):
    """Registro auditable de una notificación saliente o entrante."""

    __tablename__ = "notificaciones"

    __table_args__ = (
        CheckConstraint(
            "canal IN ('WHATSAPP', 'EMAIL', 'SMS', 'PUSH')",
            name="ck_notificaciones_canal",
        ),
        CheckConstraint(
            "tipo_destinatario IN ('ASESOR', 'CLIENTE', 'SUPERVISOR', 'USUARIO')",
            name="ck_notificaciones_tipo_destinatario",
        ),
        CheckConstraint(
            "estado IN ('PENDIENTE', 'SIMULADA', 'PROCESANDO', 'ENVIADA', "
            "'ENTREGADA', 'LEIDA', 'RESPONDIDA', 'FALLIDA', 'CANCELADA')",
            name="ck_notificaciones_estado",
        ),
        CheckConstraint("intentos >= 0", name="ck_notificaciones_intentos"),
        UniqueConstraint(
            "clave_idempotencia",
            name="uq_notificaciones_clave_idempotencia",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    visita_id: Mapped[int | None] = mapped_column(
        ForeignKey("visitas.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    asesor_id: Mapped[int | None] = mapped_column(
        ForeignKey("asesores.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    tercero_id: Mapped[int | None] = mapped_column(
        ForeignKey("terceros.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    canal: Mapped[str] = mapped_column(
        String(20), nullable=False, default="WHATSAPP", server_default="WHATSAPP", index=True
    )
    tipo_destinatario: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    telefono_destino: Mapped[str | None] = mapped_column(String(30), nullable=True, index=True)
    email_destino: Mapped[str | None] = mapped_column(String(150), nullable=True)
    plantilla: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    datos_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    mensaje_renderizado: Mapped[str | None] = mapped_column(Text, nullable=True)

    fecha_programada: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    fecha_envio: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    fecha_entrega: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    fecha_lectura: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    fecha_respuesta: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    estado: Mapped[str] = mapped_column(
        String(20), nullable=False, default="PENDIENTE", server_default="PENDIENTE", index=True
    )
    intentos: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    proveedor: Mapped[str | None] = mapped_column(String(50), nullable=True)
    proveedor_message_id: Mapped[str | None] = mapped_column(String(180), nullable=True, index=True)
    clave_idempotencia: Mapped[str] = mapped_column(String(180), nullable=False)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    respuesta: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
