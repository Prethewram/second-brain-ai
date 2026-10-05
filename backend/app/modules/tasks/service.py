from app.common.exceptions import (
    ValidationException,
)

from app.core.base_service import BaseService
from app.modules.tasks.repository import TaskRepository
from app.modules.meetings.service import get_owned_meeting


class TaskService(BaseService):

    def __init__(self, db):

        super().__init__(TaskRepository(db))

    @staticmethod
    def _validate_title(title):
        if not isinstance(title, str) or not title.strip():
            raise ValidationException("Task title cannot be empty.")
        title = title.strip()
        if len(title) > 255:
            raise ValidationException("Task title cannot exceed 255 characters.")
        return title

    @staticmethod
    def _validate_optional_text(value, field, max_length=None):
        if value is not None:
            if not isinstance(value, str):
                raise ValidationException(f"{field} must be a string or null.")
            if max_length is not None and len(value) > max_length:
                raise ValidationException(
                    f"{field} cannot exceed {max_length} characters."
                )
        return value

    @staticmethod
    def _validate_priority(priority, *, fallback=False):
        if not isinstance(priority, str):
            raise ValidationException("Priority must be a string.")
        priority = priority.strip().lower()
        if priority not in ("low", "medium", "high"):
            if fallback:
                return "medium"
            raise ValidationException("Invalid priority.")
        return priority

    def create_task(
        self,
        user_id: int,
        title: str,
        description: str | None = None,
        priority: str = "medium",
        deadline: str | None = None,
        meeting_id: int | None = None,
    ):

        title = self._validate_title(title)
        if meeting_id is not None:
            get_owned_meeting(self.repository.db, user_id, meeting_id)
        priority = self._validate_priority(priority, fallback=True)
        description = self._validate_optional_text(description, "Description")
        deadline = self._validate_optional_text(deadline, "Deadline", 100)

        return self.repository.create(
            user_id=user_id,
            title=title,
            description=description,
            priority=priority,
            deadline=deadline,
            meeting_id=meeting_id,
        )

    def get_task(
        self,
        user_id: int,
        task_id: int,
    ):

        task = self.get_or_404(task_id)

        self.verify_owner(
            task,
            user_id,
        )

        return task

    def list_tasks(
        self,
        user_id: int,
    ):

        return self.repository.list_by_user(user_id)

    def update_task(
        self,
        user_id: int,
        task_id: int,
        **kwargs,
    ):

        task = self.get_task(
            user_id=user_id,
            task_id=task_id,
        )

        # Validate all supplied fields before changing the tracked object.
        changes = {}
        if kwargs.get("title") is not None:
            changes["title"] = self._validate_title(kwargs["title"])
        if kwargs.get("priority") is not None:
            changes["priority"] = self._validate_priority(kwargs["priority"])
        if "description" in kwargs:
            changes["description"] = self._validate_optional_text(
                kwargs["description"], "Description"
            )
        if "deadline" in kwargs:
            changes["deadline"] = self._validate_optional_text(
                kwargs["deadline"], "Deadline", 100
            )
        self.update_fields(task, changes)
        return self.repository.update(task)

    def complete_task(
        self,
        user_id: int,
        task_id: int,
    ):

        task = self.get_task(
            user_id=user_id,
            task_id=task_id,
        )

        return self.repository.complete(task)

    def delete_task(
        self,
        user_id: int,
        task_id: int,
    ):

        task = self.get_task(
            user_id=user_id,
            task_id=task_id,
        )

        self.repository.delete(task)
