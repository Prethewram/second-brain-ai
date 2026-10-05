from sqlalchemy.orm import Session

from app.core.base_repository import BaseRepository
from app.models.task import Task


class TaskRepository(BaseRepository[Task]):

    def __init__(self, db: Session):
        super().__init__(db, Task)

    def create(
        self,
        user_id: int,
        title: str,
        description: str | None = None,
        priority: str = "medium",
        deadline: str | None = None,
        meeting_id: int | None = None,
    ) -> Task:

        return super().create(
            user_id=user_id,
            title=title,
            description=description,
            priority=priority,
            deadline=deadline,
            meeting_id=meeting_id,
        )

    def get(
        self,
        task_id: int,
    ) -> Task | None:

        return super().get(task_id)

    def list_by_user(
        self,
        user_id: int,
    ) -> list[Task]:

        return (
            self.db.query(Task)
            .filter(Task.user_id == user_id)
            .order_by(Task.created_at.desc())
            .all()
        )

    def complete(
        self,
        task_id: int | Task,
    ) -> Task | None:

        # Accept the service's owned object and retain legacy ID-based calls.
        task = task_id if isinstance(task_id, Task) else self.get(task_id)

        if task is None:
            return None

        task.completed = True

        return self.update(task)

    def delete(
        self,
        task_id: int | Task,
    ) -> bool:

        task = task_id if isinstance(task_id, Task) else self.get(task_id)

        if task is None:
            return False

        super().delete(task)

        return True

    def get_active_tasks(
        self,
        user_id: int,
        limit: int = 10,
    ):

        return (
            self.db.query(Task)
            .filter(
                Task.user_id == user_id,
                Task.completed.is_(False),
            )
            .order_by(Task.created_at.desc())
            .limit(limit)
            .all()
        )
