from datetime import date

from pydantic import BaseModel, Field


class MemoryContext(BaseModel):
    content: str
    category: str
    importance: int


class TaskContext(BaseModel):
    title: str
    priority: str
    completed: bool
    deadline: str | None = None


class UserContext(BaseModel):
    id: int
    name: str
    email: str


class MeetingContext(BaseModel):
    title: str
    meeting_date: date
    attendees: str
    agenda: str


class NoteContext(BaseModel):
    title: str
    content: str
    category: str | None = None
    meeting_id: int | None = None


class AIContext(BaseModel):
    user: UserContext
    memories: list[MemoryContext] = Field(default_factory=list)
    tasks: list[TaskContext] = Field(default_factory=list)
    current_date: date = Field(default_factory=date.today)
    upcoming_meetings: list[MeetingContext] = Field(default_factory=list)
    upcoming_meeting_count: int = 0
    notes: list[NoteContext] = Field(default_factory=list)
    note_count: int = 0
