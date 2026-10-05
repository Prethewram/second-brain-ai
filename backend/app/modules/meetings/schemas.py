from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.modules.notes.schemas import NoteResponse
from app.modules.tasks.schema import TaskResponse


class MeetingWrite(BaseModel):
    title: str = Field(max_length=255)
    meeting_date: date | None = None
    attendees: str = Field(default="", max_length=10000)
    agenda: str = Field(default="", max_length=50000)
    minutes: str = Field(max_length=100000)
    decisions: str = Field(default="", max_length=50000)

    @field_validator("title", "minutes")
    @classmethod
    def not_blank(cls, value):
        if not value.strip():
            raise ValueError("This field cannot be empty")
        return value.strip()


class MeetingResponse(MeetingWrite):
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class MeetingDetail(MeetingResponse):
    notes: list[NoteResponse]
    tasks: list[TaskResponse]
