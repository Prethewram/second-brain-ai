from pydantic import BaseModel, field_validator


class AnalyzeRequest(BaseModel):
    message: str

    @field_validator("message")
    @classmethod
    def require_nonempty_message(cls, message):
        if not message.strip():
            raise ValueError("Message cannot be empty.")
        return message
