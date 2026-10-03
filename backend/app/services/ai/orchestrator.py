from app.ai.client import AIClient
from app.ai.prompt_builder import PromptBuilder
from app.services.ai.context_service import ContextService


class AIOrchestrator:

    def __init__(
        self,
        db,
        ai=None,
        context_service=None,
    ):

        self.ai = ai or AIClient()

        self.context_service = context_service or ContextService(db)

    def generate_reply(
        self,
        user_id: int,
        messages,
    ):

        context = self.context_service.build_context(
            user_id=user_id,
        )

        prompt = PromptBuilder.build(
            context=context,
            messages=messages,
        )

        return self.ai.chat(prompt)
