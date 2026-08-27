from datetime import date, datetime, time
from typing import Any

from sqlalchemy.orm import Session

from app.services.pdf_generator import PDFGenerator
from app.services.visita_pdf_service import construir_modelo_visita_pdf


def _fecha(valor: date | datetime | None) -> str:
    if valor is None:
        return "No registrada"
    if isinstance(valor, datetime):
        valor = valor.date()
    return valor.strftime("%d/%m/%Y")


def _hora(valor: time | None) -> str:
    if valor is None:
        return "No registrada"
    return valor.strftime("%H:%M")


def _texto_amigable(valor: Any, predeterminado: str = "No registrado") -> str:
    if valor is None:
        return predeterminado
    texto = str(valor).strip()
    if not texto:
        return predeterminado
    return texto.replace("_", " ").capitalize()


def construir_modelo_asistencia_pdf(
    db: Session,
    visita_id: int,
) -> dict[str, Any]:
    """Construye el contrato documental del formato de asistencia."""

    base = construir_modelo_visita_pdf(
        db=db,
        visita_id=visita_id,
    )

    visita = base["visita"]
    empresa = base["empresa"]
    asesor = base["asesor"]

    return {
        "documento": {
            "tipo": "FORMATO DE ASISTENCIA",
            "version": "1.0",
            "codigo": base["documento"]["codigo"],
            "fecha_generacion": datetime.now().strftime(
                "%d/%m/%Y %H:%M"
            ),
            "logo_uri": base["documento"].get("logo_uri"),
        },
        "visita": {
            "fecha": _fecha(visita.get("fecha")),
            "hora_inicio": _hora(visita.get("hora_inicio")),
            "hora_fin": _hora(visita.get("hora_fin")),
            "servicio": visita.get("servicio") or "No registrado",
            "tipo": _texto_amigable(visita.get("tipo")),
            "participantes_esperados": (
                visita.get("cantidad_participantes") or 0
            ),
        },
        "empresa": {
            "nombre": empresa.get("nombre") or "No registrado",
            "nit": empresa.get("nit") or "No registrado",
            "direccion": empresa.get("direccion") or "No registrada",
            "ciudad": empresa.get("ciudad") or "No registrada",
            "departamento": (
                empresa.get("departamento") or "No registrado"
            ),
            "contacto_nombre": (
                empresa.get("contacto_nombre") or "No registrado"
            ),
        },
        "asesor": {
            "nombre": asesor.get("nombre") or "No registrado",
            "identificacion": (
                asesor.get("identificacion") or "No registrada"
            ),
        },
        "asistencia": {
            "filas": list(range(1, 21)),
        },
    }


def generar_pdf_asistencia(
    db: Session,
    visita_id: int,
) -> bytes:
    """Genera el formato PDF imprimible para registrar asistencia."""

    contexto = construir_modelo_asistencia_pdf(
        db=db,
        visita_id=visita_id,
    )

    generador = PDFGenerator()

    return generador.generar_pdf(
        plantilla="visitas/asistencia_v1.html",
        contexto=contexto,
    )
