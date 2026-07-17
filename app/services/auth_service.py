from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.usuario import Usuario
from app.repositories.usuario_repository import (
    actualizar_ultimo_acceso,
    buscar_usuario_por_username,
)
from app.schemas.auth import TokenRespuesta
from app.security import (
    crear_access_token,
    verificar_password,
)


settings = get_settings()


def autenticar_usuario(
    db: Session,
    username: str,
    password: str,
) -> Usuario:
    username_normalizado = username.strip().lower()

    usuario = buscar_usuario_por_username(
        db,
        username_normalizado,
    )

    credenciales_invalidas = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Usuario o contraseña incorrectos",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if usuario is None:
        raise credenciales_invalidas

    if usuario.deleted_at is not None:
        raise credenciales_invalidas

    if not usuario.activo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="El usuario se encuentra inactivo",
        )

    if not verificar_password(
        password,
        usuario.password_hash,
    ):
        raise credenciales_invalidas

    return usuario


def iniciar_sesion(
    db: Session,
    username: str,
    password: str,
) -> TokenRespuesta:
    usuario = autenticar_usuario(
        db,
        username,
        password,
    )

    access_token = crear_access_token(
        subject=str(usuario.id),
        datos_adicionales={
            "username": usuario.username,
            "rol": usuario.rol,
        },
    )

    actualizar_ultimo_acceso(db, usuario)

    return TokenRespuesta(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60,
        usuario_id=usuario.id,
        username=usuario.username,
        rol=usuario.rol,
    )