from app.modules.memory.service import MemoryService
from app.services.ai.handlers.base_handler import BaseHandler


class MemoryHandler(BaseHandler):

    def __init__(self, db):

        super().__init__(MemoryService(db))

    def execute(
        self,
        user_id: int,
        payload: dict,
    ):

        self.service.create_memory(
            user_id=user_id,
            content=payload["content"],
            category=payload.get(
                "category",
                "general",
            ),
            importance=payload.get(
                "importance",
                1,
            ),
        )
