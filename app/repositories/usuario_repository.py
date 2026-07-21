from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.asesor import Asesor
from app.models.usuario import Usuario

from datetime import datetime, timezone

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
            Usuario.deleted_at.is_(None),
        )
    )


def buscar_usuario_por_email(
    db: Session,
    email: str,
) -> Usuario | None:
    return db.scalar(
        select(Usuario).where(
            Usuario.email == email,
            Usuario.deleted_at.is_(None),
        )
    )


def buscar_usuario_por_asesor(
    db: Session,
    asesor_id: int,
) -> Usuario | None:
    return db.scalar(
        select(Usuario).where(
            Usuario.asesor_id == asesor_id,
            Usuario.deleted_at.is_(None),
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

def listar_usuarios(
    db: Session,
    buscar: str | None = None,
    limite: int = 50,
    offset: int = 0,
) -> list[Usuario]:
    consulta = select(Usuario).where(
        Usuario.deleted_at.is_(None),
    )

    if buscar:
        termino = f"%{buscar.strip()}%"

        consulta = consulta.where(
            or_(
                Usuario.username.ilike(termino),
                Usuario.email.ilike(termino),
                Usuario.rol.ilike(termino),
            )
        )

    consulta = (
        consulta
        .order_by(Usuario.id)
        .offset(offset)
        .limit(limite)
    )

    return list(
        db.scalars(consulta).all()
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

def actualizar_usuario(
    db: Session,
    usuario: Usuario,
) -> Usuario:
    db.add(usuario)
    db.commit()
    db.refresh(usuario)

    return usuario
def desactivar_usuario(
    db: Session,
    usuario: Usuario,
) -> Usuario:
    fecha_actual = datetime.now(timezone.utc)

    usuario.activo = False
    usuario.deleted_at = fecha_actual
    usuario.updated_at = fecha_actual

    db.add(usuario)
    db.commit()
    db.refresh(usuario)

    return usuario


def reactivar_usuario(
    db: Session,
    usuario: Usuario,
) -> Usuario:
    usuario.activo = True
    usuario.deleted_at = None
    usuario.updated_at = datetime.now(timezone.utc)

    db.add(usuario)
    db.commit()
    db.refresh(usuario)

    return usuario

def buscar_usuario_por_id_incluyendo_eliminados(
    db: Session,
    usuario_id: int,
) -> Usuario | None:
    return db.scalar(
        select(Usuario).where(
            Usuario.id == usuario_id,
        )
    )