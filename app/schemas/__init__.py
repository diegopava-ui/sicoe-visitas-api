from app.schemas.asesor import (
    AsesorActualizar,
    AsesorBase,
    AsesorCrear,
    AsesorRespuesta,
)

from app.schemas.usuario import (
    UsuarioActualizar,
    UsuarioBase,
    UsuarioCrear,
    UsuarioRespuesta,
)

from app.schemas.visita import (
    VisitaActualizar,
    VisitaBase,
    VisitaCrear,
    VisitaListado,
    VisitaRespuesta,
)

from app.schemas.visita_evidencia import (
    VisitaEvidenciaActualizar,
    VisitaEvidenciaBase,
    VisitaEvidenciaCrear,
    VisitaEvidenciaRespuesta,
)

from app.schemas.tercero import (
    TerceroCreate,
    TerceroResponse,
    TerceroUpdate,
)

__all__ = [
    # Asesores
    "AsesorBase",
    "AsesorCrear",
    "AsesorActualizar",
    "AsesorRespuesta",

    # Usuarios
    "UsuarioBase",
    "UsuarioCrear",
    "UsuarioActualizar",
    "UsuarioRespuesta",

    # Visitas
    "VisitaBase",
    "VisitaCrear",
    "VisitaActualizar",
    "VisitaRespuesta",
    "VisitaListado",

    # Evidencias
    "VisitaEvidenciaBase",
    "VisitaEvidenciaCrear",
    "VisitaEvidenciaActualizar",
    "VisitaEvidenciaRespuesta",
]

from app.schemas.notificacion import (
    CanalNotificacion,
    EstadoNotificacion,
    NotificacionCrear,
    NotificacionRespuesta,
    PreferenciaNotificacionActualizar,
    PreferenciaNotificacionCrear,
    PreferenciaNotificacionRespuesta,
    SimulacionWhatsAppRespuesta,
    TipoDestinatario,
)
