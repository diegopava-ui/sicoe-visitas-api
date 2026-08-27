from datetime import datetime

from pydantic import BaseModel, ConfigDict


class VisitaEvidenciaBase(BaseModel):
    tipo_archivo: str
    descripcion: str | None = None


class VisitaEvidenciaCrear(VisitaEvidenciaBase):
    """
    Representa los datos de una evidencia ya
    almacenada (nombre y URL del archivo), útil
    si en el futuro se registra una evidencia
    cuyo archivo se subió por otro medio.

    El endpoint de subida (multipart/form-data)
    NO usa este schema como body directamente
    -recibe el archivo binario aparte-, pero se
    mantiene aquí por consistencia con el resto
    de módulos (Base/Crear/Actualizar/Respuesta)
    y para reutilizarlo internamente si hace falta.
    """

    visita_id: int
    nombre_archivo: str
    url_archivo: str


class VisitaEvidenciaActualizar(BaseModel):
    tipo_archivo: str | None = None
    descripcion: str | None = None
    activo: bool | None = None


class VisitaEvidenciaRespuesta(VisitaEvidenciaBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    visita_id: int
    nombre_archivo: str
    url_archivo: str
    created_by: int | None
    created_at: datetime


class VisitaEvidenciaListado(BaseModel):
    resultados: list[VisitaEvidenciaRespuesta]
    total: int
