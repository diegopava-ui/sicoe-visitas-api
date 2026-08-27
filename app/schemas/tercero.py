from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class TerceroBase(BaseModel):
    tipo_tercero: str = Field(default="cliente", max_length=30)
    tipo_identificacion: str = Field(default="NIT", max_length=20)
    identificacion: str = Field(..., max_length=30)

    razon_social: str = Field(..., max_length=200)
    nombre_comercial: Optional[str] = Field(None, max_length=200)

    email: Optional[EmailStr] = None
    telefono: Optional[str] = Field(None, max_length=30)

    direccion: Optional[str] = Field(None, max_length=250)

    ciudad: Optional[str] = Field(None, max_length=100)
    departamento: Optional[str] = Field(None, max_length=100)

    contacto_nombre: Optional[str] = Field(None, max_length=150)
    contacto_email: Optional[EmailStr] = None
    contacto_telefono: Optional[str] = Field(None, max_length=30)

    observaciones: Optional[str] = None


class TerceroCreate(TerceroBase):
    # No se piden en el request: el backend los calcula
    # automáticamente por geocodificación al guardar.
    latitud: Optional[Decimal] = None
    longitud: Optional[Decimal] = None
    fuente_ubicacion: str = "SIN_VALIDAR"


class TerceroUpdate(BaseModel):
    tipo_tercero: Optional[str] = None
    tipo_identificacion: Optional[str] = None
    identificacion: Optional[str] = None

    razon_social: Optional[str] = None
    nombre_comercial: Optional[str] = None

    email: Optional[EmailStr] = None
    telefono: Optional[str] = None

    direccion: Optional[str] = None

    ciudad: Optional[str] = None
    departamento: Optional[str] = None

    # No se piden en el request: el backend los recalcula
    # automáticamente por geocodificación si cambia la
    # dirección, ciudad o departamento.
    latitud: Optional[Decimal] = None
    longitud: Optional[Decimal] = None
    fuente_ubicacion: Optional[str] = None

    contacto_nombre: Optional[str] = None
    contacto_email: Optional[EmailStr] = None
    contacto_telefono: Optional[str] = None

    observaciones: Optional[str] = None
    activo: Optional[bool] = None


class TerceroResponse(TerceroBase):
    id: int
    activo: bool

    latitud: Optional[Decimal] = None
    longitud: Optional[Decimal] = None
    fuente_ubicacion: str = "SIN_VALIDAR"

    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)
