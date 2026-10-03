from app.services.ai.handlers.memory_handler import MemoryHandler
from app.modules.notes.handler import NoteHandler
from app.modules.profile.handler import ProfileHandler
from app.modules.tasks.handler import TaskHandler


class HandlerRegistry:

    def __init__(self, db):

        self._handlers = {
            "memory.create": MemoryHandler(db),
            "task.create": TaskHandler(db),
            "note.create": NoteHandler(db),
            "profile.update": ProfileHandler(db),
        }

    def get(
        self,
        action_type: str,
    ):

        return self._handlers.get(action_type)
