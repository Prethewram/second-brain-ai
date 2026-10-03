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


class AIContext(BaseModel):
    user: UserContext
    memories: list[MemoryContext] = Field(default_factory=list)
    tasks: list[TaskContext] = Field(default_factory=list)
