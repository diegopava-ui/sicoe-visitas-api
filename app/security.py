from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from pwdlib import PasswordHash

from app.config import get_settings


settings = get_settings()
password_hash = PasswordHash.recommended()


def generar_hash_password(password: str) -> str:
    return password_hash.hash(password)


def verificar_password(
    password_plano: str,
    password_guardado: str,
) -> bool:
    return password_hash.verify(
        password_plano,
        password_guardado,
    )


def crear_access_token(
    subject: str,
    datos_adicionales: dict[str, Any] | None = None,
) -> str:
    ahora = datetime.now(timezone.utc)

    payload: dict[str, Any] = {
        "sub": subject,
        "iat": ahora,
        "exp": ahora
        + timedelta(
            minutes=settings.access_token_expire_minutes,
        ),
        "type": "access",
    }

    if datos_adicionales:
        payload.update(datos_adicionales)

    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )