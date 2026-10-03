from datetime import datetime

from pydantic import BaseModel, ConfigDict


class MemoryCreate(BaseModel):
    content: str
    category: str = "general"
    importance: int = 1


class MemoryUpdate(BaseModel):
    content: str
    category: str
    importance: int


class MemoryResponse(BaseModel):
    id: int
    content: str
    category: str
    importance: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
