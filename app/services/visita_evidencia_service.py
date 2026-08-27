import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.visita import Visita
from app.models.visita_evidencia import VisitaEvidencia

# Carpeta raíz donde se guardan todos los archivos subidos.
# Debe coincidir con el mount de StaticFiles en main.py.
UPLOADS_DIR = Path("uploads")

EXTENSIONES_PERMITIDAS = {
    ".pdf",
    ".jpg",
    ".jpeg",
    ".png",
}

TAMANO_MAXIMO_BYTES = 10 * 1024 * 1024  # 10 MB

TIPOS_ARCHIVO_VALIDOS = {
    "FOTO",
    "PDF",
    "VIDEO",
    "AUDIO",
    "OTRO",
}


def _validar_archivo(
    archivo: UploadFile,
) -> str:
    nombre_original = archivo.filename or ""
    extension = Path(nombre_original).suffix.lower()

    if extension not in EXTENSIONES_PERMITIDAS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "Tipo de archivo no permitido. "
                "Solo se aceptan PDF, JPG o PNG."
            ),
        )

    return extension


def _guardar_archivo_en_disco(
    visita_id: int,
    archivo: UploadFile,
    extension: str,
) -> tuple[str, str]:
    """
    Guarda el archivo físicamente en
    uploads/visitas/{visita_id}/ con un
    nombre único, y devuelve
    (nombre_archivo_original, url_relativa).
    """

    carpeta_visita = (
        UPLOADS_DIR / "visitas" / str(visita_id)
    )
    carpeta_visita.mkdir(
        parents=True,
        exist_ok=True,
    )

    nombre_unico = f"{uuid.uuid4().hex}{extension}"
    ruta_destino = carpeta_visita / nombre_unico

    contenido = archivo.file.read()

    if len(contenido) > TAMANO_MAXIMO_BYTES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="El archivo supera el tamaño máximo permitido (10 MB).",
        )

    with open(ruta_destino, "wb") as destino:
        destino.write(contenido)

    url_relativa = (
        f"/uploads/visitas/{visita_id}/{nombre_unico}"
    )

    return archivo.filename or nombre_unico, url_relativa


def crear_evidencia(
    db: Session,
    visita_id: int,
    archivo: UploadFile,
    tipo_archivo: str,
    descripcion: str | None,
    usuario_actual_id: int,
) -> VisitaEvidencia:
    visita = db.get(Visita, visita_id)

    if visita is None or visita.deleted_at is not None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="La visita no existe.",
        )

    tipo_normalizado = tipo_archivo.strip().upper()

    if tipo_normalizado not in TIPOS_ARCHIVO_VALIDOS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "tipo_archivo inválido. Debe ser uno de: "
                f"{', '.join(sorted(TIPOS_ARCHIVO_VALIDOS))}."
            ),
        )

    extension = _validar_archivo(archivo)

    nombre_archivo, url_archivo = _guardar_archivo_en_disco(
        visita_id=visita_id,
        archivo=archivo,
        extension=extension,
    )

    evidencia = VisitaEvidencia(
        visita_id=visita_id,
        nombre_archivo=nombre_archivo,
        url_archivo=url_archivo,
        tipo_archivo=tipo_normalizado,
        descripcion=descripcion,
        created_by=usuario_actual_id,
        updated_by=usuario_actual_id,
    )

    db.add(evidencia)
    db.commit()
    db.refresh(evidencia)

    return evidencia


def listar_evidencias(
    db: Session,
    visita_id: int,
) -> list[VisitaEvidencia]:
    consulta = (
        select(VisitaEvidencia)
        .where(
            VisitaEvidencia.visita_id == visita_id,
            VisitaEvidencia.activo.is_(True),
            VisitaEvidencia.deleted_at.is_(None),
        )
        .order_by(VisitaEvidencia.created_at.desc())
    )

    return list(db.scalars(consulta).all())


def eliminar_evidencia(
    db: Session,
    visita_id: int,
    evidencia_id: int,
    usuario_actual_id: int,
) -> None:
    evidencia = db.get(VisitaEvidencia, evidencia_id)

    if (
        evidencia is None
        or evidencia.visita_id != visita_id
        or evidencia.deleted_at is not None
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El adjunto no existe.",
        )

    evidencia.activo = False
    evidencia.deleted_at = datetime.now(timezone.utc)
    evidencia.updated_by = usuario_actual_id

    db.commit()
