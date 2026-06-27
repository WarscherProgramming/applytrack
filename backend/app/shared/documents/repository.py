import logging
from typing import TypeVar

from sqlalchemy import func, select

from app.shared.base_repository import BaseRepository
from app.shared.documents.model import DocumentBase

logger = logging.getLogger(__name__)

DocumentT = TypeVar("DocumentT", bound=DocumentBase)


class DocumentRepository(BaseRepository[DocumentT]):
    """
    Shared query logic for versioned document tables (resumes, cover letters).

    Subclasses bind a concrete model in __init__; this class adds the
    version-numbering and library-listing queries common to both.
    """

    def next_version(self, name: str) -> int:
        """Next 1-based version number for documents sharing `name`."""
        current_max = self.db.scalar(
            select(func.max(self.model.version)).where(self.model.name == name)
        )
        return (current_max or 0) + 1

    def list_paginated(
        self,
        *,
        query: str | None = None,
        name: str | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[DocumentT], int]:
        base = select(self.model)

        if query:
            like = f"%{query}%"
            base = base.where(
                self.model.name.ilike(like) | self.model.file_name.ilike(like)
            )
        if name is not None:
            base = base.where(self.model.name == name)

        total = self.db.scalar(select(func.count()).select_from(base.subquery())) or 0

        items = list(
            self.db.scalars(
                # Group documents by name (A→Z), newest version first within each
                # group — the library renders the latest version on top.
                base.order_by(
                    self.model.name.asc(),
                    self.model.version.desc(),
                )
                .offset(skip)
                .limit(limit)
            ).all()
        )
        return items, total
