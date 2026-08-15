from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class CanalNotificacion(StrEnum):
    WHATSAPP = "WHATSAPP"
    EMAIL = "EMAIL"
    SMS = "SMS"
    PUSH = "PUSH"


class TipoDestinatario(StrEnum):
    ASESOR = "ASESOR"
    CLIENTE = "CLIENTE"
    SUPERVISOR = "SUPERVISOR"
    USUARIO = "USUARIO"


class EstadoNotificacion(StrEnum):
    PENDIENTE = "PENDIENTE"
    SIMULADA = "SIMULADA"
    PROCESANDO = "PROCESANDO"
    ENVIADA = "ENVIADA"
    ENTREGADA = "ENTREGADA"
    LEIDA = "LEIDA"
    RESPONDIDA = "RESPONDIDA"
    FALLIDA = "FALLIDA"
    CANCELADA = "CANCELADA"


class PreferenciaNotificacionCrear(BaseModel):
    tipo_destinatario: TipoDestinatario
    asesor_id: int | None = Field(default=None, gt=0)
    tercero_id: int | None = Field(default=None, gt=0)
    telefono_whatsapp: str = Field(min_length=8, max_length=30)
    acepta_whatsapp: bool = False
    whatsapp_activo: bool = True
    origen_consentimiento: str | None = Field(default=None, max_length=100)

    @field_validator("telefono_whatsapp")
    @classmethod
    def normalizar_telefono(cls, value: str) -> str:
        limpio = "".join(character for character in value if character.isdigit() or character == "+")
        if limpio.startswith("00"):
            limpio = "+" + limpio[2:]
        return limpio

    @model_validator(mode="after")
    def validar_destinatario(self):
        if self.tipo_destinatario == TipoDestinatario.ASESOR and self.asesor_id is None:
            raise ValueError("asesor_id es obligatorio para destinatario ASESOR")
        if self.tipo_destinatario == TipoDestinatario.CLIENTE and self.tercero_id is None:
            raise ValueError("tercero_id es obligatorio para destinatario CLIENTE")
        return self


class PreferenciaNotificacionActualizar(BaseModel):
    telefono_whatsapp: str | None = Field(default=None, min_length=8, max_length=30)
    acepta_whatsapp: bool | None = None
    whatsapp_activo: bool | None = None
    origen_consentimiento: str | None = Field(default=None, max_length=100)
    motivo_retiro: str | None = Field(default=None, max_length=250)


class PreferenciaNotificacionRespuesta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tipo_destinatario: TipoDestinatario
    asesor_id: int | None
    tercero_id: int | None
    telefono_whatsapp: str
    acepta_whatsapp: bool
    whatsapp_activo: bool
    fecha_consentimiento: datetime | None
    origen_consentimiento: str | None
    fecha_retiro: datetime | None
    motivo_retiro: str | None
    created_at: datetime
    updated_at: datetime


class NotificacionCrear(BaseModel):
    visita_id: int | None = Field(default=None, gt=0)
    asesor_id: int | None = Field(default=None, gt=0)
    tercero_id: int | None = Field(default=None, gt=0)
    canal: CanalNotificacion = CanalNotificacion.WHATSAPP
    tipo_destinatario: TipoDestinatario
    telefono_destino: str | None = Field(default=None, max_length=30)
    email_destino: str | None = Field(default=None, max_length=150)
    plantilla: str = Field(min_length=1, max_length=120)
    datos_json: dict[str, Any] = Field(default_factory=dict)
    mensaje_renderizado: str | None = None
    fecha_programada: datetime
    clave_idempotencia: str = Field(min_length=5, max_length=180)


class NotificacionRespuesta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    visita_id: int | None
    asesor_id: int | None
    tercero_id: int | None
    canal: CanalNotificacion
    tipo_destinatario: TipoDestinatario
    telefono_destino: str | None
    email_destino: str | None
    plantilla: str
    datos_json: dict[str, Any]
    mensaje_renderizado: str | None
    fecha_programada: datetime
    fecha_envio: datetime | None
    estado: EstadoNotificacion
    intentos: int
    proveedor: str | None
    proveedor_message_id: str | None
    clave_idempotencia: str
    error: str | None
    created_at: datetime
    updated_at: datetime


class SimulacionWhatsAppRespuesta(BaseModel):
    notificacion: NotificacionRespuesta
    proveedor: str
    modo_simulacion: bool
    mensaje: str


class EstadoResultadoWorker(StrEnum):
    SIMULADA = "SIMULADA"
    ENVIADA = "ENVIADA"
    FALLIDA = "FALLIDA"


class NotificacionResultadoWorker(BaseModel):
    estado: EstadoResultadoWorker
    proveedor: str = Field(min_length=2, max_length=50)
    proveedor_message_id: str | None = Field(default=None, max_length=180)
    error: str | None = None
    respuesta: str | None = None
