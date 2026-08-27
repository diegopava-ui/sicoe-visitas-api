from __future__ import annotations

from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.visita import Visita


def _codigo_visita(visita_id: int) -> str:
    return f"VIS-{visita_id:06d}"


def consultar_proxima_visita(db: Session, asesor_id: int) -> dict:
    consulta = (
        select(Visita)
        .where(
            Visita.asesor_id == asesor_id,
            Visita.activo.is_(True),
            Visita.deleted_at.is_(None),
            Visita.estado == "PROGRAMADA",
            Visita.fecha_visita >= date.today(),
        )
        .order_by(
            Visita.fecha_visita.asc(),
            Visita.hora_inicio.asc().nulls_last(),
            Visita.id.asc(),
        )
        .limit(1)
    )

    visita = db.scalar(consulta)

    if visita is None:
        return {
            "respuesta": "No tienes visitas futuras programadas.",
            "intencion": "PROXIMA_VISITA",
            "fuera_de_dominio": False,
            "seguridad": "SOLO_MI_AGENDA",
            "total_visitas": 0,
            "visitas": [],
        }

    hora = (
        visita.hora_inicio.strftime("%H:%M")
        if visita.hora_inicio is not None
        else "Sin hora"
    )
    empresa = visita.empresa or "Sin empresa"
    ciudad = visita.ciudad or "Sin ciudad"
    departamento = visita.departamento or "Sin departamento"

    item = {
        "id": visita.id,
        "codigo": _codigo_visita(visita.id),
        "fecha": visita.fecha_visita.isoformat(),
        "hora_inicio": visita.hora_inicio.isoformat() if visita.hora_inicio else None,
        "hora_fin": visita.hora_fin.isoformat() if visita.hora_fin else None,
        "empresa": visita.empresa,
        "servicio": visita.servicio,
        "tipo_visita": visita.tipo_visita,
        "estado": visita.estado,
        "ciudad": visita.ciudad,
        "departamento": visita.departamento,
        "direccion": visita.direccion,
        "ubicacion_validada": visita.ubicacion_validada,
        "tiene_coordenadas": (
            visita.latitud is not None and visita.longitud is not None
        ),
    }

    return {
        "respuesta": (
            f"Tu próxima visita es el {visita.fecha_visita.isoformat()} "
            f"a las {hora}: {_codigo_visita(visita.id)}, {empresa}, "
            f"{ciudad}, {departamento}."
        ),
        "intencion": "PROXIMA_VISITA",
        "fuera_de_dominio": False,
        "seguridad": "SOLO_MI_AGENDA",
        "total_visitas": 1,
        "visitas": [item],
    }
