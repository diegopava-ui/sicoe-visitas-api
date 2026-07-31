from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.visita import Visita
from app.models.visita_evidencia import VisitaEvidencia


def obtener_visita_para_pdf(
    db: Session,
    visita_id: int,
) -> Visita | None:
    """
    Obtiene una visita con todas las relaciones necesarias
    para generar el informe corporativo en PDF.

    Incluye:
    - Asesor
    - Tercero
    - Evidencias
    - Usuario creador
    - Usuario modificador

    No devuelve visitas eliminadas lógicamente.
    """

    consulta = (
        select(Visita)
        .options(
            selectinload(Visita.asesor),
            selectinload(Visita.tercero),
            selectinload(Visita.evidencias),
            selectinload(Visita.usuario_creador),
            selectinload(Visita.usuario_modificador),
        )
       .where(
            Visita.id == visita_id,
            Visita.activo.is_(True),
            Visita.deleted_at.is_(None),
        )
    )

    return db.scalar(consulta)


def obtener_evidencias_activas(
    visita: Visita,
) -> list[VisitaEvidencia]:
    """
    Filtra las evidencias activas y no eliminadas
    asociadas con una visita.
    """

    evidencias_activas = [
        evidencia
        for evidencia in visita.evidencias
        if evidencia.activo
        and evidencia.deleted_at is None
    ]

    return sorted(
        evidencias_activas,
        key=lambda evidencia: (
            evidencia.created_at,
            evidencia.id,
        ),
    )