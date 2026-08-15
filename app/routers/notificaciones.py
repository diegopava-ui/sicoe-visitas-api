from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import require_roles
from app.models.usuario import Usuario
from app.models.visita import Visita
from app.repositories.notificacion_repository import (
    buscar_preferencia_por_id,
    listar_notificaciones_pendientes_envio,
)
from app.schemas.notificacion import (
    CanalNotificacion,
    EstadoNotificacion,
    NotificacionRespuesta,
    PreferenciaNotificacionActualizar,
    PreferenciaNotificacionCrear,
    PreferenciaNotificacionRespuesta,
    SimulacionWhatsAppRespuesta,
    NotificacionResultadoWorker,
)
from app.services.notificacion_programacion_service import (
    programar_notificaciones_visita,
)
from app.services.notificacion_piloto_service import (
    ejecutar_piloto_simulado,
    encolar_piloto_n8n,
)
from app.services.notificacion_worker_service import (
    iniciar_procesamiento_notificacion,
    registrar_resultado_notificacion,
)
from app.services.notificacion_service import (
    crear_preferencia,
    modificar_preferencia,
    obtener_notificaciones,
    simular_recordatorio_asesor,
)

router = APIRouter(prefix="/api/v1/notificaciones", tags=["Notificaciones"])


@router.post(
    "/preferencias",
    response_model=PreferenciaNotificacionRespuesta,
    status_code=201,
)
def registrar_preferencia(
    datos: PreferenciaNotificacionCrear,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_roles("ADMINISTRADOR", "COORDINADOR")),
):
    return crear_preferencia(db, datos)


@router.patch(
    "/preferencias/{preferencia_id}",
    response_model=PreferenciaNotificacionRespuesta,
)
def actualizar_preferencia_endpoint(
    preferencia_id: int,
    datos: PreferenciaNotificacionActualizar,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_roles("ADMINISTRADOR", "COORDINADOR")),
):
    preferencia = buscar_preferencia_por_id(db, preferencia_id)
    if preferencia is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Preferencia no encontrada.")
    return modificar_preferencia(db, preferencia, datos)


@router.get("", response_model=list[NotificacionRespuesta])
def consultar_notificaciones(
    estado: EstadoNotificacion | None = Query(default=None),
    canal: CanalNotificacion | None = Query(default=None),
    limite: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_roles("ADMINISTRADOR", "COORDINADOR")),
):
    return obtener_notificaciones(
        db,
        estado=estado.value if estado else None,
        canal=canal.value if canal else None,
        limite=limite,
    )


@router.get(
    "/pendientes-envio",
    response_model=list[NotificacionRespuesta],
    summary="Consultar notificaciones listas para ser procesadas por n8n",
)
def consultar_pendientes_envio(
    hasta: datetime | None = Query(default=None),
    limite: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_roles("ADMINISTRADOR", "COORDINADOR")),
):
    return listar_notificaciones_pendientes_envio(db, hasta=hasta, limite=limite)


@router.post(
    "/programar/visita/{visita_id}",
    summary="Generar órdenes de notificación para una visita",
)
def programar_visita(
    visita_id: int,
    reemplazar_pendientes: bool = Query(default=False),
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_roles("ADMINISTRADOR", "COORDINADOR")),
):
    visita = db.get(Visita, visita_id)
    if visita is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Visita no encontrada.")
    resultado = programar_notificaciones_visita(
        db, visita, reemplazar_pendientes=reemplazar_pendientes
    )
    return {
        "visita_id": resultado.visita_id,
        "notificaciones_creadas": resultado.creadas,
        "notificaciones_canceladas": resultado.canceladas,
        "omisiones": resultado.omitidas,
    }


@router.post(
    "/whatsapp/simular/asesor/{visita_id}",
    response_model=SimulacionWhatsAppRespuesta,
)
def simular_whatsapp_asesor(
    visita_id: int,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_roles("ADMINISTRADOR", "COORDINADOR")),
):
    notificacion = simular_recordatorio_asesor(db, visita_id)
    return SimulacionWhatsAppRespuesta(
        notificacion=notificacion,
        proveedor=notificacion.proveedor or "SIMULADOR_SICOE",
        modo_simulacion=True,
        mensaje="Simulación registrada correctamente. No se consumió un servicio de WhatsApp.",
    )


@router.post(
    "/piloto/simular/{visita_id}",
    summary="Preparar preferencias y simular WhatsApp para asesor y cliente",
)
def simular_piloto_whatsapp(
    visita_id: int,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_roles("ADMINISTRADOR", "COORDINADOR")),
):
    return ejecutar_piloto_simulado(db, visita_id)


@router.post(
    "/piloto/encolar/{visita_id}",
    summary="Crear órdenes PENDIENTES para la prueba del worker n8n",
)
def encolar_piloto_worker_n8n(
    visita_id: int,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_roles("ADMINISTRADOR", "COORDINADOR")),
):
    return encolar_piloto_n8n(db, visita_id)


@router.post(
    "/{notificacion_id}/procesar",
    response_model=NotificacionRespuesta,
    summary="Tomar una notificación PENDIENTE para procesamiento exclusivo",
)
def procesar_notificacion_worker(
    notificacion_id: int,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_roles("ADMINISTRADOR", "COORDINADOR")),
):
    return iniciar_procesamiento_notificacion(db, notificacion_id)


@router.patch(
    "/{notificacion_id}/resultado",
    response_model=NotificacionRespuesta,
    summary="Registrar el resultado devuelto por n8n o el proveedor",
)
def resultado_notificacion_worker(
    notificacion_id: int,
    datos: NotificacionResultadoWorker,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_roles("ADMINISTRADOR", "COORDINADOR")),
):
    return registrar_resultado_notificacion(db, notificacion_id, datos)
