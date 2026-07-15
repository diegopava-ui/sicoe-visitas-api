from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.usuario import Usuario
from app.repositories.usuario_repository import (
    buscar_asesor_activo,
    buscar_usuario_por_asesor,
    buscar_usuario_por_email,
    buscar_usuario_por_username,
    guardar_usuario,
)
from app.schemas.usuario import UsuarioCrear
from app.security import generar_hash_password


def crear_usuario(
    db: Session,
    datos: UsuarioCrear,
) -> Usuario:
    username = datos.username.strip().lower()
    email = str(datos.email).strip().lower()

    if buscar_usuario_por_username(db, username):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El nombre de usuario ya está registrado",
        )

    if buscar_usuario_por_email(db, email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El correo electrónico ya está registrado",
        )

    if datos.asesor_id is not None:
        asesor = buscar_asesor_activo(db, datos.asesor_id)

        if asesor is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="El asesor indicado no existe o está inactivo",
            )

        if buscar_usuario_por_asesor(db, datos.asesor_id):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="El asesor ya tiene un usuario asociado",
            )

    usuario = Usuario(
        asesor_id=datos.asesor_id,
        username=username,
        email=email,
        password_hash=generar_hash_password(datos.password),
        rol=datos.rol,
        activo=datos.activo,
    )

    try:
        return guardar_usuario(db, usuario)

    except IntegrityError as exc:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No fue posible crear el usuario por datos duplicados",
        ) from exc