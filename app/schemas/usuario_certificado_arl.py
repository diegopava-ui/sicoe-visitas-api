from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class UsuarioCertificadoArlRespuesta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    usuario_id: int
    nombre_archivo: str
    url_archivo: str
    fecha_vigencia: date | None
    created_by: int | None
    created_at: datetime


class UsuarioCertificadoArlListado(BaseModel):
    resultados: list[UsuarioCertificadoArlRespuesta]
    total: int
