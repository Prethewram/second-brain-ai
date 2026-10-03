from app.modules.notes.service import NoteService
from app.services.ai.handlers.base_handler import BaseHandler


class NoteHandler(BaseHandler):

    def __init__(self, db):

        super().__init__(NoteService(db))

    def execute(
        self,
        user_id: int,
        payload: dict,
    ):

        self.service.create_note(
            user_id=user_id,
            title=payload["title"],
            content=payload["content"],
            category=payload.get(
                "category",
                "general",
            ),
            source=payload.get(
                "source",
                "ai",
            ),
        )
