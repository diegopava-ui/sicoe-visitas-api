from datetime import UTC, datetime
from typing import Generic, Type, TypeVar

from sqlalchemy.orm import Query, Session


ModelType = TypeVar("ModelType")


class BaseRepository(Generic[ModelType]):

    def __init__(self, model: Type[ModelType]):
        self.model = model

    def base_query(
        self,
        db: Session,
        incluir_inactivos: bool = False,
    ) -> Query:
        query = db.query(self.model)

        if not incluir_inactivos:
            if hasattr(self.model, "activo"):
                query = query.filter(
                    self.model.activo.is_(True)
                )

            if hasattr(self.model, "deleted_at"):
                query = query.filter(
                    self.model.deleted_at.is_(None)
                )

        return query

    def get_all(
        self,
        db: Session,
        offset: int = 0,
        limit: int = 20,
    ) -> list[ModelType]:
        return (
            self.base_query(db)
            .offset(offset)
            .limit(limit)
            .all()
        )

    def count(
        self,
        db: Session,
    ) -> int:
        return self.base_query(db).count()

    def get_by_id(
        self,
        db: Session,
        item_id: int,
        incluir_inactivos: bool = False,
    ) -> ModelType | None:
        return (
            self.base_query(
                db,
                incluir_inactivos=incluir_inactivos,
            )
            .filter(self.model.id == item_id)
            .first()
        )

    def create(
        self,
        db: Session,
        data,
    ) -> ModelType:
        valores = (
            data.model_dump()
            if hasattr(data, "model_dump")
            else data
        )

        obj = self.model(**valores)

        db.add(obj)
        db.commit()
        db.refresh(obj)

        return obj

    def update(
        self,
        db: Session,
        obj: ModelType,
        data,
    ) -> ModelType:
        valores = (
            data.model_dump(exclude_unset=True)
            if hasattr(data, "model_dump")
            else data
        )

        for campo, valor in valores.items():
            setattr(obj, campo, valor)

        if hasattr(obj, "updated_at"):
            obj.updated_at = datetime.now(UTC)

        db.commit()
        db.refresh(obj)

        return obj

    def soft_delete(
        self,
        db: Session,
        obj: ModelType,
    ) -> ModelType:
        ahora = datetime.now(UTC)

        if hasattr(obj, "activo"):
            obj.activo = False

        if hasattr(obj, "deleted_at"):
            obj.deleted_at = ahora

        if hasattr(obj, "updated_at"):
            obj.updated_at = ahora

        db.commit()
        db.refresh(obj)

        return obj