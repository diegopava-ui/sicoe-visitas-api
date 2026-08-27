from datetime import UTC, datetime

from sqlalchemy import or_
from sqlalchemy.orm import Query, Session

from app.models.tercero import Tercero
from app.repositories.base_repository import BaseRepository


ESTADOS_FILTRO_TERCERO = {
    "TODOS",
    "ACTIVOS",
    "INACTIVOS",
}


class TerceroRepository(BaseRepository[Tercero]):

    def __init__(self):
        super().__init__(Tercero)

    @staticmethod
    def _aplicar_filtro_estado(
        query: Query,
        estado: str,
    ) -> Query:
        estado_normalizado = estado.strip().upper()

        if estado_normalizado == "ACTIVOS":
            return query.filter(
                Tercero.activo.is_(True),
                Tercero.deleted_at.is_(None),
            )

        if estado_normalizado == "INACTIVOS":
            return query.filter(
                or_(
                    Tercero.activo.is_(False),
                    Tercero.deleted_at.is_not(None),
                )
            )

        # TODOS: no se limita por activo/deleted_at.
        return query

    def list_by_estado(
        self,
        db: Session,
        estado: str,
        offset: int = 0,
        limit: int = 20,
    ) -> list[Tercero]:
        query = db.query(Tercero)
        query = self._aplicar_filtro_estado(query, estado)

        return (
            query
            .order_by(Tercero.razon_social.asc())
            .offset(offset)
            .limit(limit)
            .all()
        )

    def count_by_estado(
        self,
        db: Session,
        estado: str,
    ) -> int:
        query = db.query(Tercero)
        query = self._aplicar_filtro_estado(query, estado)
        return query.count()

    def get_by_identificacion(
        self,
        db: Session,
        identificacion: str,
    ) -> Tercero | None:
        return (
            db.query(Tercero)
            .filter(
                Tercero.identificacion == identificacion,
                Tercero.activo.is_(True),
                Tercero.deleted_at.is_(None),
            )
            .first()
        )

    def get_by_identificacion_including_deleted(
        self,
        db: Session,
        identificacion: str,
    ) -> Tercero | None:
        return (
            db.query(Tercero)
            .filter(Tercero.identificacion == identificacion)
            .first()
        )

    def get_by_tipo(
        self,
        db: Session,
        tipo_tercero: str,
    ) -> list[Tercero]:
        return (
            db.query(Tercero)
            .filter(
                Tercero.tipo_tercero == tipo_tercero,
                Tercero.activo.is_(True),
                Tercero.deleted_at.is_(None),
            )
            .order_by(Tercero.razon_social.asc())
            .all()
        )

    def search(
        self,
        db: Session,
        texto: str,
        estado: str = "TODOS",
    ) -> list[Tercero]:
        patron = f"%{texto.strip()}%"

        query = db.query(Tercero).filter(
            (
                Tercero.razon_social.ilike(patron)
                | Tercero.nombre_comercial.ilike(patron)
                | Tercero.identificacion.ilike(patron)
                | Tercero.email.ilike(patron)
                | Tercero.telefono.ilike(patron)
                | Tercero.ciudad.ilike(patron)
            )
        )

        query = self._aplicar_filtro_estado(query, estado)

        return (
            query
            .order_by(Tercero.razon_social.asc())
            .all()
        )

    def reactivate(
        self,
        db: Session,
        tercero: Tercero,
    ) -> Tercero:
        ahora = datetime.now(UTC)

        tercero.activo = True
        tercero.deleted_at = None

        if hasattr(tercero, "updated_at"):
            tercero.updated_at = ahora

        db.commit()
        db.refresh(tercero)

        return tercero


tercero_repository = TerceroRepository()
