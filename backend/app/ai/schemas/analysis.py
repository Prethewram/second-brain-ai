from pydantic import BaseModel


class MemoryAction(BaseModel):
    store: bool = False
    content: str | None = None
    category: str = "general"
    importance: int = 1


class TaskAction(BaseModel):
    create: bool = False
    title: str | None = None
    deadline: str | None = None


class ReplyAction(BaseModel):
    text: str = ""


class AnalysisResult(BaseModel):
    memory: MemoryAction
    task: TaskAction
    reply: ReplyAction
