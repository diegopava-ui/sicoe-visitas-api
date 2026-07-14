import logging
from typing import Any

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine, URL

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

database_url = URL.create(
    drivername="postgresql+psycopg",
    username=settings.db_user,
    password=settings.db_password,
    host=settings.db_host,
    port=settings.db_port,
    database=settings.db_name,
)

engine: Engine = create_engine(
    database_url,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
    connect_args={"connect_timeout": 3},
)


def check_database_connection() -> dict[str, Any]:
    try:
        with engine.connect() as connection:
            row = connection.execute(
                text(
                    """
                    SELECT
                        current_database() AS database_name,
                        current_user AS database_user,
                        version() AS database_version
                    """
                )
            ).mappings().one()

        return {
            "status": "connected",
            "database": row["database_name"],
            "user": row["database_user"],
            "version": row["database_version"],
        }

    except Exception:
        logger.exception("No fue posible conectar con PostgreSQL")

        return {
            "status": "error",
            "database": "unavailable",
            "detail": "No fue posible conectar con la base de datos",
        }