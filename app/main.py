from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI

from app.config import get_settings
from app.database import check_database_connection

from app.routers.asesores import router as asesores_router

from app.routers.usuarios import router as usuarios_router

from app.routers.auth import router as auth_router

from app.routers.terceros import router as terceros_router

from app.routers.visitas import router as visitas_router

from app.routers.reportes import router as reportes_router

from fastapi.middleware.cors import CORSMiddleware



print("========== MAIN CARGADO ==========")


settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
)

app.include_router(asesores_router)
app.include_router(usuarios_router)
app.include_router(auth_router)
app.include_router(terceros_router)
app.include_router(visitas_router)
app.include_router(reportes_router)


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
