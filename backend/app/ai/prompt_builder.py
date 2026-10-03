from app.ai.schemas.context import AIContext


class PromptBuilder:

    @staticmethod
    def build(
        context: AIContext,
        messages,
    ):

        prompt = []

        # --------------------------
        # System Prompt
        # --------------------------

        prompt.append(
            {
                "role": "system",
                "content": (
                    "You are Second Brain AI.\n"
                    "You are a personal AI assistant.\n"
                    "Use the provided context whenever it is relevant.\n"
                    "Do not invent facts.\n"
                    "If the answer is not in the provided context, say you don't know.\n"
                ),
            }
        )

        # --------------------------
        # User Profile
        # --------------------------

        prompt.append(
            {
                "role": "system",
                "content": (
                    f"User Profile:\n"
                    f"Name: {context.user.name}\n"
                    f"Email: {context.user.email}"
                ),
            }
        )

        # --------------------------
        # Long-Term Memory
        # --------------------------

        if context.memories:

            memory_text = "\n".join(
                f"- {memory.content}" for memory in context.memories
            )

            prompt.append(
                {
                    "role": "system",
                    "content": ("Long-Term Memory:\n" f"{memory_text}"),
                }
            )

        # --------------------------
        # Active Tasks
        # --------------------------

        active_tasks = [task for task in context.tasks if not task.completed]

        if active_tasks:

            task_text = "\n".join(
                f"- {task.title}"
                + (
                    f" (Priority: {task.priority}, Deadline: {task.deadline})"
                    if task.deadline
                    else f" (Priority: {task.priority})"
                )
                for task in active_tasks
            )

            prompt.append(
                {
                    "role": "system",
                    "content": ("Active Tasks:\n" f"{task_text}"),
                }
            )

        # --------------------------
        # Conversation
        # --------------------------

        for message in messages:

            prompt.append(
                {
                    "role": message.role,
                    "content": message.content,
                }
            )

        return prompt
