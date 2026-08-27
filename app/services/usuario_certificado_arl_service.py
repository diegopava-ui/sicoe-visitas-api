import uuid
from datetime import date, datetime, timezone
from pathlib import Path

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.usuario import Usuario
from app.models.usuario_certificado_arl import UsuarioCertificadoArl

# Misma carpeta raíz que usa visita_evidencia_service.py
UPLOADS_DIR = Path("uploads")

EXTENSIONES_PERMITIDAS = {
    ".pdf",
    ".jpg",
    ".jpeg",
    ".png",
}

TAMANO_MAXIMO_BYTES = 10 * 1024 * 1024  # 10 MB


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
    usuario_id: int,
    archivo: UploadFile,
    extension: str,
) -> tuple[str, str]:
    carpeta_usuario = (
        UPLOADS_DIR / "usuarios" / str(usuario_id) / "arl"
    )
    carpeta_usuario.mkdir(
        parents=True,
        exist_ok=True,
    )

    nombre_unico = f"{uuid.uuid4().hex}{extension}"
    ruta_destino = carpeta_usuario / nombre_unico

    contenido = archivo.file.read()

    if len(contenido) > TAMANO_MAXIMO_BYTES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="El archivo supera el tamaño máximo permitido (10 MB).",
        )

    with open(ruta_destino, "wb") as destino:
        destino.write(contenido)

    url_relativa = (
        f"/uploads/usuarios/{usuario_id}/arl/{nombre_unico}"
    )

    return archivo.filename or nombre_unico, url_relativa


def crear_certificado_arl(
    db: Session,
    usuario_id: int,
    archivo: UploadFile,
    fecha_vigencia: date | None,
    usuario_actual_id: int,
) -> UsuarioCertificadoArl:
    usuario = db.get(Usuario, usuario_id)

    if usuario is None or usuario.deleted_at is not None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El usuario no existe.",
        )

    extension = _validar_archivo(archivo)

    nombre_archivo, url_archivo = _guardar_archivo_en_disco(
        usuario_id=usuario_id,
        archivo=archivo,
        extension=extension,
    )

    certificado = UsuarioCertificadoArl(
        usuario_id=usuario_id,
        nombre_archivo=nombre_archivo,
        url_archivo=url_archivo,
        fecha_vigencia=fecha_vigencia,
        created_by=usuario_actual_id,
        updated_by=usuario_actual_id,
    )

    db.add(certificado)
    db.commit()
    db.refresh(certificado)

    return certificado


def listar_certificados_arl(
    db: Session,
    usuario_id: int,
) -> list[UsuarioCertificadoArl]:
    consulta = (
        select(UsuarioCertificadoArl)
        .where(
            UsuarioCertificadoArl.usuario_id == usuario_id,
            UsuarioCertificadoArl.activo.is_(True),
            UsuarioCertificadoArl.deleted_at.is_(None),
        )
        .order_by(UsuarioCertificadoArl.created_at.desc())
    )

    return list(db.scalars(consulta).all())


def eliminar_certificado_arl(
    db: Session,
    usuario_id: int,
    certificado_id: int,
    usuario_actual_id: int,
) -> None:
    certificado = db.get(
        UsuarioCertificadoArl,
        certificado_id,
    )

    if (
        certificado is None
        or certificado.usuario_id != usuario_id
        or certificado.deleted_at is not None
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El certificado no existe.",
        )

    certificado.activo = False
    certificado.deleted_at = datetime.now(timezone.utc)
    certificado.updated_by = usuario_actual_id

    db.commit()
