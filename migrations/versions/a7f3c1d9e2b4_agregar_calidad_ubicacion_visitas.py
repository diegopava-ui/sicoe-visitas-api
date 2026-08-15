"""agregar calidad de ubicacion a visitas

Revision ID: a7f3c1d9e2b4
Revises: c9d8a1f4e2b7
Create Date: 2026-08-12

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a7f3c1d9e2b4"
down_revision: Union[str, Sequence[str], None] = "c9d8a1f4e2b7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "visitas",
        sa.Column(
            "fuente_ubicacion",
            sa.String(length=20),
            server_default="SIN_VALIDAR",
            nullable=False,
        ),
    )
    op.add_column(
        "visitas",
        sa.Column(
            "ubicacion_validada",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
    )
    op.add_column(
        "visitas",
        sa.Column(
            "ubicacion_validada_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )
    op.add_column(
        "visitas",
        sa.Column(
            "ubicacion_validada_by",
            sa.Integer(),
            nullable=True,
        ),
    )

    op.create_check_constraint(
        "ck_visitas_fuente_ubicacion",
        "visitas",
        (
            "fuente_ubicacion IN "
            "('GPS', 'GEOCODIFICADA', 'MANUAL', 'SIN_VALIDAR')"
        ),
    )

    op.create_foreign_key(
        "fk_visitas_ubicacion_validada_by_usuarios",
        "visitas",
        "usuarios",
        ["ubicacion_validada_by"],
        ["id"],
    )

    op.create_index(
        op.f("ix_visitas_fuente_ubicacion"),
        "visitas",
        ["fuente_ubicacion"],
        unique=False,
    )

    op.create_index(
        op.f("ix_visitas_ubicacion_validada_by"),
        "visitas",
        ["ubicacion_validada_by"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_visitas_ubicacion_validada_by"),
        table_name="visitas",
    )
    op.drop_index(
        op.f("ix_visitas_fuente_ubicacion"),
        table_name="visitas",
    )

    op.drop_constraint(
        "fk_visitas_ubicacion_validada_by_usuarios",
        "visitas",
        type_="foreignkey",
    )

    op.drop_constraint(
        "ck_visitas_fuente_ubicacion",
        "visitas",
        type_="check",
    )

    op.drop_column("visitas", "ubicacion_validada_by")
    op.drop_column("visitas", "ubicacion_validada_at")
    op.drop_column("visitas", "ubicacion_validada")
    op.drop_column("visitas", "fuente_ubicacion")
