from datetime import date, datetime, timezone

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.tercero import Tercero
from app.models.visita import Visita


def _consulta_visitas(
    buscar: str | None = None,
    asesor_id: int | None = None,
    tercero_id: int | None = None,
    estado: str | None = None,
    tipo_visita: str | None = None,
    servicio: str | None = None,
    fecha_inicio: date | None = None,
    fecha_fin: date | None = None,
    activo: bool | None = None,
):
    consulta = (
        select(Visita)
        .outerjoin(
            Tercero,
            Visita.tercero_id == Tercero.id,
        )
    )

    if activo is True:
        consulta = consulta.where(
            Visita.activo.is_(True),
            Visita.deleted_at.is_(None),
        )
    elif activo is False:
        consulta = consulta.where(
            or_(
                Visita.activo.is_(False),
                Visita.deleted_at.is_not(None),
            )
        )

    if buscar:
        patron = f"%{buscar.strip()}%"

        consulta = consulta.where(
            or_(
                Tercero.razon_social.ilike(patron),
                Tercero.nombre_comercial.ilike(patron),
                Tercero.identificacion.ilike(patron),
                Visita.empresa.ilike(patron),
                Visita.nit.ilike(patron),
                Visita.servicio.ilike(patron),
                Visita.objetivo.ilike(patron),
                Visita.resultado.ilike(patron),
                Visita.observaciones.ilike(patron),
            )
        )

    if asesor_id is not None:
        consulta = consulta.where(
            Visita.asesor_id == asesor_id,
        )

    if tercero_id is not None:
        consulta = consulta.where(
            Visita.tercero_id == tercero_id,
        )

    if estado is not None:
        consulta = consulta.where(
            Visita.estado == estado,
        )

    if tipo_visita is not None:
        consulta = consulta.where(
            Visita.tipo_visita == tipo_visita,
        )

    if servicio:
        consulta = consulta.where(
            Visita.servicio.ilike(
                f"%{servicio.strip()}%"
            ),
        )

    if fecha_inicio is not None:
        consulta = consulta.where(
            Visita.fecha_visita >= fecha_inicio,
        )

    if fecha_fin is not None:
        consulta = consulta.where(
            Visita.fecha_visita <= fecha_fin,
        )

    return consulta


def buscar_visita_por_id(
    db: Session,
    visita_id: int,
) -> Visita | None:
    return db.scalar(
        select(Visita).where(
            Visita.id == visita_id,
            Visita.activo.is_(True),
            Visita.deleted_at.is_(None),
        )
    )


def buscar_visita_por_id_incluyendo_eliminadas(
    db: Session,
    visita_id: int,
) -> Visita | None:
    return db.scalar(
        select(Visita).where(
            Visita.id == visita_id,
        )
    )


def listar_visitas(
    db: Session,
    buscar: str | None = None,
    asesor_id: int | None = None,
    tercero_id: int | None = None,
    estado: str | None = None,
    tipo_visita: str | None = None,
    servicio: str | None = None,
    fecha_inicio: date | None = None,
    fecha_fin: date | None = None,
    activo: bool | None = None,
    limite: int = 50,
    offset: int = 0,
) -> list[Visita]:
    consulta = _consulta_visitas(
        buscar=buscar,
        asesor_id=asesor_id,
        tercero_id=tercero_id,
        estado=estado,
        tipo_visita=tipo_visita,
        servicio=servicio,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        activo=activo,
    )

    consulta = (
        consulta
        .order_by(
            Visita.fecha_visita.desc(),
            Visita.id.desc(),
        )
        .offset(offset)
        .limit(limite)
    )

    return list(
        db.scalars(consulta).unique().all()
    )


def contar_visitas(
    db: Session,
    buscar: str | None = None,
    asesor_id: int | None = None,
    tercero_id: int | None = None,
    estado: str | None = None,
    tipo_visita: str | None = None,
    servicio: str | None = None,
    fecha_inicio: date | None = None,
    fecha_fin: date | None = None,
    activo: bool | None = None,
) -> int:
    subconsulta = _consulta_visitas(
        buscar=buscar,
        asesor_id=asesor_id,
        tercero_id=tercero_id,
        estado=estado,
        tipo_visita=tipo_visita,
        servicio=servicio,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        activo=activo,
    ).with_only_columns(
        Visita.id,
    ).distinct().subquery()

    return int(
        db.scalar(
            select(func.count()).select_from(
                subconsulta
            )
        )
        or 0
    )


def guardar_visita(
    db: Session,
    visita: Visita,
) -> Visita:
    db.add(visita)
    db.commit()
    db.refresh(visita)

    return visita


def actualizar_visita(
    db: Session,
    visita: Visita,
) -> Visita:
    db.add(visita)
    db.commit()
    db.refresh(visita)

    return visita


def desactivar_visita(
    db: Session,
    visita: Visita,
) -> Visita:
    fecha_actual = datetime.now(timezone.utc)

    visita.activo = False
    visita.deleted_at = fecha_actual
    visita.updated_at = fecha_actual

    db.add(visita)
    db.commit()
    db.refresh(visita)

    return visita


def reactivar_visita(
    db: Session,
    visita: Visita,
) -> Visita:
    visita.activo = True
    visita.deleted_at = None
    visita.updated_at = datetime.now(timezone.utc)

    db.add(visita)
    db.commit()
    db.refresh(visita)

    return visita


def contar_visitas_por_estado(
    db: Session,
) -> dict[str, int]:
    consulta = (
        select(
            Visita.estado,
            func.count(Visita.id),
        )
        .where(
            Visita.activo.is_(True),
            Visita.deleted_at.is_(None),
        )
        .group_by(
            Visita.estado,
        )
    )

    resultados = db.execute(consulta).all()

    conteos = {
        "PROGRAMADA": 0,
        "EN_PROCESO": 0,
        "FINALIZADA": 0,
        "CANCELADA": 0,
    }

    for estado, cantidad in resultados:
        conteos[estado] = int(cantidad)

    return conteos


def contar_visitas_por_asesor(
    db: Session,
) -> list[tuple[int, int]]:
    consulta = (
        select(
            Visita.asesor_id,
            func.count(Visita.id),
        )
        .where(
            Visita.activo.is_(True),
            Visita.deleted_at.is_(None),
        )
        .group_by(
            Visita.asesor_id,
        )
        .order_by(
            func.count(Visita.id).desc(),
        )
    )

    resultados = db.execute(consulta).all()

    return [
        (asesor_id, int(cantidad))
        for asesor_id, cantidad in resultados
    ]
