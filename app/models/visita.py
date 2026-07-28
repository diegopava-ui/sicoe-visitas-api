from datetime import date, datetime, time
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    Time,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Visita(Base):
    __tablename__ = "visitas"

    __table_args__ = (
        CheckConstraint(
            """
            tipo_visita IN (
                'CAPACITACION',
                'RECAPACITACION',
                'IMPLEMENTACION',
                'SOPORTE',
                'SEGUIMIENTO',
                'COMERCIAL',
                'LEVANTAMIENTO',
                'OTRA'
            )
            """,
            name="ck_visitas_tipo_visita",
        ),
        CheckConstraint(
            """
            estado IN (
                'PROGRAMADA',
                'EN_PROCESO',
                'FINALIZADA',
                'CANCELADA'
            )
            """,
            name="ck_visitas_estado",
        ),
        CheckConstraint(
            """
            origen_registro IN (
                'WEB',
                'MOVIL',
                'API'
            )
            """,
            name="ck_visitas_origen_registro",
        ),
        CheckConstraint(
            """
            hora_fin IS NULL
            OR hora_inicio IS NULL
            OR hora_fin >= hora_inicio
            """,
            name="ck_visitas_rango_horas",
        ),
        CheckConstraint(
            "latitud IS NULL OR latitud BETWEEN -90 AND 90",
            name="ck_visitas_latitud",
        ),
        CheckConstraint(
            "longitud IS NULL OR longitud BETWEEN -180 AND 180",
            name="ck_visitas_longitud",
        ),
        CheckConstraint(
            """
            cantidad_participantes IS NULL
            OR cantidad_participantes >= 0
            """,
            name="ck_visitas_cantidad_participantes",
        ),
        CheckConstraint(
            """
            duracion_minutos IS NULL
            OR duracion_minutos >= 0
            """,
            name="ck_visitas_duracion_minutos",
        ),
        CheckConstraint(
            """
            nivel_satisfaccion IS NULL
            OR nivel_satisfaccion IN (
                'EXCELENTE',
                'BUENO',
                'REGULAR',
                'MALO'
            )
            """,
            name="ck_visitas_nivel_satisfaccion",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    asesor_id: Mapped[int] = mapped_column(
        ForeignKey("asesores.id"),
        nullable=False,
        index=True,
    )

    tercero_id: Mapped[int | None] = mapped_column(
        ForeignKey("terceros.id"),
        nullable=True,
        index=True,
    )

    fecha_visita: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )

    hora_inicio: Mapped[time | None] = mapped_column(
        Time,
        nullable=True,
    )

    hora_fin: Mapped[time | None] = mapped_column(
        Time,
        nullable=True,
    )

    empresa: Mapped[str] = mapped_column(
        String(180),
        nullable=False,
        index=True,
    )

    nit: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
        index=True,
    )

    ciudad: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    departamento: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    direccion: Mapped[str | None] = mapped_column(
        String(220),
        nullable=True,
    )

    contacto_nombre: Mapped[str | None] = mapped_column(
        String(180),
        nullable=True,
    )

    cargo_contacto: Mapped[str | None] = mapped_column(
        String(120),
        nullable=True,
    )

    telefono_contacto: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )

    email_contacto: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    servicio: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
        index=True,
    )

    tipo_visita: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        index=True,
    )

    estado: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="PROGRAMADA",
        server_default="PROGRAMADA",
        index=True,
    )

    origen_registro: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="WEB",
        server_default="WEB",
    )

    cantidad_participantes: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    duracion_minutos: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    objetivo: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    desarrollo: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    resultado: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    compromisos: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    observaciones: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    nivel_satisfaccion: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        index=True,
    )

    proxima_visita: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    latitud: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 7),
        nullable=True,
    )

    longitud: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 7),
        nullable=True,
    )

    firma_cliente_url: Mapped[str | None] = mapped_column(
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

    tercero = relationship(
        "Tercero",
        back_populates="visitas",
        lazy="selectin",
    )

    asesor = relationship(
        "Asesor",
        back_populates="visitas",
        lazy="selectin",
    )

    evidencias = relationship(
        "VisitaEvidencia",
        back_populates="visita",
        lazy="selectin",
    )

    usuario_creador = relationship(
        "Usuario",
        foreign_keys=[created_by],
        back_populates="visitas_creadas",
        lazy="selectin",
    )

    usuario_modificador = relationship(
        "Usuario",
        foreign_keys=[updated_by],
        back_populates="visitas_modificadas",
        lazy="selectin",
    )