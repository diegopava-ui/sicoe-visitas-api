from datetime import date, time
from typing import Literal

from pydantic import BaseModel, Field


class AgendaAgentePregunta(BaseModel):
    pregunta: str = Field(
        min_length=2,
        max_length=500,
        description=(
            "Pregunta en lenguaje natural relacionada "
            "exclusivamente con la agenda propia."
        ),
    )


PeriodoAgendaAgente = Literal[
    "HOY",
    "MANANA",
    "ESTA_SEMANA",
    "RESTO_SEMANA",
    "ESTE_MES",
    "RESTO_MES",
    "SIN_PERIODO",
]

EstadoAgendaAgente = Literal[
    "PROGRAMADA",
    "EN_PROCESO",
    "FINALIZADA",
    "CANCELADA",
    "SIN_ESTADO",
]


class AgendaAgenteConsultaEstructurada(BaseModel):
    periodo: PeriodoAgendaAgente
    ciudad: str = Field(default="SIN_CIUDAD", max_length=100)
    estado: EstadoAgendaAgente = "SIN_ESTADO"


class AgendaAgenteVisita(BaseModel):
    id: int
    codigo: str
    fecha: date
    hora_inicio: time | None = None
    hora_fin: time | None = None
    empresa: str
    servicio: str | None = None
    tipo_visita: str | None = None
    estado: str
    ciudad: str | None = None
    departamento: str | None = None
    ubicacion_validada: bool = False
    tiene_coordenadas: bool = False


class AgendaAgenteRespuesta(BaseModel):
    respuesta: str
    intencion: str
    fuera_de_dominio: bool = False
    seguridad: str = "SOLO_MI_AGENDA"
    fecha_desde: date | None = None
    fecha_hasta: date | None = None
    total_visitas: int = 0
    visitas: list[AgendaAgenteVisita] = []
