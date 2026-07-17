from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.auth import TokenRespuesta
from app.services.auth_service import iniciar_sesion
from app.dependencies.auth import get_current_user
from app.models.usuario import Usuario

router = APIRouter(
    prefix="/api/v1/auth",
    tags=["Autenticación"],
)

print("========== AUTH ROUTER CARGADO ==========")

@router.post(
    "/login",
    response_model=TokenRespuesta,
)
def login(
    formulario: Annotated[
        OAuth2PasswordRequestForm,
        Depends(),
    ],
    db: Session = Depends(get_db),
) -> TokenRespuesta:
    return iniciar_sesion(
        db=db,
        username=formulario.username,
        password=formulario.password,
    )

@router.get(
    "/me",
    response_model=TokenRespuesta,   # luego lo cambiaremos
)
def obtener_usuario_actual(
    usuario: Usuario = Depends(get_current_user),
):
    return {
        "access_token": "",
        "token_type": "bearer",
        "expires_in": 0,
        "usuario_id": usuario.id,
        "username": usuario.username,
        "rol": usuario.rol,
    }