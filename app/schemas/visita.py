from datetime import date, datetime, time
from decimal import Decimal
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
    model_validator,
)


TipoVisita = Literal[
    "CAPACITACION",
    "RECAPACITACION",
    "IMPLEMENTACION",
    "SOPORTE",
    "SEGUIMIENTO",
    "COMERCIAL",
    "LEVANTAMIENTO",
    "OTRA",
]

EstadoVisita = Literal[
    "PROGRAMADA",
    "EN_PROCESO",
    "FINALIZADA",
    "CANCELADA",
]

OrigenRegistro = Literal[
    "WEB",
    "MOVIL",
    "API",
]

NivelSatisfaccion = Literal[
    "EXCELENTE",
    "BUENO",
    "REGULAR",
    "MALO",
]


FuenteUbicacion = Literal[
    "GPS",
    "GEOCODIFICADA",
    "MANUAL",
    "SIN_VALIDAR",
]


class VisitaBase(BaseModel):
    asesor_id: int = Field(gt=0)
    tercero_id: int = Field(gt=0)

    fecha_visita: date
    hora_inicio: time | None = None
    hora_fin: time | None = None

    ciudad: str | None = Field(default=None, max_length=100)
    departamento: str | None = Field(default=None, max_length=100)
    direccion: str | None = Field(default=None, max_length=220)

    contacto_nombre: str | None = Field(default=None, max_length=180)
    cargo_contacto: str | None = Field(default=None, max_length=120)
    telefono_contacto: str | None = Field(default=None, max_length=30)
    email_contacto: EmailStr | None = None

    servicio: str = Field(min_length=2, max_length=120)
    tipo_visita: TipoVisita

    estado: EstadoVisita = "PROGRAMADA"
    origen_registro: OrigenRegistro = "WEB"

    cantidad_participantes: int | None = Field(default=None, ge=0)
    duracion_minutos: int | None = Field(default=None, ge=0)

    objetivo: str | None = None
    desarrollo: str | None = None
    resultado: str | None = None
    compromisos: str | None = None
    observaciones: str | None = None

    nivel_satisfaccion: NivelSatisfaccion | None = None
    proxima_visita: date | None = None

    latitud: Decimal | None = Field(
        default=None,
        ge=Decimal("-90"),
        le=Decimal("90"),
        max_digits=10,
        decimal_places=7,
    )

    longitud: Decimal | None = Field(
        default=None,
        ge=Decimal("-180"),
        le=Decimal("180"),
        max_digits=10,
        decimal_places=7,
    )

    firma_cliente_url: str | None = None
    activo: bool = True

    @field_validator(
        "ciudad",
        "departamento",
        "direccion",
        "contacto_nombre",
        "cargo_contacto",
        "telefono_contacto",
        "servicio",
        mode="before",
    )
    @classmethod
    def limpiar_textos(
        cls,
        valor: str | None,
    ) -> str | None:
        if valor is None:
            return None

        valor_limpio = valor.strip()

        if not valor_limpio:
            return None

        return valor_limpio

    @model_validator(mode="after")
    def validar_horario(self) -> "VisitaBase":
        if (
            self.hora_inicio is not None
            and self.hora_fin is not None
            and self.hora_fin < self.hora_inicio
        ):
            raise ValueError(
                "La hora de finalización no puede ser anterior "
                "a la hora de inicio"
            )

        return self


class VisitaCrear(VisitaBase):
    pass


class VisitaActualizar(BaseModel):
    asesor_id: int | None = Field(default=None, gt=0)

    tercero_id: int | None = Field(default=None, gt=0)

    fecha_visita: date | None = None
    hora_inicio: time | None = None
    hora_fin: time | None = None

    ciudad: str | None = Field(default=None, max_length=100)
    departamento: str | None = Field(default=None, max_length=100)
    direccion: str | None = Field(default=None, max_length=220)

    contacto_nombre: str | None = Field(default=None, max_length=180)
    cargo_contacto: str | None = Field(default=None, max_length=120)
    telefono_contacto: str | None = Field(default=None, max_length=30)
    email_contacto: EmailStr | None = None

    servicio: str | None = Field(
        default=None,
        min_length=2,
        max_length=120,
    )
    tipo_visita: TipoVisita | None = None

    estado: EstadoVisita | None = None
    origen_registro: OrigenRegistro | None = None

    cantidad_participantes: int | None = Field(default=None, ge=0)
    duracion_minutos: int | None = Field(default=None, ge=0)

    objetivo: str | None = None
    desarrollo: str | None = None
    resultado: str | None = None
    compromisos: str | None = None
    observaciones: str | None = None

    nivel_satisfaccion: NivelSatisfaccion | None = None
    proxima_visita: date | None = None

    latitud: Decimal | None = Field(
        default=None,
        ge=Decimal("-90"),
        le=Decimal("90"),
        max_digits=10,
        decimal_places=7,
    )

    longitud: Decimal | None = Field(
        default=None,
        ge=Decimal("-180"),
        le=Decimal("180"),
        max_digits=10,
        decimal_places=7,
    )

    firma_cliente_url: str | None = None
    activo: bool | None = None

    @field_validator(
        "ciudad",
        "departamento",
        "direccion",
        "contacto_nombre",
        "cargo_contacto",
        "telefono_contacto",
        "servicio",
        mode="before",
    )
    @classmethod
    def limpiar_textos(
        cls,
        valor: str | None,
    ) -> str | None:
        if valor is None:
            return None

        valor_limpio = valor.strip()

        if not valor_limpio:
            return None

        return valor_limpio

    @model_validator(mode="after")
    def validar_horario(self) -> "VisitaActualizar":
        if (
            self.hora_inicio is not None
            and self.hora_fin is not None
            and self.hora_fin < self.hora_inicio
        ):
            raise ValueError(
                "La hora de finalización no puede ser anterior "
                "a la hora de inicio"
            )

        return self

class TerceroResumen(BaseModel):
    id: int
    identificacion: str
    razon_social: str
    nombre_comercial: str | None = None
    tipo_tercero: str

    model_config = ConfigDict(from_attributes=True)

class VisitaRespuesta(VisitaBase):
    id: int
    tercero: TerceroResumen | None = None

    fuente_ubicacion: FuenteUbicacion = "SIN_VALIDAR"
    ubicacion_validada: bool = False
    ubicacion_validada_at: datetime | None = None
    ubicacion_validada_by: int | None = None

    created_by: int | None
    updated_by: int | None

    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class VisitaListado(BaseModel):
    total: int = Field(ge=0)
    pagina: int = Field(ge=1)
    limite: int = Field(ge=1)
    paginas: int = Field(ge=0)
    resultados: list[VisitaRespuesta]