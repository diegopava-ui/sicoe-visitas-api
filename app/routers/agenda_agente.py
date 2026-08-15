from fastapi import (
    APIRouter,
    Depends,
)
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import require_roles
from app.models.usuario import Usuario
from app.schemas.agenda_agente import (
    AgendaAgentePregunta,
    AgendaAgenteRespuesta,
)
from app.services.agenda_agente_service import (
    responder_pregunta_agenda,
)


router = APIRouter(
    prefix="/api/v1/agenda-agente",
    tags=["Agente Agenda"],
)


@router.post(
    "/preguntar",
    response_model=AgendaAgenteRespuesta,
    summary=(
        "Consultar exclusivamente la agenda "
        "propia en lenguaje natural"
    ),
)
def preguntar_agenda(
    datos: AgendaAgentePregunta,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(
        require_roles(
            "ADMINISTRADOR",
            "COORDINADOR",
            "ASESOR",
        )
    ),
) -> AgendaAgenteRespuesta:
    """
    Endpoint cerrado al dominio Agenda.

    SEGURIDAD:
    - No recibe asesor_id.
    - El asesor se resuelve desde el JWT.
    - Nunca consulta la agenda de otro asesor.
    """

    return responder_pregunta_agenda(
        db=db,
        usuario_actual=usuario_actual,
        pregunta=datos.pregunta,
    )
