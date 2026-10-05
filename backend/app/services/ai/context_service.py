from datetime import date

from app.models.meeting import Meeting
from app.ai.schemas.context import (
    AIContext,
    MemoryContext,
    MeetingContext,
    TaskContext,
    UserContext,
)

from app.modules.auth.repository import UserRepository
from app.modules.memory.repository import MemoryRepository
from app.modules.tasks.repository import TaskRepository


class ContextService:

    def __init__(
        self,
        db,
        user_repository=None,
        memory_repository=None,
        task_repository=None,
    ):

        self.db = db
        self.user_repository = user_repository or UserRepository(db)

        self.memory_repository = memory_repository or MemoryRepository(db)

        self.task_repository = task_repository or TaskRepository(db)

    def build_context(
        self,
        user_id: int,
    ) -> AIContext:

        user = self.user_repository.get(user_id)

        memories = self.memory_repository.get_top_memories(
            user_id=user_id,
            limit=10,
        )

        tasks = self.task_repository.get_active_tasks(
            user_id=user_id,
            limit=10,
        )

        today = date.today()
        meetings = self.db.query(Meeting).filter(
            Meeting.user_id == user_id, Meeting.meeting_date >= today
        )
        meeting_count = meetings.count()
        upcoming = meetings.order_by(Meeting.meeting_date, Meeting.id).limit(20).all()

        return AIContext(
            current_date=today,
            upcoming_meeting_count=meeting_count,
            upcoming_meetings=[
                MeetingContext(
                    title=m.title,
                    meeting_date=m.meeting_date,
                    attendees=m.attendees[:2000],
                    agenda=m.agenda[:4000],
                )
                for m in upcoming
            ],
            user=UserContext(
                id=user.id,
                name=user.name,
                email=user.email,
            ),
            memories=[
                MemoryContext(
                    content=m.content,
                    category=m.category,
                    importance=m.importance,
                )
                for m in memories
            ],
            tasks=[
                TaskContext(
                    title=t.title,
                    priority=t.priority,
                    completed=t.completed,
                    deadline=t.deadline,
                )
                for t in tasks
            ],
        )
