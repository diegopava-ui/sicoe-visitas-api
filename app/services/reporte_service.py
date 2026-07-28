from fastapi import HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.repositories import reporte_repository


def _error_consulta(
    exc: SQLAlchemyError,
) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=(
            "No fue posible consultar los indicadores. "
            "Verifique que las vistas BI estén creadas."
        ),
    )


def consultar_resumen(
    db: Session,
) -> dict:
    try:
        resultado = (
            reporte_repository.obtener_resumen(db)
        )

        if resultado is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=(
                    "No se encontró información "
                    "para el resumen."
                ),
            )

        return resultado

    except HTTPException:
        raise
    except SQLAlchemyError as exc:
        raise _error_consulta(exc) from exc


def consultar_visitas_por_estado(
    db: Session,
) -> list[dict]:
    try:
        return (
            reporte_repository
            .obtener_visitas_por_estado(db)
        )
    except SQLAlchemyError as exc:
        raise _error_consulta(exc) from exc


def consultar_productividad_asesores(
    db: Session,
    limite: int,
) -> list[dict]:
    try:
        return (
            reporte_repository
            .obtener_productividad_asesores(
                db,
                limite,
            )
        )
    except SQLAlchemyError as exc:
        raise _error_consulta(exc) from exc


def consultar_actividad_terceros(
    db: Session,
    limite: int,
) -> list[dict]:
    try:
        return (
            reporte_repository
            .obtener_actividad_terceros(
                db,
                limite,
            )
        )
    except SQLAlchemyError as exc:
        raise _error_consulta(exc) from exc


def consultar_visitas_por_periodo(
    db: Session,
    limite: int,
) -> list[dict]:
    try:
        return (
            reporte_repository
            .obtener_visitas_por_periodo(
                db,
                limite,
            )
        )
    except SQLAlchemyError as exc:
        raise _error_consulta(exc) from exc


def consultar_compromisos_pendientes(
    db: Session,
    limite: int,
) -> list[dict]:
    try:
        return (
            reporte_repository
            .obtener_compromisos_pendientes(
                db,
                limite,
            )
        )
    except SQLAlchemyError as exc:
        raise _error_consulta(exc) from exc


def consultar_proximas_visitas(
    db: Session,
    dias: int,
    limite: int,
) -> list[dict]:
    try:
        return (
            reporte_repository
            .obtener_proximas_visitas(
                db,
                dias,
                limite,
            )
        )
    except SQLAlchemyError as exc:
        raise _error_consulta(exc) from exc


def consultar_satisfaccion(
    db: Session,
) -> list[dict]:
    try:
        return (
            reporte_repository
            .obtener_satisfaccion(db)
        )
    except SQLAlchemyError as exc:
        raise _error_consulta(exc) from exc


def consultar_cobertura_geografica(
    db: Session,
    limite: int,
) -> list[dict]:
    try:
        return (
            reporte_repository
            .obtener_cobertura_geografica(
                db,
                limite,
            )
        )
    except SQLAlchemyError as exc:
        raise _error_consulta(exc) from exc

def consultar_ultimo_analisis_ia(
    db: Session,
) -> dict:
    try:
        resultado = (
            reporte_repository
            .obtener_ultimo_analisis_ia(db)
        )

        if resultado is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=(
                    "Todavía no existe un análisis "
                    "ejecutivo generado con IA."
                ),
            )

        return resultado

    except HTTPException:
        raise
    except SQLAlchemyError as exc:
        raise _error_consulta(exc) from exc

