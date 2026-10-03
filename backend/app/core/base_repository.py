from __future__ import annotations

from typing import Generic, TypeVar

from sqlalchemy.orm import Session

ModelType = TypeVar("ModelType")


class BaseRepository(Generic[ModelType]):

    def __init__(
        self,
        db: Session,
        model: type[ModelType],
    ):
        self.db = db
        self.model = model

    def create(self, **kwargs) -> ModelType:

        obj = self.model(**kwargs)

        self.db.add(obj)

        self.db.commit()

        self.db.refresh(obj)

        return obj

    def get(
        self,
        obj_id: int,
    ) -> ModelType | None:

        return self.db.query(self.model).filter(self.model.id == obj_id).first()

    def list(self):

        return self.db.query(self.model).all()

    def get_by(self, **filters) -> ModelType | None:
        return self.db.query(self.model).filter_by(**filters).first()

    def list_by(self, **filters) -> list[ModelType]:
        return self.db.query(self.model).filter_by(**filters).all()

    def exists(self, **filters) -> bool:
        query = self.db.query(self.model).filter_by(**filters)
        return bool(self.db.query(query.exists()).scalar())

    def update(
        self,
        obj: ModelType,
    ) -> ModelType:

        self.db.commit()

        self.db.refresh(obj)

        return obj

    def delete(
        self,
        obj: ModelType,
    ):

        self.db.delete(obj)

        self.db.commit()
