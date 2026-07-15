from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


RolUsuario = Literal[
    "ADMINISTRADOR",
    "COORDINADOR",
    "ASESOR",
]


class UsuarioBase(BaseModel):
    asesor_id: int | None = Field(default=None, gt=0)
    username: str = Field(min_length=4, max_length=80)
    email: EmailStr
    rol: RolUsuario = "ASESOR"
    activo: bool = True

    @field_validator("username")
    @classmethod
    def normalizar_username(cls, valor: str) -> str:
        username = valor.strip().lower()

        if " " in username:
            raise ValueError("El nombre de usuario no puede contener espacios")

        return username


class UsuarioCrear(UsuarioBase):
    password: str = Field(min_length=10, max_length=128)


class UsuarioActualizar(BaseModel):
    asesor_id: int | None = Field(default=None, gt=0)
    username: str | None = Field(default=None, min_length=4, max_length=80)
    email: EmailStr | None = None
    rol: RolUsuario | None = None
    activo: bool | None = None

    @field_validator("username")
    @classmethod
    def normalizar_username(
        cls,
        valor: str | None,
    ) -> str | None:
        if valor is None:
            return None

        username = valor.strip().lower()

        if " " in username:
            raise ValueError("El nombre de usuario no puede contener espacios")

        return username


class UsuarioRespuesta(UsuarioBase):
    id: int
    ultimo_acceso: datetime | None
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None

    model_config = ConfigDict(from_attributes=True)