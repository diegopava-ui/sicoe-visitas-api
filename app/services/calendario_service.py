from datetime import date

from sqlalchemy.orm import Session

from app.repositories.calendario_repository import (
    listar_eventos_calendario,
)
from app.schemas.calendario import (
    CalendarioAsesor,
    CalendarioCliente,
    CalendarioEvento,
    CalendarioUbicacion,
    CalendarioVisual,
)


VISUAL_ESTADOS = {
    "PROGRAMADA": {
        "color": "#2563EB",
        "icono": "calendar",
    },
    "EN_PROCESO": {
        "color": "#F59E0B",
        "icono": "play",
    },
    "FINALIZADA": {
        "color": "#16A34A",
        "icono": "check",
    },
    "CANCELADA": {
        "color": "#DC2626",
        "icono": "x",
    },
}


def _nombre_completo_asesor(asesor) -> str:
    if asesor is None:
        return "Sin asesor"

    partes = [
        asesor.primer_nombre,
        asesor.segundo_nombre,
        asesor.primer_apellido,
        asesor.segundo_apellido,
    ]

    return " ".join(
        parte.strip()
        for parte in partes
        if parte and parte.strip()
    )


def _visual_por_estado(estado: str) -> CalendarioVisual:
    configuracion = VISUAL_ESTADOS.get(
        estado,
        {
            "color": "#64748B",
            "icono": "calendar",
        },
    )

    return CalendarioVisual(
        color=configuracion["color"],
        icono=configuracion["icono"],
    )


def _titulo_evento(visita) -> str:
    empresa = visita.empresa or "Sin empresa"
    servicio = visita.servicio or visita.tipo_visita

    if servicio:
        return f"{empresa} - {servicio}"

    return empresa


def listar_eventos(
    db: Session,
    desde: date,
    hasta: date,
    asesor_id: int | None = None,
    tercero_id: int | None = None,
    estado: str | None = None,
    tipo_visita: str | None = None,
    servicio: str | None = None,
) -> list[CalendarioEvento]:

    visitas = listar_eventos_calendario(
        db=db,
        desde=desde,
        hasta=hasta,
        asesor_id=asesor_id,
        tercero_id=tercero_id,
        estado=estado,
        tipo_visita=tipo_visita,
        servicio=servicio,
    )

    eventos: list[CalendarioEvento] = []

    for visita in visitas:

        evento = CalendarioEvento(
            id=visita.id,

            fecha_visita=visita.fecha_visita,
            hora_inicio=visita.hora_inicio,
            hora_fin=visita.hora_fin,
            duracion_minutos=visita.duracion_minutos,

            titulo=_titulo_evento(visita),

            asesor=CalendarioAsesor(
                id=visita.asesor_id,
                nombre=_nombre_completo_asesor(
                    visita.asesor
                ),
            ),

            cliente=CalendarioCliente(
                tercero_id=visita.tercero_id,
                empresa=visita.empresa,
                nit=visita.nit,
            ),

            ubicacion=CalendarioUbicacion(
                direccion=visita.direccion,
                ciudad=visita.ciudad,
                departamento=visita.departamento,
                latitud=visita.latitud,
                longitud=visita.longitud,
                fuente_ubicacion=visita.fuente_ubicacion,
                ubicacion_validada=visita.ubicacion_validada,
                ubicacion_validada_at=visita.ubicacion_validada_at,
                ubicacion_validada_by=visita.ubicacion_validada_by,
            ),

            servicio=visita.servicio,
            tipo_visita=visita.tipo_visita,
            estado=visita.estado,

            visual=_visual_por_estado(
                visita.estado
            ),
        )

        eventos.append(evento)

    return eventos
