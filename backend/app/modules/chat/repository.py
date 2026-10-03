from sqlalchemy.orm import Session

from app.models.conversation import Conversation
from app.models.message import Message


class ChatRepository:

    def __init__(self, db: Session):
        self.db = db

    def create_conversation(self, user_id: int):

        conversation = Conversation(user_id=user_id, title="New Chat")

        self.db.add(conversation)
        self.db.commit()
        self.db.refresh(conversation)

        return conversation

    def get_conversation(self, conversation_id: int):

        return (
            self.db.query(Conversation)
            .filter(Conversation.id == conversation_id)
            .first()
        )

    def add_message(
        self,
        conversation_id: int,
        role: str,
        content: str,
    ):

        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
        )

        self.db.add(message)
        self.db.commit()

        return message

    def get_messages(
        self,
        conversation_id: int,
    ):

        return (
            self.db.query(Message)
            .filter(Message.conversation_id == conversation_id)
            .order_by(Message.id)
            .all()
        )
