"""crear modulo notificaciones whatsapp

Revision ID: c9d8a1f4e2b7
Revises: a17844fe1898
Create Date: 2026-08-02 22:15:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "c9d8a1f4e2b7"
down_revision: Union[str, Sequence[str], None] = "a17844fe1898"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "preferencias_notificacion",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tipo_destinatario", sa.String(length=20), nullable=False),
        sa.Column("asesor_id", sa.Integer(), nullable=True),
        sa.Column("tercero_id", sa.Integer(), nullable=True),
        sa.Column("telefono_whatsapp", sa.String(length=30), nullable=False),
        sa.Column("acepta_whatsapp", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("whatsapp_activo", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("fecha_consentimiento", sa.DateTime(timezone=True), nullable=True),
        sa.Column("origen_consentimiento", sa.String(length=100), nullable=True),
        sa.Column("fecha_retiro", sa.DateTime(timezone=True), nullable=True),
        sa.Column("motivo_retiro", sa.String(length=250), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint(
            "tipo_destinatario IN ('ASESOR', 'CLIENTE', 'SUPERVISOR', 'USUARIO')",
            name="ck_preferencias_tipo_destinatario",
        ),
        sa.ForeignKeyConstraint(["asesor_id"], ["asesores.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tercero_id"], ["terceros.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "tipo_destinatario", "asesor_id", "tercero_id", "telefono_whatsapp",
            name="uq_preferencia_notificacion_destinatario",
        ),
    )
    op.create_index("ix_preferencias_notificacion_asesor_id", "preferencias_notificacion", ["asesor_id"])
    op.create_index("ix_preferencias_notificacion_tercero_id", "preferencias_notificacion", ["tercero_id"])
    op.create_index("ix_preferencias_notificacion_telefono_whatsapp", "preferencias_notificacion", ["telefono_whatsapp"])
    op.create_index("ix_preferencias_notificacion_tipo_destinatario", "preferencias_notificacion", ["tipo_destinatario"])

    op.create_table(
        "notificaciones",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("visita_id", sa.Integer(), nullable=True),
        sa.Column("asesor_id", sa.Integer(), nullable=True),
        sa.Column("tercero_id", sa.Integer(), nullable=True),
        sa.Column("canal", sa.String(length=20), server_default="WHATSAPP", nullable=False),
        sa.Column("tipo_destinatario", sa.String(length=20), nullable=False),
        sa.Column("telefono_destino", sa.String(length=30), nullable=True),
        sa.Column("email_destino", sa.String(length=150), nullable=True),
        sa.Column("plantilla", sa.String(length=120), nullable=False),
        sa.Column("datos_json", sa.JSON(), nullable=False),
        sa.Column("mensaje_renderizado", sa.Text(), nullable=True),
        sa.Column("fecha_programada", sa.DateTime(timezone=True), nullable=False),
        sa.Column("fecha_envio", sa.DateTime(timezone=True), nullable=True),
        sa.Column("fecha_entrega", sa.DateTime(timezone=True), nullable=True),
        sa.Column("fecha_lectura", sa.DateTime(timezone=True), nullable=True),
        sa.Column("fecha_respuesta", sa.DateTime(timezone=True), nullable=True),
        sa.Column("estado", sa.String(length=20), server_default="PENDIENTE", nullable=False),
        sa.Column("intentos", sa.Integer(), server_default="0", nullable=False),
        sa.Column("proveedor", sa.String(length=50), nullable=True),
        sa.Column("proveedor_message_id", sa.String(length=180), nullable=True),
        sa.Column("clave_idempotencia", sa.String(length=180), nullable=False),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("respuesta", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("canal IN ('WHATSAPP', 'EMAIL', 'SMS', 'PUSH')", name="ck_notificaciones_canal"),
        sa.CheckConstraint("estado IN ('PENDIENTE', 'SIMULADA', 'PROCESANDO', 'ENVIADA', 'ENTREGADA', 'LEIDA', 'RESPONDIDA', 'FALLIDA', 'CANCELADA')", name="ck_notificaciones_estado"),
        sa.CheckConstraint("intentos >= 0", name="ck_notificaciones_intentos"),
        sa.CheckConstraint("tipo_destinatario IN ('ASESOR', 'CLIENTE', 'SUPERVISOR', 'USUARIO')", name="ck_notificaciones_tipo_destinatario"),
        sa.ForeignKeyConstraint(["asesor_id"], ["asesores.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["tercero_id"], ["terceros.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["visita_id"], ["visitas.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("clave_idempotencia", name="uq_notificaciones_clave_idempotencia"),
    )
    for column in ["asesor_id", "canal", "estado", "fecha_programada", "plantilla", "proveedor_message_id", "telefono_destino", "tercero_id", "tipo_destinatario", "visita_id"]:
        op.create_index(f"ix_notificaciones_{column}", "notificaciones", [column])


def downgrade() -> None:
    op.drop_table("notificaciones")
    op.drop_table("preferencias_notificacion")
