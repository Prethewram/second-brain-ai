from pydantic import BaseModel, Field
from typing import Any


class Action(BaseModel):
    type: str
    payload: dict[str, Any] = Field(default_factory=dict)


class Reply(BaseModel):
    text: str = ""


class AnalysisResult(BaseModel):
    actions: list[Action] = Field(default_factory=list)
    reply: Reply = Field(default_factory=Reply)
