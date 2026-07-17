from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt import ExpiredSignatureError, InvalidTokenError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.usuario import Usuario
from app.repositories.usuario_repository import buscar_usuario_por_id
from app.security import decodificar_access_token

from fastapi import status


oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login",
)


def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Session = Depends(get_db),
) -> Usuario:
    credenciales_invalidas = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No fue posible validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )

def require_roles(*roles_permitidos):
    def dependency(usuario: Usuario = Depends(get_current_user)):
        if usuario.rol not in roles_permitidos:
            raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para realizar esta acción.",
            )
        return usuario

    return dependency

    try:
        payload = decodificar_access_token(token)

        if payload.get("type") != "access":
            raise credenciales_invalidas

        subject = payload.get("sub")

        if subject is None:
            raise credenciales_invalidas

        usuario_id = int(subject)

    except ExpiredSignatureError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="El token ha expirado",
            headers={"WWW-Authenticate": "Bearer"},
        ) from error

    except (InvalidTokenError, TypeError, ValueError) as error:
        raise credenciales_invalidas from error

    usuario = buscar_usuario_por_id(db, usuario_id)

    if usuario is None or usuario.deleted_at is not None:
        raise credenciales_invalidas

    if not usuario.activo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="El usuario se encuentra inactivo",
        )

    return usuario