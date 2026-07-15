from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from pwdlib import PasswordHash

from app.config import get_settings


settings = get_settings()

password_hash = PasswordHash.recommended()


def generar_hash_password(password: str) -> str:
    """Genera un hash irreversible para almacenar la contraseña."""
    return password_hash.hash(password)


def verificar_password(password_plano: str, password_guardado: str) -> bool:
    """Verifica una contraseña contra el hash almacenado."""
    return password_hash.verify(password_plano, password_guardado)


def crear_access_token(
    subject: str,
    datos_adicionales: dict[str, Any] | None = None,
) -> str:
    ahora = datetime.now(timezone.utc)
    expiracion = ahora + timedelta(
        minutes=settings.access_token_expire_minutes
    )

    payload: dict[str, Any] = {
        "sub": subject,
        "iat": ahora,
        "exp": expiracion,
    }

    if datos_adicionales:
        payload.update(datos_adicionales)

    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )