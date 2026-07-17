from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.auth import TokenRespuesta
from app.services.auth_service import iniciar_sesion

from fastapi import APIRouter


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