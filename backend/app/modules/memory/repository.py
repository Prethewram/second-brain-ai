from sqlalchemy.orm import Session

from app.core.base_repository import BaseRepository
from app.models.memory import Memory

_UNSET = object()


class MemoryRepository(BaseRepository[Memory]):

    def __init__(self, db: Session):
        super().__init__(db, Memory)

    def create(
        self,
        user_id: int,
        content: str,
        category: str = "general",
        importance: int = 1,
    ):

        return super().create(
            user_id=user_id,
            content=content,
            category=category,
            importance=importance,
        )

    def get_all(self, user_id: int):

        return (
            self.db.query(Memory)
            .filter(Memory.user_id == user_id)
            .order_by(
                Memory.importance.desc(),
                Memory.created_at.desc(),
            )
            .all()
        )

    def get_by_id(self, memory_id: int):

        # Compatibility for callers using the original repository interface.
        return self.get(memory_id)

    def update(
        self,
        memory,
        content=_UNSET,
        category=_UNSET,
        importance=_UNSET,
    ):

        # Services pass the modified object; older callers pass field values.
        for field, value in {
            "content": content,
            "category": category,
            "importance": importance,
        }.items():
            if value is not _UNSET:
                setattr(memory, field, value)
        return super().update(memory)

    def get_top_memories(
        self,
        user_id: int,
        limit: int = 10,
    ):

        return (
            self.db.query(Memory)
            .filter(Memory.user_id == user_id)
            .order_by(
                Memory.importance.desc(),
                Memory.created_at.desc(),
            )
            .limit(limit)
            .all()
        )
