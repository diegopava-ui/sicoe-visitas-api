from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session


def _fila_unica(
    db: Session,
    consulta_sql: str,
    parametros: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    resultado = db.execute(
        text(consulta_sql),
        parametros or {},
    ).mappings().first()

    return dict(resultado) if resultado else None


def _filas(
    db: Session,
    consulta_sql: str,
    parametros: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    resultados = db.execute(
        text(consulta_sql),
        parametros or {},
    ).mappings().all()

    return [dict(fila) for fila in resultados]


def obtener_resumen(
    db: Session,
) -> dict[str, Any] | None:
    return _fila_unica(
        db,
        """
        SELECT *
        FROM vw_bi_resumen_visitas
        """,
    )


def obtener_visitas_por_estado(
    db: Session,
) -> list[dict[str, Any]]:
    return _filas(
        db,
        """
        SELECT *
        FROM vw_bi_visitas_por_estado
        """,
    )


def obtener_productividad_asesores(
    db: Session,
    limite: int,
) -> list[dict[str, Any]]:
    return _filas(
        db,
        """
        SELECT *
        FROM vw_bi_productividad_asesores
        ORDER BY
            total_visitas DESC,
            asesor_nombre
        LIMIT :limite
        """,
        {"limite": limite},
    )


def obtener_actividad_terceros(
    db: Session,
    limite: int,
) -> list[dict[str, Any]]:
    return _filas(
        db,
        """
        SELECT *
        FROM vw_bi_actividad_terceros
        ORDER BY
            total_visitas DESC,
            razon_social
        LIMIT :limite
        """,
        {"limite": limite},
    )


def obtener_visitas_por_periodo(
    db: Session,
    limite: int,
) -> list[dict[str, Any]]:
    return _filas(
        db,
        """
        SELECT *
        FROM vw_bi_visitas_por_periodo
        ORDER BY periodo_mes DESC
        LIMIT :limite
        """,
        {"limite": limite},
    )


def obtener_compromisos_pendientes(
    db: Session,
    limite: int,
) -> list[dict[str, Any]]:
    return _filas(
        db,
        """
        SELECT *
        FROM vw_bi_compromisos_pendientes
        ORDER BY
            CASE estado_compromiso
                WHEN 'VENCIDO' THEN 1
                WHEN 'PROXIMO_A_VENCER' THEN 2
                WHEN 'PENDIENTE' THEN 3
                WHEN 'SIN_FECHA' THEN 4
                ELSE 5
            END,
            proxima_visita NULLS LAST,
            fecha_visita DESC
        LIMIT :limite
        """,
        {"limite": limite},
    )


def obtener_proximas_visitas(
    db: Session,
    dias: int,
    limite: int,
) -> list[dict[str, Any]]:
    return _filas(
        db,
        """
        SELECT *
        FROM vw_bi_proximas_visitas
        WHERE fecha_visita <= CURRENT_DATE + :dias
        ORDER BY
            fecha_visita,
            hora_inicio NULLS LAST
        LIMIT :limite
        """,
        {
            "dias": dias,
            "limite": limite,
        },
    )


def obtener_satisfaccion(
    db: Session,
) -> list[dict[str, Any]]:
    return _filas(
        db,
        """
        SELECT *
        FROM vw_bi_satisfaccion
        """,
    )


def obtener_cobertura_geografica(
    db: Session,
    limite: int,
) -> list[dict[str, Any]]:
    return _filas(
        db,
        """
        SELECT *
        FROM vw_bi_cobertura_geografica
        ORDER BY
            total_visitas DESC,
            departamento,
            ciudad
        LIMIT :limite
        """,
        {"limite": limite},
    )

def obtener_ultimo_analisis_ia(
    db: Session,
) -> dict[str, Any] | None:
    return _fila_unica(
        db,
        """
        SELECT
            id,
            evento_id,
            informe_evento_id,
            modelo,
            openai_response_id,
            resumen_ejecutivo,
            hallazgos_json,
            riesgos_json,
            recomendaciones_json,
            mensaje_cierre,
            CASE
                WHEN jsonb_typeof(
                    contexto_anonimizado_json
                ) = 'object'
                THEN TRUE
                ELSE FALSE
            END AS contexto_anonimizado,
            created_at
        FROM public.analisis_ia_ejecutivo
        ORDER BY
            created_at DESC,
            id DESC
        LIMIT 1
        """,
    )

