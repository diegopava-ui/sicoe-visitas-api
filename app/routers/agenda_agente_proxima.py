from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import require_roles
from app.models.usuario import Usuario
from app.services.agenda_agente_proxima_service import consultar_proxima_visita


router = APIRouter(
    prefix="/api/v1/agenda-agente",
    tags=["Agente Agenda"],
)


@router.get(
    "/proxima-visita",
    summary="Consultar mi próxima visita programada",
)
def obtener_proxima_visita(
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(
        require_roles(
            "ADMINISTRADOR",
            "COORDINADOR",
            "ASESOR",
        )
    ),
):
    if usuario_actual.asesor_id is None:
        return {
            "respuesta": (
                "Tu usuario no tiene un asesor asociado. "
                "No puedo consultar una agenda personal hasta "
                "que se configure esa asociación."
            ),
            "intencion": "USUARIO_SIN_ASESOR",
            "fuera_de_dominio": False,
            "seguridad": "SOLO_MI_AGENDA",
            "total_visitas": 0,
            "visitas": [],
        }

    return consultar_proxima_visita(
        db=db,
        asesor_id=usuario_actual.asesor_id,
    )
