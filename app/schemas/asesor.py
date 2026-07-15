from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class AsesorBase(BaseModel):
    identificacion: str = Field(min_length=3, max_length=30)
    primer_nombre: str = Field(min_length=1, max_length=80)
    segundo_nombre: str | None = Field(default=None, max_length=80)
    primer_apellido: str = Field(min_length=1, max_length=80)
    segundo_apellido: str | None = Field(default=None, max_length=80)
    email: EmailStr
    telefono: str | None = Field(default=None, max_length=30)
    cargo: str | None = Field(default=None, max_length=100)
    activo: bool = True


class AsesorCrear(AsesorBase):
    pass


class AsesorActualizar(BaseModel):
    identificacion: str | None = Field(default=None, min_length=3, max_length=30)
    primer_nombre: str | None = Field(default=None, min_length=1, max_length=80)
    segundo_nombre: str | None = Field(default=None, max_length=80)
    primer_apellido: str | None = Field(default=None, min_length=1, max_length=80)
    segundo_apellido: str | None = Field(default=None, max_length=80)
    email: EmailStr | None = None
    telefono: str | None = Field(default=None, max_length=30)
    cargo: str | None = Field(default=None, max_length=100)
    activo: bool | None = None


class AsesorRespuesta(AsesorBase):
    id: int
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None

    model_config = ConfigDict(from_attributes=True)