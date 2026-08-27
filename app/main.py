from datetime import datetime, timezone
from typing import Any
import os

from fastapi import FastAPI

from app.config import get_settings
from app.database import check_database_connection

from app.routers.asesores import router as asesores_router

from app.routers.usuarios import router as usuarios_router

from app.routers.auth import router as auth_router

from app.routers.terceros import router as terceros_router

from app.routers.visitas import router as visitas_router

from app.routers.reportes import router as reportes_router

from app.routers.notificaciones import router as notificaciones_router

from app.routers.calendario import router as calendario_router

from app.routers.agenda_agente import router as agenda_agente_router

from fastapi.middleware.cors import CORSMiddleware

from pathlib import Path

from fastapi.staticfiles import StaticFiles

from app.routers.catalogos import router as catalogos_router





print("========== MAIN CARGADO ==========")


settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
)

from app.routers.agenda_agente_proxima import router as agenda_agente_proxima_router

app.include_router(asesores_router)
app.include_router(usuarios_router)
app.include_router(auth_router)
app.include_router(terceros_router)
app.include_router(visitas_router)
app.include_router(reportes_router)
app.include_router(notificaciones_router)
app.include_router(calendario_router)
app.include_router(agenda_agente_router)
app.include_router(agenda_agente_proxima_router)
app.include_router(catalogos_router)

UPLOADS_DIR = Path(
    os.getenv("UPLOADS_DIR", "uploads")
)

try:
    UPLOADS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    app.mount(
        "/uploads",
        StaticFiles(directory=str(UPLOADS_DIR)),
        name="uploads",
    )
except OSError as error:
    # Si el contenedor no tiene permisos de escritura en esta
    # ruta (ej. un cambio de imagen/usuario en el despliegue),
    # la API sigue funcionando igual - solo queda deshabilitada
    # la descarga de archivos en /uploads hasta que se resuelva
    # el permiso o se configure UPLOADS_DIR a una ruta escribible.
    print(
        "ADVERTENCIA: no se pudo preparar la carpeta de "
        f"uploads en '{UPLOADS_DIR}': {error}. "
        "El resto de la API sigue funcionando normalmente."
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

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:8088",
    "http://127.0.0.1:8088",
    "https://sicoe-visitas-sicoe-visitas-frontend.tzfllg.easypanel.host",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

