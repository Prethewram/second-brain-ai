from typing import Optional

from pydantic import BaseModel, ConfigDict


class ProfileCreate(BaseModel):
    name: Optional[str] = None
    occupation: Optional[str] = None
    company: Optional[str] = None
    timezone: Optional[str] = None
    language: Optional[str] = None
    bio: Optional[str] = None
    goals: Optional[str] = None
    interests: Optional[str] = None
    skills: Optional[str] = None


class ProfileUpdate(BaseModel):
    name: Optional[str] = None
    occupation: Optional[str] = None
    company: Optional[str] = None
    timezone: Optional[str] = None
    language: Optional[str] = None
    bio: Optional[str] = None
    goals: Optional[str] = None
    interests: Optional[str] = None
    skills: Optional[str] = None


class ProfileResponse(BaseModel):
    id: int
    user_id: int
    name: Optional[str]
    occupation: Optional[str]
    company: Optional[str]
    timezone: Optional[str]
    language: Optional[str]
    bio: Optional[str]
    goals: Optional[str]
    interests: Optional[str]
    skills: Optional[str]
    model_config = ConfigDict(from_attributes=True)
