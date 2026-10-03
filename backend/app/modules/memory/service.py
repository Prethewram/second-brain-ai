from app.common.exceptions import ValidationException
from app.core.base_service import BaseService
from app.modules.memory.repository import MemoryRepository


class MemoryService(BaseService):

    def __init__(self, db):

        super().__init__(MemoryRepository(db))

    @staticmethod
    def _validate_fields(content, category, importance):
        if not isinstance(content, str) or not content.strip():
            raise ValidationException("Content cannot be empty.")
        if not isinstance(category, str) or not category.strip():
            raise ValidationException("Category cannot be empty.")
        category = category.strip().lower()
        if len(category) > 100:
            raise ValidationException("Category cannot exceed 100 characters.")
        if isinstance(importance, bool) or not isinstance(importance, int):
            raise ValidationException("Importance must be an integer.")
        return content.strip(), category, importance

    def create_memory(
        self,
        user_id: int,
        content: str,
        category: str = "general",
        importance: int = 1,
    ):
        content, category, importance = self._validate_fields(
            content, category, importance
        )
        return self.repository.create(
            user_id=user_id,
            content=content,
            category=category,
            importance=importance,
        )

    def list_memories(
        self,
        user_id: int,
    ):

        return self.repository.get_all(user_id)

    def get_memory(
        self,
        user_id: int,
        memory_id: int,
    ):

        memory = self.get_or_404(memory_id)

        self.verify_owner(
            memory,
            user_id,
        )

        return memory

    def update_memory(
        self,
        user_id: int,
        memory_id: int,
        body,
    ):

        memory = self.get_memory(
            user_id=user_id,
            memory_id=memory_id,
        )

        content, category, importance = self._validate_fields(
            body.content,
            body.category,
            body.importance,
        )
        memory.content = content
        memory.category = category
        memory.importance = importance

        return self.repository.update(memory)

    def delete_memory(
        self,
        user_id: int,
        memory_id: int,
    ):

        memory = self.get_memory(
            user_id=user_id,
            memory_id=memory_id,
        )

        self.repository.delete(memory)
