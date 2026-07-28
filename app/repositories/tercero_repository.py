from sqlalchemy.orm import Session

from app.models.tercero import Tercero
from app.repositories.base_repository import BaseRepository


class TerceroRepository(BaseRepository[Tercero]):

    def __init__(self):
        super().__init__(Tercero)

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
    ) -> list[Tercero]:
        patron = f"%{texto.strip()}%"

        return (
            db.query(Tercero)
            .filter(
                Tercero.activo.is_(True),
                Tercero.deleted_at.is_(None),
                (
                    Tercero.razon_social.ilike(patron)
                    | Tercero.nombre_comercial.ilike(patron)
                    | Tercero.identificacion.ilike(patron)
                ),
            )
            .order_by(Tercero.razon_social.asc())
            .all()
        )


tercero_repository = TerceroRepository()