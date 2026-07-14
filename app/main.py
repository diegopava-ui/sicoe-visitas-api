from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI

from app.config import get_settings
from app.database import check_database_connection

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
)


@app.get("/")
def inicio() -> dict[str, str]:
    return {
        "mensaje": "Bienvenido a SICOE VISITAS API",
        "documentacion": "/docs",
    }


@app.get("/health")
def health() -> dict[str, Any]:
    database = check_database_connection()

    return {
        "status": "OK" if database["status"] == "connected" else "DEGRADED",
        "fecha": datetime.now(timezone.utc).isoformat(),
        "api": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "database": database,
    }