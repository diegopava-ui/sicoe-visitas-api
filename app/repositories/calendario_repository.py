from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.visita import Visita


def listar_eventos_calendario(
    db: Session,
    desde: date,
    hasta: date,
    asesor_id: int | None = None,
    tercero_id: int | None = None,
    estado: str | None = None,
    tipo_visita: str | None = None,
    servicio: str | None = None,
) -> list[Visita]:

    consulta = (
        select(Visita)
        .options(
            selectinload(Visita.asesor),
        )
        .where(
            Visita.deleted_at.is_(None),
            Visita.activo.is_(True),
            Visita.fecha_visita >= desde,
            Visita.fecha_visita <= hasta,
        )
    )

    if asesor_id is not None:
        consulta = consulta.where(
            Visita.asesor_id == asesor_id
        )

    if tercero_id is not None:
        consulta = consulta.where(
            Visita.tercero_id == tercero_id
        )

    if estado is not None:
        consulta = consulta.where(
            Visita.estado == estado
        )

    if tipo_visita is not None:
        consulta = consulta.where(
            Visita.tipo_visita == tipo_visita
        )

    if servicio:
        consulta = consulta.where(
            Visita.servicio.ilike(
                f"%{servicio.strip()}%"
            )
        )

    consulta = consulta.order_by(
        Visita.fecha_visita.asc(),
        Visita.hora_inicio.asc().nulls_last(),
        Visita.id.asc(),
    )

    return list(
        db.scalars(consulta).all()
    )