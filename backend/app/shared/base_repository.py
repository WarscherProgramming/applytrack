import logging
from typing import Any, Generic, TypeVar
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.exceptions.http import NotFoundError
from app.shared.base_model import BaseModel

logger = logging.getLogger(__name__)

ModelT = TypeVar("ModelT", bound=BaseModel)


class BaseRepository(Generic[ModelT]):
    """
    Generic CRUD repository.

    Feature repositories subclass this and add domain-specific query methods.
    This class never calls session.commit() — transaction boundaries are owned
    by get_db() in database/session.py, which commits on success and rolls
    back on any exception.
    """

    def __init__(self, model: type[ModelT], db: Session) -> None:
        self.model = model
        self.db = db

    def get(self, id: UUID) -> ModelT | None:
        # Session.get() checks the identity map before hitting the DB,
        # avoiding a round-trip if the object was loaded earlier in the request.
        return self.db.get(self.model, id)

    def get_or_raise(self, id: UUID) -> ModelT:
        instance = self.get(id)
        if instance is None:
            raise NotFoundError(self.model.__name__, id)
        return instance

    def get_all(self, *, skip: int = 0, limit: int = 100) -> list[ModelT]:
        stmt = select(self.model).offset(skip).limit(limit)
        return list(self.db.scalars(stmt).all())

    def create(self, data: dict[str, Any]) -> ModelT:
        instance = self.model(**data)
        self.db.add(instance)
        self.db.flush()  # assigns id without committing
        logger.debug("Created %s id=%s", self.model.__name__, instance.id)
        return instance

    def update(self, instance: ModelT, data: dict[str, Any]) -> ModelT:
        for key, value in data.items():
            setattr(instance, key, value)
        self.db.flush()
        logger.debug("Updated %s id=%s", self.model.__name__, instance.id)
        return instance

    def delete(self, instance: ModelT) -> None:
        self.db.delete(instance)
        self.db.flush()
        logger.debug("Deleted %s id=%s", self.model.__name__, instance.id)
