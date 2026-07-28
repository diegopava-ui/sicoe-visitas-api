from datetime import date, datetime, time
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class ReporteBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class ResumenVisitasResponse(ReporteBase):
    total_visitas_vigentes: int = 0
    visitas_mes_actual: int = 0
    visitas_semana_actual: int = 0
    visitas_programadas: int = 0
    visitas_en_proceso: int = 0
    visitas_finalizadas: int = 0
    visitas_canceladas: int = 0
    porcentaje_cumplimiento: Decimal | None = None
    duracion_promedio_minutos: Decimal | None = None
    participantes_totales: int = 0
    terceros_atendidos: int = 0
    asesores_con_actividad: int = 0
    compromisos_registrados: int = 0
    proximas_visitas_30_dias: int = 0
    satisfaccion_promedio_escala_1_4: Decimal | None = None
    ultima_fecha_visita: date | None = None
    siguiente_fecha_programada: date | None = None


class VisitasPorEstadoResponse(ReporteBase):
    estado: str
    cantidad: int
    porcentaje_total: Decimal | None = None
    terceros: int
    asesores: int
    participantes: int
    duracion_promedio_minutos: Decimal | None = None


class ProductividadAsesorResponse(ReporteBase):
    asesor_id: int
    asesor_identificacion: str
    asesor_nombre: str
    asesor_email: str
    asesor_activo: bool
    total_visitas: int
    programadas: int
    en_proceso: int
    finalizadas: int
    canceladas: int
    porcentaje_cumplimiento: Decimal | None = None
    duracion_promedio_minutos: Decimal | None = None
    participantes_atendidos: int
    terceros_atendidos: int
    ultima_visita: date | None = None
    proxima_visita: date | None = None
    satisfaccion_promedio_escala_1_4: Decimal | None = None


class ActividadTerceroResponse(ReporteBase):
    tercero_id: int
    identificacion: str
    razon_social: str
    nombre_comercial: str | None = None
    tipo_tercero: str
    ciudad: str | None = None
    departamento: str | None = None
    email: str | None = None
    contacto_nombre: str | None = None
    contacto_email: str | None = None
    tercero_activo: bool
    total_visitas: int
    visitas_finalizadas: int
    visitas_programadas: int
    visitas_canceladas: int
    asesores_relacionados: int
    participantes_acumulados: int
    ultima_visita: date | None = None
    proxima_visita: date | None = None
    dias_sin_visita: int | None = None
    satisfaccion_promedio_escala_1_4: Decimal | None = None


class VisitasPorPeriodoResponse(ReporteBase):
    periodo_mes: date
    anio: int
    mes_numero: int
    total_visitas: int
    programadas: int
    en_proceso: int
    finalizadas: int
    canceladas: int
    porcentaje_cumplimiento: Decimal | None = None
    asesores: int
    terceros: int
    participantes: int
    duracion_promedio_minutos: Decimal | None = None


class CompromisoPendienteResponse(ReporteBase):
    visita_id: int
    fecha_visita: date
    asesor_id: int
    asesor_nombre: str | None = None
    asesor_email: str | None = None
    tercero_id: int | None = None
    tercero_nombre: str | None = None
    tercero_razon_social: str | None = None
    tercero_email: str | None = None
    contacto_nombre: str | None = None
    contacto_email: str | None = None
    servicio: str
    tipo_visita: str
    compromisos: str
    proxima_visita: date | None = None
    estado_compromiso: str
    dias_para_seguimiento: int | None = None


class ProximaVisitaResponse(ReporteBase):
    visita_id: int
    fecha_visita: date
    hora_inicio: time | None = None
    hora_fin: time | None = None
    dias_restantes: int
    prioridad_recordatorio: str
    asesor_id: int
    asesor_nombre: str | None = None
    asesor_email: str | None = None
    tercero_id: int | None = None
    tercero_nombre: str | None = None
    tercero_razon_social: str | None = None
    tercero_identificacion: str | None = None
    tercero_email: str | None = None
    contacto_nombre: str | None = None
    contacto_email: str | None = None
    contacto_telefono: str | None = None
    servicio: str
    tipo_visita: str
    estado: str
    ciudad: str | None = None
    departamento: str | None = None
    direccion: str | None = None


class SatisfaccionResponse(ReporteBase):
    nivel_satisfaccion: str
    satisfaccion_valor: int
    cantidad: int
    porcentaje: Decimal | None = None
    terceros: int
    asesores: int


class CoberturaGeograficaResponse(ReporteBase):
    departamento: str
    ciudad: str
    total_visitas: int
    finalizadas: int
    programadas: int
    terceros: int
    asesores: int
    participantes: int
    duracion_promedio_minutos: Decimal | None = None
    satisfaccion_promedio_escala_1_4: Decimal | None = None
    latitud_promedio: Decimal | None = None
    longitud_promedio: Decimal | None = None


class FiltroLimite(BaseModel):
    limite: int = Field(default=20, ge=1, le=100)

class HallazgoIAResponse(ReporteBase):
    titulo: str
    detalle: str
    severidad: str


class RiesgoIAResponse(ReporteBase):
    riesgo: str
    evidencia: str
    nivel: str


class RecomendacionIAResponse(ReporteBase):
    accion: str
    justificacion: str
    prioridad: str
    plazo: str


class UltimoAnalisisIAResponse(ReporteBase):
    id: int
    evento_id: int
    informe_evento_id: int
    modelo: str
    openai_response_id: str | None = None
    resumen_ejecutivo: str
    hallazgos_json: list[HallazgoIAResponse] = Field(
        default_factory=list,
    )
    riesgos_json: list[RiesgoIAResponse] = Field(
        default_factory=list,
    )
    recomendaciones_json: list[
        RecomendacionIAResponse
    ] = Field(
        default_factory=list,
    )
    mensaje_cierre: str | None = None
    contexto_anonimizado: bool = False
    created_at: datetime

