from app.modules.tasks.service import TaskService
from app.services.ai.handlers.base_handler import BaseHandler


class TaskHandler(BaseHandler):

    def __init__(self, db):

        super().__init__(TaskService(db))

    def execute(
        self,
        user_id: int,
        payload: dict,
    ):

        self.service.create_task(
            user_id=user_id,
            title=payload["title"],
            description=payload.get("description"),
            priority=payload.get(
                "priority",
                "medium",
            ),
            deadline=payload.get("deadline"),
        )
