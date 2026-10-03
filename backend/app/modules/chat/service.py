from app.common.exceptions import (
    AIProviderException,
    NotFoundException,
    ValidationException,
)
from app.core.base_service import BaseService

from app.modules.chat.repository import ChatRepository
from app.services.ai.analyzer import AIAnalyzer
from app.services.ai.action_engine import ActionEngine
from app.services.ai.orchestrator import AIOrchestrator
from app.ai.schemas.actions import AnalysisResult


class ChatService(BaseService):

    def __init__(
        self,
        db,
        repository=None,
        orchestrator=None,
        analyzer=None,
        action_engine=None,
    ):

        super().__init__(repository if repository is not None else ChatRepository(db))

        self.orchestrator = orchestrator or AIOrchestrator(db)

        self.analyzer = analyzer or AIAnalyzer()

        self.action_engine = action_engine or ActionEngine(db)

    def chat(
        self,
        user_id: int,
        conversation_id: int | None,
        message: str,
    ):

        if not isinstance(message, str) or not message.strip():
            raise ValidationException("Message cannot be empty.")

        if conversation_id is None:

            conversation = self.repository.create_conversation(user_id)

        else:

            conversation = self.repository.get_conversation(conversation_id)

            if conversation is None:
                raise NotFoundException("Conversation not found")

            self.verify_owner(conversation, user_id)

        self.repository.add_message(
            conversation.id,
            "user",
            message,
        )

        try:
            analysis: AnalysisResult = self.analyzer.analyze(message)
        except AIProviderException as exc:
            exc.conversation_id = conversation.id
            raise

        self.action_engine.execute(
            user_id=user_id,
            actions=analysis.actions,
        )

        messages = self.repository.get_messages(conversation.id)

        try:
            response = self.orchestrator.generate_reply(
                user_id=user_id,
                messages=messages,
            )
        except AIProviderException as exc:
            exc.conversation_id = conversation.id
            exc.actions_may_be_saved = bool(analysis.actions)
            raise

        self.repository.add_message(
            conversation.id,
            "assistant",
            response,
        )

        return {
            "conversation_id": conversation.id,
            "response": response,
        }
