from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import require_roles
from app.models.usuario import Usuario
from app.schemas.reporte import (
    ActividadTerceroResponse,
    CoberturaGeograficaResponse,
    CompromisoPendienteResponse,
    ProductividadAsesorResponse,
    ProximaVisitaResponse,
    ResumenVisitasResponse,
    SatisfaccionResponse,
    UltimoAnalisisIAResponse,
    VisitasPorEstadoResponse,
    VisitasPorPeriodoResponse,
)
from app.services.reporte_service import (
    consultar_actividad_terceros,
    consultar_cobertura_geografica,
    consultar_compromisos_pendientes,
    consultar_productividad_asesores,
    consultar_proximas_visitas,
    consultar_resumen,
    consultar_satisfaccion,
    consultar_ultimo_analisis_ia,
    consultar_visitas_por_estado,
    consultar_visitas_por_periodo,
)


router = APIRouter(
    prefix="/api/v1/reportes",
    tags=["Reportes BI"],
)


RolesReportes = Depends(
    require_roles(
        "ADMINISTRADOR",
        "COORDINADOR",
    )
)


@router.get(
    "/resumen",
    response_model=ResumenVisitasResponse,
)
def get_resumen(
    db: Session = Depends(get_db),
    usuario_actual: Usuario = RolesReportes,
):
    return consultar_resumen(db)


@router.get(
    "/visitas-por-estado",
    response_model=list[VisitasPorEstadoResponse],
)
def get_visitas_por_estado(
    db: Session = Depends(get_db),
    usuario_actual: Usuario = RolesReportes,
):
    return consultar_visitas_por_estado(db)


@router.get(
    "/productividad-asesores",
    response_model=list[ProductividadAsesorResponse],
)
def get_productividad_asesores(
    limite: int = Query(
        default=20,
        ge=1,
        le=100,
    ),
    db: Session = Depends(get_db),
    usuario_actual: Usuario = RolesReportes,
):
    return consultar_productividad_asesores(
        db,
        limite,
    )


@router.get(
    "/actividad-terceros",
    response_model=list[ActividadTerceroResponse],
)
def get_actividad_terceros(
    limite: int = Query(
        default=20,
        ge=1,
        le=100,
    ),
    db: Session = Depends(get_db),
    usuario_actual: Usuario = RolesReportes,
):
    return consultar_actividad_terceros(
        db,
        limite,
    )


@router.get(
    "/visitas-por-periodo",
    response_model=list[VisitasPorPeriodoResponse],
)
def get_visitas_por_periodo(
    limite: int = Query(
        default=12,
        ge=1,
        le=60,
    ),
    db: Session = Depends(get_db),
    usuario_actual: Usuario = RolesReportes,
):
    return consultar_visitas_por_periodo(
        db,
        limite,
    )


@router.get(
    "/compromisos-pendientes",
    response_model=list[CompromisoPendienteResponse],
)
def get_compromisos_pendientes(
    limite: int = Query(
        default=50,
        ge=1,
        le=200,
    ),
    db: Session = Depends(get_db),
    usuario_actual: Usuario = RolesReportes,
):
    return consultar_compromisos_pendientes(
        db,
        limite,
    )


@router.get(
    "/proximas-visitas",
    response_model=list[ProximaVisitaResponse],
)
def get_proximas_visitas(
    dias: int = Query(
        default=30,
        ge=0,
        le=365,
    ),
    limite: int = Query(
        default=100,
        ge=1,
        le=200,
    ),
    db: Session = Depends(get_db),
    usuario_actual: Usuario = RolesReportes,
):
    return consultar_proximas_visitas(
        db,
        dias,
        limite,
    )


@router.get(
    "/satisfaccion",
    response_model=list[SatisfaccionResponse],
)
def get_satisfaccion(
    db: Session = Depends(get_db),
    usuario_actual: Usuario = RolesReportes,
):
    return consultar_satisfaccion(db)


@router.get(
    "/cobertura-geografica",
    response_model=list[CoberturaGeograficaResponse],
)
def get_cobertura_geografica(
    limite: int = Query(
        default=100,
        ge=1,
        le=500,
    ),
    db: Session = Depends(get_db),
    usuario_actual: Usuario = RolesReportes,
):
    return consultar_cobertura_geografica(
        db,
        limite,
    )

@router.get(
    "/analisis-ia/ultimo",
    response_model=UltimoAnalisisIAResponse,
)
def get_ultimo_analisis_ia(
    db: Session = Depends(get_db),
    usuario_actual: Usuario = RolesReportes,
):
    return consultar_ultimo_analisis_ia(db)

