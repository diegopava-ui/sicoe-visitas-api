from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.models.notificacion import Notificacion
from app.models.preferencia_notificacion import PreferenciaNotificacion


def buscar_notificacion_por_id(db: Session, notificacion_id: int) -> Notificacion | None:
    return db.get(Notificacion, notificacion_id)


def buscar_notificacion_por_clave(db: Session, clave_idempotencia: str) -> Notificacion | None:
    return db.scalar(
        select(Notificacion).where(Notificacion.clave_idempotencia == clave_idempotencia)
    )


def listar_notificaciones(
    db: Session,
    estado: str | None = None,
    canal: str | None = None,
    limite: int = 100,
) -> list[Notificacion]:
    consulta = select(Notificacion)
    if estado:
        consulta = consulta.where(Notificacion.estado == estado)
    if canal:
        consulta = consulta.where(Notificacion.canal == canal)
    consulta = consulta.order_by(Notificacion.created_at.desc()).limit(limite)
    return list(db.scalars(consulta).all())


def listar_notificaciones_pendientes_envio(
    db: Session,
    *,
    hasta: datetime | None = None,
    limite: int = 100,
) -> list[Notificacion]:
    hasta = hasta or datetime.now(timezone.utc)
    consulta = (
        select(Notificacion)
        .where(
            Notificacion.estado == "PENDIENTE",
            Notificacion.fecha_programada <= hasta,
        )
        .order_by(Notificacion.fecha_programada.asc(), Notificacion.id.asc())
        .limit(limite)
    )
    return list(db.scalars(consulta).all())


def cancelar_notificaciones_pendientes_visita(db: Session, visita_id: int) -> int:
    resultado = db.execute(
        update(Notificacion)
        .where(
            Notificacion.visita_id == visita_id,
            Notificacion.estado.in_(("PENDIENTE", "PROCESANDO")),
        )
        .values(
            estado="CANCELADA",
            error="Cancelada por reprogramación o cambio de estado de la visita.",
            updated_at=datetime.now(timezone.utc),
        )
    )
    db.commit()
    return int(resultado.rowcount or 0)


def guardar_notificacion(db: Session, notificacion: Notificacion) -> Notificacion:
    db.add(notificacion)
    db.commit()
    db.refresh(notificacion)
    return notificacion


def actualizar_notificacion(db: Session, notificacion: Notificacion) -> Notificacion:
    db.add(notificacion)
    db.commit()
    db.refresh(notificacion)
    return notificacion


def buscar_preferencia_por_id(
    db: Session, preferencia_id: int
) -> PreferenciaNotificacion | None:
    return db.get(PreferenciaNotificacion, preferencia_id)


def buscar_preferencia_asesor(
    db: Session, asesor_id: int, telefono: str | None = None
) -> PreferenciaNotificacion | None:
    consulta = select(PreferenciaNotificacion).where(
        PreferenciaNotificacion.tipo_destinatario == "ASESOR",
        PreferenciaNotificacion.asesor_id == asesor_id,
    )
    if telefono:
        consulta = consulta.where(PreferenciaNotificacion.telefono_whatsapp == telefono)
    return db.scalar(consulta.order_by(PreferenciaNotificacion.id.desc()))


def buscar_preferencia_cliente(
    db: Session, tercero_id: int, telefono: str | None = None
) -> PreferenciaNotificacion | None:
    consulta = select(PreferenciaNotificacion).where(
        PreferenciaNotificacion.tipo_destinatario == "CLIENTE",
        PreferenciaNotificacion.tercero_id == tercero_id,
    )
    if telefono:
        consulta = consulta.where(PreferenciaNotificacion.telefono_whatsapp == telefono)
    return db.scalar(consulta.order_by(PreferenciaNotificacion.id.desc()))


def guardar_preferencia(
    db: Session, preferencia: PreferenciaNotificacion
) -> PreferenciaNotificacion:
    db.add(preferencia)
    db.commit()
    db.refresh(preferencia)
    return preferencia


def actualizar_preferencia(
    db: Session, preferencia: PreferenciaNotificacion
) -> PreferenciaNotificacion:
    preferencia.updated_at = datetime.now().astimezone()
    db.add(preferencia)
    db.commit()
    db.refresh(preferencia)
    return preferencia


def tomar_notificacion_para_proceso(
    db: Session, notificacion_id: int
) -> Notificacion | None:
    notificacion = db.scalar(
        select(Notificacion)
        .where(Notificacion.id == notificacion_id)
        .with_for_update()
    )
    if notificacion is None or notificacion.estado != "PENDIENTE":
        return None

    notificacion.estado = "PROCESANDO"
    notificacion.intentos += 1
    notificacion.updated_at = datetime.now(timezone.utc)
    db.add(notificacion)
    db.commit()
    db.refresh(notificacion)
    return notificacion


def guardar_resultado_worker(
    db: Session,
    notificacion: Notificacion,
    *,
    estado: str,
    proveedor: str,
    proveedor_message_id: str | None = None,
    error: str | None = None,
    respuesta: str | None = None,
) -> Notificacion:
    notificacion.estado = estado
    notificacion.proveedor = proveedor
    notificacion.proveedor_message_id = proveedor_message_id
    notificacion.error = error
    notificacion.respuesta = respuesta
    notificacion.updated_at = datetime.now(timezone.utc)
    if estado in ("SIMULADA", "ENVIADA"):
        notificacion.fecha_envio = datetime.now(timezone.utc)
    db.add(notificacion)
    db.commit()
    db.refresh(notificacion)
    return notificacion
