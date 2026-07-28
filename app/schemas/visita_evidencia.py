from datetime import datetime
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)


TipoArchivoEvidencia = Literal[
    "FOTO",
    "PDF",
    "VIDEO",
    "AUDIO",
    "OTRO",
]


class VisitaEvidenciaBase(BaseModel):
    visita_id: int = Field(gt=0)

    nombre_archivo: str = Field(
        min_length=1,
        max_length=255,
    )

    url_archivo: str = Field(
        min_length=1,
    )

    tipo_archivo: TipoArchivoEvidencia

    descripcion: str | None = None

    activo: bool = True

    @field_validator(
        "nombre_archivo",
        "url_archivo",
        "descripcion",
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


class VisitaEvidenciaCrear(VisitaEvidenciaBase):
    pass


class VisitaEvidenciaActualizar(BaseModel):
    visita_id: int | None = Field(
        default=None,
        gt=0,
    )

    nombre_archivo: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
    )

    url_archivo: str | None = Field(
        default=None,
        min_length=1,
    )

    tipo_archivo: TipoArchivoEvidencia | None = None

    descripcion: str | None = None

    activo: bool | None = None

    @field_validator(
        "nombre_archivo",
        "url_archivo",
        "descripcion",
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


class VisitaEvidenciaRespuesta(VisitaEvidenciaBase):
    id: int

    created_by: int | None
    updated_by: int | None

    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None

    model_config = ConfigDict(from_attributes=True)