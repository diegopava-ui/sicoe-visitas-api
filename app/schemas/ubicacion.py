from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


FuenteUbicacionValidable = Literal[
    "GPS",
    "GEOCODIFICADA",
    "MANUAL",
]


class UbicacionValidar(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "fuente_ubicacion": "MANUAL"
            }
        }
    )

    fuente_ubicacion: FuenteUbicacionValidable

    latitud: Decimal | None = Field(
        default=None,
        ge=Decimal("-90"),
        le=Decimal("90"),
        max_digits=10,
        decimal_places=7,
        description=(
            "Opcional. Si se omite junto con longitud, "
            "se conservan las coordenadas existentes de la visita."
        ),
    )

    longitud: Decimal | None = Field(
        default=None,
        ge=Decimal("-180"),
        le=Decimal("180"),
        max_digits=10,
        decimal_places=7,
        description=(
            "Opcional. Si se omite junto con latitud, "
            "se conservan las coordenadas existentes de la visita."
        ),
    )

    @model_validator(mode="after")
    def validar_par_coordenadas(self) -> "UbicacionValidar":
        una_sola_coordenada = (
            (self.latitud is None)
            != (self.longitud is None)
        )

        if una_sola_coordenada:
            raise ValueError(
                "Latitud y longitud deben enviarse juntas."
            )

        return self


class UbicacionValidacionRespuesta(BaseModel):
    visita_id: int
    latitud: Decimal
    longitud: Decimal
    fuente_ubicacion: FuenteUbicacionValidable
    ubicacion_validada: bool
    ubicacion_validada_at: datetime
    ubicacion_validada_by: int
    mensaje: str
