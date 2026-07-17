from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.asesor import Asesor
from app.models.usuario import Usuario

from datetime import datetime, timezone


def buscar_usuario_por_id(
    db: Session,
    usuario_id: int,
) -> Usuario | None:
    return db.scalar(
        select(Usuario).where(
            Usuario.id == usuario_id,
            Usuario.deleted_at.is_(None),
        )
    )


def buscar_usuario_por_username(
    db: Session,
    username: str,
) -> Usuario | None:
    return db.scalar(
        select(Usuario).where(
            Usuario.username == username,
        )
    )


def buscar_usuario_por_email(
    db: Session,
    email: str,
) -> Usuario | None:
    return db.scalar(
        select(Usuario).where(
            Usuario.email == email,
        )
    )


def buscar_usuario_por_asesor(
    db: Session,
    asesor_id: int,
) -> Usuario | None:
    return db.scalar(
        select(Usuario).where(
            Usuario.asesor_id == asesor_id,
        )
    )


def buscar_asesor_activo(
    db: Session,
    asesor_id: int,
) -> Asesor | None:
    return db.scalar(
        select(Asesor).where(
            Asesor.id == asesor_id,
            Asesor.activo.is_(True),
            Asesor.deleted_at.is_(None),
        )
    )


def guardar_usuario(
    db: Session,
    usuario: Usuario,
) -> Usuario:
    db.add(usuario)
    db.commit()
    db.refresh(usuario)

    return usuario

def actualizar_ultimo_acceso(
    db: Session,
    usuario: Usuario,
) -> Usuario:
    usuario.ultimo_acceso = datetime.now(timezone.utc)

    db.add(usuario)
    db.commit()
    db.refresh(usuario)

    return usuario