from datetime import date, datetime, time
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel


class CalendarioAsesor(BaseModel):
    id: int
    nombre: str


class CalendarioCliente(BaseModel):
    tercero_id: Optional[int] = None
    empresa: str
    nit: Optional[str] = None


class CalendarioUbicacion(BaseModel):
    direccion: Optional[str] = None
    ciudad: Optional[str] = None
    departamento: Optional[str] = None
    latitud: Optional[Decimal] = None
    longitud: Optional[Decimal] = None

    # UBI-005 / UBI-006
    fuente_ubicacion: str = "SIN_VALIDAR"
    ubicacion_validada: bool = False
    ubicacion_validada_at: Optional[datetime] = None
    ubicacion_validada_by: Optional[int] = None


class CalendarioVisual(BaseModel):
    color: str
    icono: str


class CalendarioEvento(BaseModel):
    id: int

    fecha_visita: date
    hora_inicio: Optional[time] = None
    hora_fin: Optional[time] = None
    duracion_minutos: Optional[int] = None

    titulo: str

    asesor: CalendarioAsesor
    cliente: CalendarioCliente
    ubicacion: CalendarioUbicacion

    servicio: Optional[str] = None
    tipo_visita: Optional[str] = None
    estado: str

    visual: CalendarioVisual
