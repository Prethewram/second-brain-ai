from pydantic import BaseModel, ConfigDict


class NoteCreate(BaseModel):
    title: str
    content: str
    category: str = "general"


class NoteUpdate(BaseModel):
    title: str | None = None
    content: str | None = None
    category: str | None = None
    is_archived: bool | None = None


class NoteResponse(BaseModel):
    id: int
    title: str
    content: str
    category: str
    source: str
    is_archived: bool

    model_config = ConfigDict(from_attributes=True)
