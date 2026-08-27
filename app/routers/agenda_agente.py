from fastapi import (
    APIRouter,
    Depends,
)
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import require_roles
from app.models.usuario import Usuario
from app.schemas.agenda_agente import (
    AgendaAgenteConsultaEstructurada,
    AgendaAgentePregunta,
    AgendaAgenteRespuesta,
)
from app.services.agenda_agente_service import (
    consultar_agenda_estructurada,
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
        "Consultar la agenda en lenguaje natural"
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
    - El alcance se resuelve a partir del JWT (usuario_actual).
    - ASESOR: solo puede consultar su propia agenda. Nunca
      la de otro asesor.
    - ADMINISTRADOR / COORDINADOR: pueden consultar la
      agenda combinada de todo el equipo, o la de un asesor
      específico mencionándolo por nombre en la pregunta
      (ej. "agenda de Natalia hoy").
    """

    return responder_pregunta_agenda(
        db=db,
        usuario_actual=usuario_actual,
        pregunta=datos.pregunta,
    )

@router.post(
    "/consultar",
    response_model=AgendaAgenteRespuesta,
    summary="Consultar la agenda con filtros estructurados de n8n",
)
def consultar_agenda(
    datos: AgendaAgenteConsultaEstructurada,
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
    Endpoint estructurado para la orquestación n8n.

    SEGURIDAD:
    - No recibe asesor_id.
    - El alcance se resuelve a partir del JWT (usuario_actual).
    - ASESOR: siempre su propia agenda.
    - ADMINISTRADOR / COORDINADOR sin asesor_id propio:
      agenda combinada de todo el equipo.
    - Aplica exclusivamente filtros del dominio Agenda.
    """

    return consultar_agenda_estructurada(
        db=db,
        usuario_actual=usuario_actual,
        periodo=datos.periodo,
        ciudad=datos.ciudad,
        estado=datos.estado,
    )
