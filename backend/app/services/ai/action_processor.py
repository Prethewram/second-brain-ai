from app.modules.memory.repository import MemoryRepository


class ActionProcessor:

    def __init__(self, db):

        self.memory_repository = MemoryRepository(db)

    def process(
        self,
        user_id: int,
        analysis: dict,
    ):

        # Store Memory
        memory = analysis.get("memory", {})

        if memory.get("store"):

            self.memory_repository.create(
                user_id=user_id,
                content=memory["content"],
                category=memory.get(
                    "category",
                    "general",
                ),
                importance=memory.get(
                    "importance",
                    1,
                ),
            )

        # Future
        #
        # if task.create:
        #
        # if reminder.create:
        #
        # if note.create:
