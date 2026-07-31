from pathlib import Path

from app.services.pdf_generator import PDFGenerator

from datetime import datetime
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.asesor import Asesor
from app.models.tercero import Tercero
from app.models.visita import Visita
from app.models.visita_evidencia import VisitaEvidencia
from app.repositories.visita_pdf_repository import (
    obtener_evidencias_activas,
    obtener_visita_para_pdf,
)

BASE_DIR = Path(__file__).resolve().parent.parent
LOGO_PATH = BASE_DIR / "static" / "logos" / "logo-sicoe.png"

def _texto(valor: Any, valor_predeterminado: str = "No registrado") -> str:
    """
    Convierte valores nulos o vacíos en un texto seguro
    para mostrar dentro del informe.
    """
    if valor is None:
        return valor_predeterminado

    texto = str(valor).strip()

    return texto if texto else valor_predeterminado


def _nombre_completo_asesor(asesor: Asesor | None) -> str:
    """
    Construye el nombre completo del asesor sin dejar
    espacios dobles ni valores None.
    """
    if asesor is None:
        return "Asesor no disponible"

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


def _datos_empresa(
    visita: Visita,
    tercero: Tercero | None,
) -> dict[str, Any]:
    """
    Prioriza la información registrada directamente
    en la visita.

    Cuando un dato no está disponible, intenta obtenerlo
    del tercero relacionado.
    """
    return {
        "nombre": _texto(
            visita.empresa
            or (tercero.razon_social if tercero else None)
        ),
        "nombre_comercial": _texto(
            tercero.nombre_comercial if tercero else None
        ),
        "nit": _texto(
            visita.nit
            or (tercero.identificacion if tercero else None)
        ),
        "direccion": _texto(
            visita.direccion
            or (tercero.direccion if tercero else None)
        ),
        "ciudad": _texto(
            visita.ciudad
            or (tercero.ciudad if tercero else None)
        ),
        "departamento": _texto(
            visita.departamento
            or (tercero.departamento if tercero else None)
        ),
        "contacto_nombre": _texto(
            visita.contacto_nombre
            or (tercero.contacto_nombre if tercero else None)
        ),
        "cargo_contacto": _texto(visita.cargo_contacto),
        "telefono": _texto(
            visita.telefono_contacto
            or (tercero.contacto_telefono if tercero else None)
            or (tercero.telefono if tercero else None)
        ),
        "correo": _texto(
            visita.email_contacto
            or (tercero.contacto_email if tercero else None)
            or (tercero.email if tercero else None)
        ),
    }


def _datos_asesor(
    asesor: Asesor | None,
) -> dict[str, Any]:
    if asesor is None:
        return {
            "id": None,
            "nombre": "Asesor no disponible",
            "identificacion": "No registrada",
            "email": "No registrado",
            "telefono": "No registrado",
            "cargo": "No registrado",
        }

    return {
        "id": asesor.id,
        "nombre": _nombre_completo_asesor(asesor),
        "identificacion": _texto(asesor.identificacion),
        "email": _texto(asesor.email),
        "telefono": _texto(asesor.telefono),
        "cargo": _texto(asesor.cargo),
    }


def _datos_evidencia(
    evidencia: VisitaEvidencia,
) -> dict[str, Any]:
    return {
        "id": evidencia.id,
        "nombre_archivo": evidencia.nombre_archivo,
        "url_archivo": evidencia.url_archivo,
        "tipo_archivo": evidencia.tipo_archivo,
        "descripcion": _texto(
            evidencia.descripcion,
            valor_predeterminado="Sin descripción",
        ),
        "fecha_registro": evidencia.created_at,
    }


def construir_modelo_visita_pdf(
    db: Session,
    visita_id: int,
) -> dict[str, Any]:
    """
    Consulta una visita y construye el modelo de datos
    que posteriormente consumirá la plantilla HTML.

    Esta función todavía no genera el PDF.
    """
    try:
        visita = obtener_visita_para_pdf(
            db=db,
            visita_id=visita_id,
        )

        if visita is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="La visita solicitada no existe o fue eliminada.",
            )

        evidencias = obtener_evidencias_activas(visita)

        return {
            "documento": {
                "tipo": "INFORME DE VISITA",
                "version": "1.0",
                "codigo": f"VIS-{visita.id:06d}",
                "fecha_generacion": datetime.now(),
                "logo_uri": (
                    LOGO_PATH.as_uri()
                    if LOGO_PATH.exists()
                    else None
                ),
            },
            "empresa": _datos_empresa(
                visita=visita,
                tercero=visita.tercero,
            ),
            "visita": {
                "id": visita.id,
                "fecha": visita.fecha_visita,
                "hora_inicio": visita.hora_inicio,
                "hora_fin": visita.hora_fin,
                "servicio": _texto(visita.servicio),
                "tipo": _texto(visita.tipo_visita),
                "estado": _texto(visita.estado),
                "origen_registro": _texto(
                    visita.origen_registro
                ),
                "cantidad_participantes": (
                    visita.cantidad_participantes or 0
                ),
                "duracion_minutos": (
                    visita.duracion_minutos or 0
                ),
                "objetivo": _texto(
                    visita.objetivo,
                    valor_predeterminado="Sin información registrada",
                ),
                "desarrollo": _texto(
                    visita.desarrollo,
                    valor_predeterminado="Sin información registrada",
                ),
                "resultado": _texto(
                    visita.resultado,
                    valor_predeterminado="Sin información registrada",
                ),
                "compromisos": _texto(
                    visita.compromisos,
                    valor_predeterminado="Sin compromisos registrados",
                ),
                "observaciones": _texto(
                    visita.observaciones,
                    valor_predeterminado="Sin observaciones registradas",
                ),
                "nivel_satisfaccion": _texto(
                    visita.nivel_satisfaccion
                ),
                "proxima_visita": visita.proxima_visita,
            },
            "ubicacion": {
                "latitud": (
                    float(visita.latitud)
                    if visita.latitud is not None
                    else None
                ),
                "longitud": (
                    float(visita.longitud)
                    if visita.longitud is not None
                    else None
                ),
            },
            "asesor": _datos_asesor(visita.asesor),
            "evidencias": [
                _datos_evidencia(evidencia)
                for evidencia in evidencias
            ],
            "firmas": {
                "cliente_url": visita.firma_cliente_url,
                "asesor_disponible": visita.asesor is not None,
            },
            "trazabilidad": {
                "creado_en": visita.created_at,
                "actualizado_en": visita.updated_at,
                "creado_por": visita.created_by,
                "actualizado_por": visita.updated_by,
            },
        }

    except HTTPException:
        raise

    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "No fue posible consultar la información "
                "necesaria para generar el informe."
            ),
        ) from exc

def generar_pdf_visita(
    db: Session,
    visita_id: int,
) -> bytes:
    """
    Genera el informe corporativo de una visita
    y devuelve el documento PDF en memoria.
    """
    contexto = construir_modelo_visita_pdf(
        db=db,
        visita_id=visita_id,
    )

    generador = PDFGenerator()

    return generador.generar_pdf(
        plantilla="visitas/visita_v2.html",
        contexto=contexto,
    )    